import os
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.orm import Session

from identidade.database import engine
from identidade.models import Usuario
from identidade.security import get_password_hash

USUARIOS = [
    ('ADM0001', 'Administrador', 'admin@episteme.dev', True),
    ('P1000', 'Rafael Oliveira', 'rafael.oliveira@episteme.dev', False),
    ('P1001', 'Mariana Silva', 'mariana.silva@episteme.dev', False),
    ('P1002', 'Juliana Alves', 'juliana.alves@episteme.dev', False),
    ('P1003', 'Tatiana Costa', 'tatiana.costa@episteme.dev', False),
    ('2023108420', 'Lucas Costa', 'lucas.costa@episteme.dev', False),
    ('2023108421', 'Beatriz Rocha', 'beatriz.rocha@episteme.dev', False),
    ('2023108422', 'Gabriel Lima', 'gabriel.lima@episteme.dev', False),
]


def usuario_id(matricula: str):
    return uuid5(NAMESPACE_URL, f'usuario:{matricula}')


def main() -> None:
    senha = get_password_hash(os.environ.get('SEED_SENHA', 'senha123456'))
    with Session(engine) as session:
        if session.get(Usuario, usuario_id('ADM0001')) is not None:
            return
        for indice, (matricula, nome, email, admin) in enumerate(USUARIOS):
            usuario = Usuario(
                nome=nome,
                senha=senha,
                email=email,
                cpf=f'{indice:011d}',
                telefone='11999990000',
                e_admin=admin,
                matricula=matricula,
            )
            usuario.id = usuario_id(matricula)
            session.add(usuario)
        session.commit()


if __name__ == '__main__':
    main()
