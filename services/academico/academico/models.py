from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column, registry

table_registry = registry()

from datetime import datetime
from sqlalchemy import JSON, func


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

@mapped_as_dataclass(table_registry)
class SolicitacaoMatricula:
    __tablename__ = 'solicitacoes_matricula'

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        init=False,
    )
    protocolo: Mapped[UUID] = mapped_column(
        unique=True,
        default=uuid4,
        init=False,
    )
    usuario_id: Mapped[UUID]
    aluno_id: Mapped[UUID]
    curso_id: Mapped[UUID]
    periodo_letivo: Mapped[str]
    turmas_ids: Mapped[list[str]] = mapped_column(
        JSON,
        default_factory=list,
        server_default='[]',
    )
    situacao: Mapped[str] = mapped_column(default='pendente')
    data_solicitacao: Mapped[datetime] = mapped_column(
        init=False,
        server_default=func.now(),
    )
