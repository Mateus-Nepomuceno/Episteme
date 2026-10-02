from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column, registry

table_registry = registry()


@mapped_as_dataclass(table_registry)
class Usuario:
    __tablename__ = 'usuarios'

    __mapper_args__ = {
        'polymorphic_on': 'tipo',
        'polymorphic_identity': 'USUARIO',
    }

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    nome: Mapped[str]
    senha: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    cpf: Mapped[str]
    telefone: Mapped[str]
    criado_em: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    tipo: Mapped[str] = mapped_column(init=False)


@mapped_as_dataclass(table_registry)
class Aluno(Usuario):
    __tablename__ = 'alunos'

    __mapper_args__ = {
        'polymorphic_identity': 'ALUNO',
    }

    id: Mapped[UUID] = mapped_column(
        ForeignKey('usuarios.id'), primary_key=True, init=False
    )
    matricula_id: Mapped[str]
    curso_id: Mapped[str]
    ativo: Mapped[bool] = mapped_column(default=True)
