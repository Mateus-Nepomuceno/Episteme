from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from comunicacao.app import app
from comunicacao.database import get_session
from comunicacao.models import table_registry
from comunicacao.security import CurrentUser, get_current_user


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
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


def como(e_admin=False):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(), email='usuario@teste.com', e_admin=e_admin
    )
