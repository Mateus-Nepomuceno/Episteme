from http import HTTPStatus
from unittest.mock import patch
from uuid import uuid4

from academico.app import app
from academico.models import Disciplina
from academico.security import CurrentUser, get_current_user

ALUNO_ID = str(uuid4())
TURMA_ID = str(uuid4())
CODIGO = 'BD002'
MEDIA = 8.5
FREQUENCIA = 96
PROGRESSO = 50


def _autenticar():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='aluno@teste.com', e_admin=False, token='token-aluno'
    )


def test_turma_matriculada_traz_media_frequencia_e_progresso(client, session):
    _autenticar()
    session.add(
        Disciplina(
            codigo=CODIGO,
            nome='Banco de Dados II',
            carga_horaria=60,
            tipo='obrigatória',
            departamento='DCC',
        )
    )
    session.commit()
    turma = {
        'id': TURMA_ID,
        'nome': 'Turma BD',
        'codigo': CODIGO,
        'periodo_letivo': '2026.2',
        'professor': None,
        'horarios': [],
    }
    desempenho = {'media': MEDIA, 'frequencia': FREQUENCIA, 'progresso': PROGRESSO}

    with (
        patch(
            'academico.routers.matriculas.buscar_aluno_por_usuario',
            return_value={'id': ALUNO_ID},
        ),
        patch(
            'academico.routers.matriculas.listar_turmas_do_aluno',
            return_value=[turma],
        ),
        patch(
            'academico.routers.matriculas.consultar_turma',
            return_value=desempenho,
        ) as consulta,
    ):
        resposta = client.get('/matricula/minhas-disciplinas')

    assert resposta.status_code == HTTPStatus.OK
    turma_json = resposta.json()['disciplinas'][0]['turmas'][0]
    assert turma_json['media'] == MEDIA
    assert turma_json['frequencia'] == FREQUENCIA
    assert turma_json['progresso'] == PROGRESSO
    consulta.assert_called_once_with(
        f'/alunos/me/turmas/{TURMA_ID}/desempenho', 'token-aluno'
    )
    app.dependency_overrides.pop(get_current_user, None)


def test_minhas_disciplinas_traz_nome_do_professor(client, session):
    _autenticar()
    session.add(
        Disciplina(
            codigo=CODIGO,
            nome='Banco de Dados II',
            carga_horaria=60,
            tipo='obrigatória',
            departamento='DCC',
        )
    )
    session.commit()
    turma = {
        'id': TURMA_ID,
        'nome': 'Turma BD',
        'codigo': CODIGO,
        'periodo_letivo': '2026.2',
        'professor': {'id': str(uuid4()), 'matricula_id': 'P1', 'nome': 'Rafael Oliveira'},
        'horarios': [],
    }

    with (
        patch(
            'academico.routers.matriculas.buscar_aluno_por_usuario',
            return_value={'id': ALUNO_ID},
        ),
        patch(
            'academico.routers.matriculas.listar_turmas_do_aluno',
            return_value=[turma],
        ),
        patch(
            'academico.routers.matriculas.consultar_turma',
            return_value={'media': None, 'frequencia': None, 'progresso': None},
        ),
    ):
        resposta = client.get('/matricula/minhas-disciplinas')

    app.dependency_overrides.pop(get_current_user, None)
    professor = resposta.json()['disciplinas'][0]['turmas'][0]['professor']
    assert professor['nome'] == 'Rafael Oliveira'
