from unittest.mock import patch
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from turma.app import app
from turma.database import get_session
from turma.models import table_registry
from turma.security import CurrentUser, get_current_user


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def session():
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    table_registry.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    table_registry.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def curso_academico():
    with patch(
        'turma.routers.alunos.consultar_curso',
        return_value={'ativo': True},
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def usuario_administrador():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='admin@teste.com', e_admin=True
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


REGISTRO_MATRICULAS = {}


def usuario_da(matricula):
    usuario_id = uuid5(NAMESPACE_URL, f'matricula:{matricula}')
    REGISTRO_MATRICULAS[str(usuario_id)] = matricula
    return usuario_id


def _usuario_da_matricula(matricula):
    return {
        'id': str(usuario_da(matricula)),
        'nome': f'Usuário {matricula}',
        'matricula': matricula,
    }


def _usuario_por_id(usuario_id):
    matricula = REGISTRO_MATRICULAS.get(str(usuario_id))
    if matricula is None:
        return None
    return {
        'id': str(usuario_id),
        'nome': f'Usuário {matricula}',
        'matricula': matricula,
    }


@pytest.fixture(autouse=True)
def identidade_isolado():
    with patch(
        'turma.usuarios.buscar_usuario', side_effect=_usuario_por_id
    ), patch(
        'turma.usuarios.buscar_usuario_por_matricula',
        side_effect=_usuario_da_matricula,
    ):
        yield
