from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column, registry

table_registry = registry()


@mapped_as_dataclass(table_registry)
class Disciplina:
    __tablename__ = 'disciplinas'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    codigo: Mapped[str] = mapped_column(unique=True)
    nome: Mapped[str]
    carga_horaria: Mapped[int]
    tipo: Mapped[str]
    departamento: Mapped[str]
    creditos: Mapped[int | None] = mapped_column(default=None)
    periodo_curricular: Mapped[int | None] = mapped_column(default=None)
    ementa: Mapped[str | None] = mapped_column(default=None)
    bibliografia: Mapped[str | None] = mapped_column(default=None)
    pre_requisitos: Mapped[str | None] = mapped_column(default=None)


@mapped_as_dataclass(table_registry)
class Curso:
    __tablename__ = 'cursos'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    codigo: Mapped[str] = mapped_column(unique=True)
    nome: Mapped[str]
    tipo_formacao: Mapped[str]
    modalidade: Mapped[str]
    nivel_academico: Mapped[str]
    carga_horaria_total: Mapped[int]
    campus: Mapped[str]
    duracao: Mapped[int | None] = mapped_column(default=None)
    documentacao: Mapped[str | None] = mapped_column(default=None)
    ativo: Mapped[bool] = mapped_column(default=True)
