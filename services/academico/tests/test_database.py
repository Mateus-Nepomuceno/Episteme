from unittest.mock import patch

from academico.database import get_session


def test_get_session():
    with patch('academico.database.Session'):
        session_gen = get_session()
        session = next(session_gen)
        assert session is not None
