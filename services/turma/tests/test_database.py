from unittest.mock import patch

from turma.database import get_session


def test_get_session():
    with patch('turma.database.Session'):
        session_gen = get_session()
        session = next(session_gen)
        assert session is not None
