from datetime import date, datetime, timedelta
from http import HTTPStatus
from unittest.mock import patch
from uuid import UUID, uuid4

import httpx
import pytest

from academico.app import app
from academico.models import AtividadeComplementar
from academico.security import CurrentUser, get_current_user

TURMA_BD = str(uuid4())
TURMA_REDES = str(uuid4())
ALUNO_ID = str(uuid4())
FUTURO = datetime.now() + timedelta(days=10)
PASSADO = datetime.now() - timedelta(days=10)


def _rotas():
    turmas = [
        {'id': TURMA_BD, 'materia': 'Banco de Dados', 'nome': 'BD'},
        {'id': TURMA_REDES, 'materia': 'Redes', 'nome': 'Redes'},
    ]
    rotas = {
        f'/turmas/aluno/{ALUNO_ID}': {'turmas': turmas},
        f'/alunos/me/turmas/{TURMA_BD}/desempenho': {
            'media': 8.0,
            'frequencia': 90,
            'progresso': 50,
        },
        f'/alunos/me/turmas/{TURMA_REDES}/desempenho': {
            'media': 9.0,
            'frequencia': 100,
            'progresso': 0,
        },
        f'/turmas/{TURMA_BD}/atividades': {
            'atividades': [
                {
                    'id': str(uuid4()),
                    'titulo': 'Lista tardia',
                    'tipo': 'exercicio',
                    'prazo': PASSADO.isoformat(),
                    'situacao': 'vencida',
                },
                {
                    'id': str(uuid4()),
                    'titulo': 'Entregue',
                    'tipo': 'leitura',
                    'prazo': FUTURO.isoformat(),
                    'situacao': 'concluida',
                },
            ]
        },
        f'/turmas/{TURMA_REDES}/atividades': {
            'atividades': [
                {
                    'id': str(uuid4()),
                    'titulo': 'Projeto',
                    'tipo': 'pratica',
                    'prazo': FUTURO.isoformat(),
                    'situacao': 'pendente',
                }
            ]
        },
        f'/turmas/{TURMA_BD}/avaliacoes': {
            'avaliacoes': [
                {
                    'id': str(uuid4()),
                    'nome': 'Prova 1',
                    'tipo': 'prova',
                    'data': (date.today() + timedelta(days=5)).isoformat(),
                    'peso': 60,
                },
                {
                    'id': str(uuid4()),
                    'nome': 'Prova antiga',
                    'tipo': 'prova',
                    'data': (date.today() - timedelta(days=5)).isoformat(),
                    'peso': 40,
                },
            ],
            'soma_pesos': 100,
        },
        f'/turmas/{TURMA_REDES}/avaliacoes': {'avaliacoes': [], 'soma_pesos': 0},
        f'/alunos/me/turmas/{TURMA_BD}/notas': {
            'notas': [
                {
                    'avaliacao_id': str(uuid4()),
                    'nome': 'P0',
                    'tipo': 'prova',
                    'data': '2026-08-01',
                    'peso': 40,
                    'valor': 7.0,
                },
                {
                    'avaliacao_id': str(uuid4()),
                    'nome': 'P1',
                    'tipo': 'prova',
                    'data': '2026-09-01',
                    'peso': 60,
                    'valor': 9.0,
                },
                {
                    'avaliacao_id': str(uuid4()),
                    'nome': 'P2',
                    'tipo': 'prova',
                    'data': '2026-10-01',
                    'peso': 60,
                    'valor': None,
                },
            ]
        },
        f'/alunos/me/turmas/{TURMA_REDES}/notas': {'notas': []},
        f'/horarios/aluno/{ALUNO_ID}': {
            'horarios': [
                {
                    'dia_semana': 'Sexta',
                    'horario_inicio': '08:00:00',
                    'horario_fim': '10:00:00',
                    'local': 'Lab 1',
                    'turma': {'id': TURMA_REDES, 'materia': 'Redes'},
                },
                {
                    'dia_semana': 'Segunda',
                    'horario_inicio': '14:00:00',
                    'horario_fim': '16:00:00',
                    'local': 'Sala 2',
                    'turma': {'id': TURMA_BD, 'materia': 'Banco de Dados'},
                },
            ]
        },
    }
    return rotas


