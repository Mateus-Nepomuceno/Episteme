from datetime import time
from http import HTTPStatus
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest

from academico.app import app
from academico.models import Disciplina
from academico.security import CurrentUser, get_current_user

ALUNO_ID = str(uuid4())
CREDITOS = 4
PROFESSOR_ID = str(uuid4())


@pytest.fixture
def autenticar():
    def _autenticar(usuario_id=None):
        usuario = CurrentUser(
            id=usuario_id or uuid4(),
            email='aluno@teste.com',
            e_admin=False,
            token='token-do-aluno',
        )
        app.dependency_overrides[get_current_user] = lambda: usuario
        return usuario

    return _autenticar


@pytest.fixture
def criar_disciplina(session):
    def _criar(codigo, nome):
        disciplina = Disciplina(
            codigo=codigo,
            nome=nome,
            carga_horaria=60,
            tipo='obrigatória',
            departamento='DCC',
            creditos=CREDITOS,
        )
        session.add(disciplina)
        session.commit()
        session.refresh(disciplina)
        return disciplina

    return _criar


def turma_json(codigo, nome='Turma'):
    return {
        'id': str(uuid4()),
        'nome': nome,
        'codigo': codigo,
        'materia': 'Matéria',
        'curso_id': str(uuid4()),
        'periodo_letivo': '2026.2',
        'capacidade': 30,
        'professor': {'id': PROFESSOR_ID, 'matricula_id': 'P000001'},
        'horarios': [
            {
                'dia_semana': 'Segunda',
                'horario_inicio': '14:00:00',
                'horario_fim': '16:00:00',
                'local': 'Sala 204',
            }
        ],
    }


def turma_falso(turmas=None, erro_turmas=None):
    def get(url, params=None, headers=None, timeout=None):
        requisicao = httpx.Request('GET', url)
        if '/alunos/usuario_id/' in url:
            return httpx.Response(
                200,
                json={
                    'id': ALUNO_ID,
                    'usuario_id': str(uuid4()),
                    'matricula_id': '2023108420',
                    'curso_id': str(uuid4()),
                    'ativo': True,
                },
                request=requisicao,
            )
        if erro_turmas is not None:
            raise erro_turmas
        return httpx.Response(
            200, json={'turmas': turmas or []}, request=requisicao
        )

    return get


def test_aluno_recebe_disciplinas_com_turmas_relacionadas_pelo_codigo(
    client, autenticar, criar_disciplina
):
    autenticar()
    criar_disciplina('BD002', 'Banco de Dados II')
    criar_disciplina('ES014', 'Engenharia de Software')

    turmas = [
        turma_json('BD002', 'Turma BD'),
        turma_json('XX999', 'Turma sem disciplina cadastrada'),
    ]

    with patch(
        'academico.turma_client.httpx.get',
        side_effect=turma_falso(turmas),
    ):
        resposta = client.get('/matricula/minhas-disciplinas')

    assert resposta.status_code == HTTPStatus.OK
    disciplinas = resposta.json()['disciplinas']
    assert [d['codigo'] for d in disciplinas] == ['BD002']

    disciplina = disciplinas[0]
    assert disciplina['nome'] == 'Banco de Dados II'
    assert disciplina['creditos'] == CREDITOS
    assert [t['nome'] for t in disciplina['turmas']] == ['Turma BD']

    turma = disciplina['turmas'][0]
    assert turma['periodo_letivo'] == '2026.2'
    assert turma['professor'] == {
        'id': PROFESSOR_ID,
        'matricula_id': 'P000001',
    }
    assert turma['horarios'] == [
        {
            'dia_semana': 'Segunda',
            'horario_inicio': time(14, 0).isoformat(),
            'horario_fim': time(16, 0).isoformat(),
            'local': 'Sala 204',
        }
    ]


def test_aluno_sem_turmas_recebe_lista_vazia(
    client, autenticar, criar_disciplina
):
    autenticar()
    criar_disciplina('BD002', 'Banco de Dados II')

    with patch(
        'academico.turma_client.httpx.get',
        side_effect=turma_falso([]),
    ):
        resposta = client.get('/matricula/minhas-disciplinas')

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json() == {'disciplinas': []}


def test_turmas_sem_disciplina_cadastrada_nao_aparecem(client, autenticar):
    autenticar()

    with patch(
        'academico.turma_client.httpx.get',
        side_effect=turma_falso([turma_json('BD002')]),
    ):
        resposta = client.get('/matricula/minhas-disciplinas')

    assert resposta.json() == {'disciplinas': []}


def test_turma_indisponivel_responde_503(client, autenticar):
    autenticar()

    with patch(
        'academico.turma_client.httpx.get',
        side_effect=turma_falso(
            erro_turmas=httpx.ConnectError('conexão recusada')
        ),
    ):
        resposta = client.get('/matricula/minhas-disciplinas')

    assert resposta.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert resposta.json()['detail'] == (
        'Não foi possível acessar o serviço de turma'
    )


def test_turma_recusa_acesso_responde_403(client, autenticar):
    autenticar()

    def get(url, params=None, headers=None, timeout=None):
        requisicao = httpx.Request('GET', url)
        if '/alunos/usuario_id/' in url:
            return httpx.Response(
                200,
                json={'id': ALUNO_ID, 'curso_id': str(uuid4())},
                request=requisicao,
            )
        return httpx.Response(
            403, json={'detail': 'Permissão negada'}, request=requisicao
        )

    with patch('academico.turma_client.httpx.get', side_effect=get):
        resposta = client.get('/matricula/minhas-disciplinas')

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_resposta_invalida_da_turma_responde_502(client, autenticar):
    autenticar()

    def get(url, params=None, headers=None, timeout=None):
        requisicao = httpx.Request('GET', url)
        if '/alunos/usuario_id/' in url:
            return httpx.Response(
                200,
                json={'id': ALUNO_ID, 'curso_id': str(uuid4())},
                request=requisicao,
            )
        return httpx.Response(
            200, json={'turmas': 'invalido'}, request=requisicao
        )

    with patch('academico.turma_client.httpx.get', side_effect=get):
        resposta = client.get('/matricula/minhas-disciplinas')

    assert resposta.status_code == HTTPStatus.BAD_GATEWAY


def test_sem_token_responde_401(client):
    app.dependency_overrides.pop(get_current_user, None)

    resposta = client.get('/matricula/minhas-disciplinas')

    assert resposta.status_code == HTTPStatus.UNAUTHORIZED
