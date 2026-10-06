from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_as_dataclass,
    mapped_column,
    registry,
    relationship,
)

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

    turmas: Mapped[list['Turma']] = relationship(
        secondary='turma_aluno', back_populates='alunos', default_factory=list
    )

    ativo: Mapped[bool] = mapped_column(default=True)


@mapped_as_dataclass(table_registry)
class Professor:
    __tablename__ = 'professores'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    usuario_id: Mapped[UUID] = mapped_column(unique=True)
    matricula_id: Mapped[str]

    turmas: Mapped[list['Turma']] = relationship(
        back_populates='professor', default_factory=list
    )

    ativo: Mapped[bool] = mapped_column(default=True)


@mapped_as_dataclass(table_registry)
class Turma:
    __tablename__ = 'turmas'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    nome: Mapped[str] = mapped_column()
    professor_id: Mapped[UUID] = mapped_column(
        ForeignKey("professores.id")
    )
    materia: Mapped[str]
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        init=False,
        default=datetime.now
    )

    professor: Mapped[Professor] = relationship(back_populates='turmas')
    alunos: Mapped[list[Aluno]] = relationship(
        secondary='turma_aluno', back_populates='turmas', default_factory=list
    )

    documentos: Mapped[list[str]] = mapped_column(JSON, default=list)
    avisos: Mapped[list[str]] = mapped_column(JSON, default=list)


@mapped_as_dataclass(table_registry)
class TurmaAluno:
    __tablename__ = "turma_aluno"

    turma_id: Mapped[UUID] = mapped_column(
        ForeignKey("turmas.id"), primary_key=True
    )
    aluno_id: Mapped[int] = mapped_column(
        ForeignKey("alunos.id"), primary_key=True
    )
