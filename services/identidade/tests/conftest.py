import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from identidade.app import app
from identidade.database import get_session
from identidade.models import Usuario, table_registry
from identidade.security import get_password_hash


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


@pytest.fixture
def user(session):
    novo_usuario = Usuario(
        nome='joana',
        senha=get_password_hash('senha_limpa'),
        email='joana@teste.com',
        cpf='12345678900',
        telefone='(11) 99999-9999',
    )
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    return novo_usuario


@pytest.fixture
def user_token(client, user):
    response = client.post(
        '/auth/token', data={'username': user.email, 'password': 'senha_limpa'}
    )
    return response.json()['access_token']


@pytest.fixture
def admin(session):
    novo_admin = Usuario(
        nome='admin_joana',
        senha=get_password_hash('senha_admin'),
        email='admin@teste.com',
        cpf='09876543211',
        telefone='(11) 88888-8888',
        e_admin=True,
    )
    session.add(novo_admin)
    session.commit()
    session.refresh(novo_admin)
    return novo_admin


@pytest.fixture
def admin_token(client, admin):
    response = client.post(
        '/auth/token',
        data={'username': admin.email, 'password': 'senha_admin'},
    )
    return response.json()['access_token']
