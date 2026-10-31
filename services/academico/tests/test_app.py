from http import HTTPStatus
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from academico.app import app


def test_root(client):
    response = client.get('/')
    assert response.status_code == HTTPStatus.OK


def test_scheduler_de_periodos_inicia_com_a_aplicacao():
    with patch(
        'academico.app.executar_scheduler_periodos',
        new=AsyncMock(),
    ) as scheduler, TestClient(app):
        pass

    scheduler.assert_called_once()
