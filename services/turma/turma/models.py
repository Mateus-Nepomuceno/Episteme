from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column, registry

table_registry = registry()


@mapped_as_dataclass(table_registry)
class Aluno:
    __tablename__ = 'alunos'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    usuario_id: Mapped[UUID] = mapped_column(unique=True)
    matricula_id: Mapped[str]
    curso_id: Mapped[str]
    ativo: Mapped[bool] = mapped_column(default=True)


@mapped_as_dataclass(table_registry)
class Professor:
    __tablename__ = 'professores'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    usuario_id: Mapped[UUID] = mapped_column(unique=True)
    matricula_id: Mapped[str]
    ativo: Mapped[bool] = mapped_column(default=True)
