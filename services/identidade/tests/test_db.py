from sqlalchemy import select

from identidade.models import Usuario


def test_create_user(session):
    novo_usuario = Usuario(
        nome='joana',
        senha='senha_secreta',
        email='teste@teste.com',
        cpf='12345678900',
        telefone='(11) 99999-9999',
    )
    session.add(novo_usuario)
    session.commit()

    usuario = session.scalar(select(Usuario).where(Usuario.nome == 'joana'))

    assert usuario.nome == 'joana'