def _fake_get(usuario_encontrado=True):
    rotas = _rotas()

    def get(url, params=None, headers=None, timeout=None):
        if '/alunos/usuario_id/' in url:
            if usuario_encontrado:
                return httpx.Response(HTTPStatus.OK, json={'id': ALUNO_ID})
            return httpx.Response(HTTPStatus.NOT_FOUND)
        for caminho, corpo in rotas.items():
            if url.endswith(caminho):
                return httpx.Response(HTTPStatus.OK, json=corpo)
        return httpx.Response(HTTPStatus.NOT_FOUND)

    return get


_USUARIO = uuid4()


@pytest.fixture
def autenticado():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=_USUARIO, email='aluno@teste.com', e_admin=False, token='token-aluno'
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_resumo_calcula_medias_e_horas_aprovadas(client, session, autenticado):
    session.add_all(
        [
            AtividadeComplementar(
                aluno_id=UUID(ALUNO_ID), descricao='Monitoria', horas=20, situacao='aprovada'
            ),
            AtividadeComplementar(
                aluno_id=UUID(ALUNO_ID), descricao='Evento', horas=5, situacao='pendente'
            ),
        ]
    )
    session.commit()

    with patch('academico.turma_client.httpx.get', side_effect=_fake_get()):
        resposta = client.get('/alunos/me/resumo')

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json() == {
        'media_geral': 8.5,
        'frequencia_geral': 95,
        'horas_complementares': 20,
    }


def test_resumo_sem_cadastro_de_aluno_devolve_vazio(client, session, autenticado):
    with patch(
        'academico.turma_client.httpx.get',
        side_effect=_fake_get(usuario_encontrado=False),
    ):
        resposta = client.get('/alunos/me/resumo')

    assert resposta.json() == {
        'media_geral': None,
        'frequencia_geral': None,
        'horas_complementares': 0,
    }


def test_pendencias_incluem_vencidas_e_pendentes_ordenadas_por_prazo(
    client, session, autenticado
):
    with patch('academico.turma_client.httpx.get', side_effect=_fake_get()):
        resposta = client.get('/alunos/me/pendencias')

    titulos = [p['titulo'] for p in resposta.json()['pendencias']]
    assert titulos == ['Lista tardia', 'Projeto']


def test_notas_recentes_ignoram_notas_nao_lancadas(client, session, autenticado):
    with patch('academico.turma_client.httpx.get', side_effect=_fake_get()):
        resposta = client.get('/alunos/me/notas/recentes?limite=5')

    notas = resposta.json()['notas']
    assert [n['nome'] for n in notas] == ['P1', 'P0']
    assert notas[0]['disciplina'] == 'Banco de Dados'


def test_compromissos_trazem_provas_futuras_e_entregas_pendentes(
    client, session, autenticado
):
    with patch('academico.turma_client.httpx.get', side_effect=_fake_get()):
        resposta = client.get('/alunos/me/compromissos')

    tipos = [(c['titulo'], c['tipo']) for c in resposta.json()['compromissos']]
    assert ('Prova 1', 'Avaliação') in tipos
    assert ('Projeto', 'Entrega') in tipos
    assert ('Prova antiga', 'Avaliação') not in tipos
    assert ('Entregue', 'Entrega') not in tipos


def test_proximas_aulas_caem_no_dia_da_semana_do_horario(
    client, session, autenticado
):
    dia_da_semana = {'Banco de Dados': 0, 'Redes': 4}

    with patch('academico.turma_client.httpx.get', side_effect=_fake_get()):
        resposta = client.get('/alunos/me/proximas-aulas')

    aulas = resposta.json()['aulas']
    datas = [datetime.fromisoformat(a['data']) for a in aulas]
    assert datas == sorted(datas)
    for aula, data in zip(aulas, datas):
        assert data.weekday() == dia_da_semana[aula['disciplina']]
        assert data >= datetime.now() - timedelta(minutes=1)
