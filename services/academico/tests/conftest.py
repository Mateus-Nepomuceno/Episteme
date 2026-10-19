from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from academico.app import app
from academico.database import get_session
from academico.models import table_registry
from academico.security import CurrentUser


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
def current_user_override():
    def override():
        return CurrentUser(id=uuid4(), email='maria@teste.com', e_admin=False)

    app.dependency_overrides[
        app.dependency_overrides.get('get_current_user', None)
    ] = override
    yield
    app.dependency_overrides.clear()
