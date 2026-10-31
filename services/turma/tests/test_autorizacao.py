from http import HTTPStatus
from uuid import uuid4

from turma.app import app
from turma.models import Aluno, Professor
from turma.security import CurrentUser, get_current_user

CURSO_ID = '11111111-1111-1111-1111-111111111111'


def como(usuario_id, e_admin=False):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=usuario_id, email='usuario@teste.com', e_admin=e_admin
    )


def sem_token():
    app.dependency_overrides.pop(get_current_user, None)


def criar_aluno(session):
    aluno = Aluno(
        usuario_id=uuid4(),
        matricula_id=f'M{uuid4().hex[:6]}',
        curso_id=CURSO_ID,
        ativo=True,
    )
    session.add(aluno)
    session.commit()
    session.refresh(aluno)
    return aluno


def criar_professor(session):
    professor = Professor(
        usuario_id=uuid4(), matricula_id=f'P{uuid4().hex[:6]}', ativo=True
    )
    session.add(professor)
    session.commit()
    session.refresh(professor)
    return professor


def corpo_aluno(aluno):
    return {
        'usuario_id': str(aluno.usuario_id),
        'matricula_id': aluno.matricula_id,
        'curso_id': CURSO_ID,
        'ativo': True,
    }


def test_aluno_dono_nao_altera_proprio_cadastro(client, session):
    aluno = criar_aluno(session)
    como(aluno.usuario_id)

    resposta = client.put(f'/alunos/{aluno.id}', json=corpo_aluno(aluno))

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_aluno_dono_nao_exclui_proprio_cadastro(client, session):
    aluno = criar_aluno(session)
    como(aluno.usuario_id)

    resposta = client.delete(f'/alunos/{aluno.id}')

    assert resposta.status_code == HTTPStatus.FORBIDDEN
    session.expire_all()
    assert session.get(Aluno, aluno.id) is not None


def test_professor_dono_nao_altera_proprio_cadastro(client, session):
    professor = criar_professor(session)
    como(professor.usuario_id)

    resposta = client.put(
        f'/professores/{professor.id}',
        json={
            'usuario_id': str(professor.usuario_id),
            'matricula_id': professor.matricula_id,
            'ativo': True,
        },
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_professor_dono_nao_exclui_proprio_cadastro(client, session):
    professor = criar_professor(session)
    como(professor.usuario_id)

    resposta = client.delete(f'/professores/{professor.id}')

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_consulta_aluno_por_id_anonimo_recebe_401(client, session):
    aluno = criar_aluno(session)
    sem_token()

    resposta = client.get(f'/alunos/{aluno.id}')

    assert resposta.status_code == HTTPStatus.UNAUTHORIZED


def test_consulta_aluno_por_id_outro_usuario_recebe_403(client, session):
    aluno = criar_aluno(session)
    como(uuid4())

    resposta = client.get(f'/alunos/{aluno.id}')

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_consulta_aluno_por_id_dono_e_admin_recebem_200(client, session):
    aluno = criar_aluno(session)

    como(aluno.usuario_id)
    assert client.get(f'/alunos/{aluno.id}').status_code == HTTPStatus.OK

    como(uuid4(), e_admin=True)
    assert client.get(f'/alunos/{aluno.id}').status_code == HTTPStatus.OK


def test_consulta_aluno_por_usuario_id_outro_usuario_recebe_403(client, session):
    aluno = criar_aluno(session)
    como(uuid4())

    resposta = client.get(f'/alunos/usuario_id/{aluno.usuario_id}')

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_consulta_aluno_por_matricula_outro_usuario_recebe_403(client, session):
    aluno = criar_aluno(session)
    como(uuid4())

    resposta = client.get(f'/alunos/matricula_id/{aluno.matricula_id}')

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_consulta_aluno_por_matricula_dono_recebe_200(client, session):
    aluno = criar_aluno(session)
    como(aluno.usuario_id)

    resposta = client.get(f'/alunos/matricula_id/{aluno.matricula_id}')

    assert resposta.status_code == HTTPStatus.OK


def test_consulta_professor_por_id_anonimo_recebe_401(client, session):
    professor = criar_professor(session)
    sem_token()

    resposta = client.get(f'/professores/{professor.id}')

    assert resposta.status_code == HTTPStatus.UNAUTHORIZED


def test_consulta_professor_por_id_outro_usuario_recebe_403(client, session):
    professor = criar_professor(session)
    como(uuid4())

    resposta = client.get(f'/professores/{professor.id}')

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_consulta_professor_por_id_dono_recebe_200(client, session):
    professor = criar_professor(session)
    como(professor.usuario_id)

    resposta = client.get(f'/professores/{professor.id}')

    assert resposta.status_code == HTTPStatus.OK
