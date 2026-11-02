from datetime import datetime, timedelta
from http import HTTPStatus

from tests.test_modulos import (
    como,
    criar_aluno,
    criar_modulo,
    criar_professor,
    criar_turma,
)

PRAZO_FUTURO = (datetime.now() + timedelta(days=30)).isoformat()


def test_status_do_modulo_acompanha_acesso_e_entregas_do_aluno(client, session):
    professor = criar_professor(session)
    aluno = criar_aluno(session)
    turma = criar_turma(session, professor, [aluno])
    como(professor.usuario_id)
    modulo = criar_modulo(client, turma.id, 'Módulo 1', 1)
    material = client.post(
        f'/modulos/{modulo["id"]}/materiais',
        json={'titulo': 'Slides', 'tipo': 'arquivo', 'ordem': 1},
    ).json()
    atividade = client.post(
        f'/turmas/{turma.id}/atividades',
        json={
            'titulo': 'Lista',
            'tipo': 'exercicio',
            'categoria': 'Lista',
            'prazo': PRAZO_FUTURO,
            'modulo_id': modulo['id'],
        },
    ).json()
    como(aluno.usuario_id)

    def status_atual():
        resposta = client.get(f'/turmas/{turma.id}/modulos')
        assert resposta.status_code == HTTPStatus.OK
        return resposta.json()['modulos'][0]['status']

    inicial = status_atual()
    client.post(f'/materiais/{material["id"]}/acesso')
    parcial = status_atual()
    client.post(f'/atividades/{atividade["id"]}/entrega')
    concluido = status_atual()

    assert (inicial, parcial, concluido) == ('pending', 'in_progress', 'completed')


def test_professor_nao_recebe_status_de_modulo(client, session):
    professor = criar_professor(session)
    turma = criar_turma(session, professor, [])
    como(professor.usuario_id)
    criar_modulo(client, turma.id, 'Módulo 1', 1)

    resposta = client.get(f'/turmas/{turma.id}/modulos')

    assert resposta.json()['modulos'][0]['status'] is None
