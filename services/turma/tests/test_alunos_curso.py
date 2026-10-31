from http import HTTPStatus
from uuid import UUID, uuid4

from turma.academico_client import ServicoAcademicoIndisponivel
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


def test_create_aluno_com_curso_inexistente(client, session, curso_academico):
    curso_academico.return_value = None

    response = client.post('/alunos/', json=_payload_aluno())

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()['detail'] == (
        'Curso não encontrado no serviço acadêmico'
    )
    assert session.query(Aluno).count() == 0


def test_create_aluno_com_curso_inativo(client, session, curso_academico):
    curso_academico.return_value = {'id': CURSO_ID, 'ativo': False}

    response = client.post('/alunos/', json=_payload_aluno())

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()['detail'] == (
        'Curso inativo não pode ser associado a alunos'
    )
    assert session.query(Aluno).count() == 0


def test_create_aluno_com_servico_academico_indisponivel(
    client, session, curso_academico
):
    curso_academico.side_effect = ServicoAcademicoIndisponivel('timeout')

    response = client.post('/alunos/', json=_payload_aluno())

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert session.query(Aluno).count() == 0


def test_create_aluno_com_curso_valido_consulta_o_curso_informado(
    client, session, curso_academico
):
    response = client.post('/alunos/', json=_payload_aluno())

    assert response.status_code == HTTPStatus.CREATED
    curso_academico.assert_called_once_with(UUID(CURSO_ID))


def test_update_aluno_com_curso_inexistente_nao_altera_cadastro(
    client, session, curso_academico
):
    aluno = Aluno(
        usuario_id=uuid4(),
        matricula_id='2026003',
        curso_id=CURSO_ID,
        ativo=True,
    )
    session.add(aluno)
    session.commit()
    session.refresh(aluno)

    novo_curso = str(uuid4())
    curso_academico.return_value = None
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=aluno.usuario_id, email='aluno@teste.com', e_admin=False
    )

    response = client.put(
        f'/alunos/{aluno.id}',
        json=_payload_aluno(
            usuario_id=str(aluno.usuario_id),
            matricula_id='2026003',
            curso_id=novo_curso,
        ),
    )

    app.dependency_overrides.clear()
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    session.refresh(aluno)
    assert aluno.curso_id == CURSO_ID


def test_update_aluno_com_curso_valido(client, session, curso_academico):
    aluno = Aluno(
        usuario_id=uuid4(),
        matricula_id='2026004',
        curso_id=CURSO_ID,
        ativo=True,
    )
    session.add(aluno)
    session.commit()
    session.refresh(aluno)

    novo_curso = '33333333-3333-3333-3333-333333333333'
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=aluno.usuario_id, email='aluno@teste.com', e_admin=False
    )

    response = client.put(
        f'/alunos/{aluno.id}',
        json=_payload_aluno(
            usuario_id=str(aluno.usuario_id),
            matricula_id='2026004',
            curso_id=novo_curso,
        ),
    )

    app.dependency_overrides.clear()
    assert response.status_code == HTTPStatus.OK
    assert response.json()['curso_id'] == novo_curso
