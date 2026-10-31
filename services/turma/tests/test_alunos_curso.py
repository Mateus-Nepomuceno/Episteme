from http import HTTPStatus
from uuid import uuid4

from turma.app import app
from turma.models import Aluno
from turma.security import CurrentUser, get_current_user

CURSO_ID = '11111111-1111-1111-1111-111111111111'


def _payload_aluno(**campos):
    payload = {
        'usuario_id': str(uuid4()),
        'matricula_id': '2026001',
        'curso_id': CURSO_ID,
        'ativo': True,
    }
    payload.update(campos)
    return payload


def test_create_aluno_recusa_curso_id_literal_string(client, session):
    response = client.post('/alunos/', json=_payload_aluno(curso_id='string'))

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert 'UUID' in response.text
    assert session.query(Aluno).count() == 0


def test_create_aluno_recusa_curso_id_numerico(client, session):
    response = client.post('/alunos/', json=_payload_aluno(curso_id='1'))

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert session.query(Aluno).count() == 0


def test_create_aluno_recusa_curso_id_vazio(client, session):
    response = client.post('/alunos/', json=_payload_aluno(curso_id=''))

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert session.query(Aluno).count() == 0


def test_create_aluno_normaliza_curso_id_uuid(client, session):
    response = client.post(
        '/alunos/',
        json=_payload_aluno(curso_id=CURSO_ID.upper()),
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['curso_id'] == CURSO_ID


def test_update_aluno_recusa_curso_id_invalido(client, session):
    aluno = Aluno(
        usuario_id=uuid4(),
        matricula_id='2026002',
        curso_id=CURSO_ID,
        ativo=True,
    )
    session.add(aluno)
    session.commit()
    session.refresh(aluno)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=aluno.usuario_id, email='aluno@teste.com', e_admin=False
    )

    response = client.put(
        f'/alunos/{aluno.id}',
        json=_payload_aluno(
            usuario_id=str(aluno.usuario_id),
            matricula_id='2026002',
            curso_id='string',
        ),
    )

    app.dependency_overrides.clear()
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    session.refresh(aluno)
    assert aluno.curso_id == CURSO_ID
