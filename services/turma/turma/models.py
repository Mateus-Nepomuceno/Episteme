import enum
from datetime import date, datetime, time
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Time, UniqueConstraint
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
    horarios: Mapped[list['Horario']] = relationship(
        back_populates='professor', default_factory=list
    )

    ativo: Mapped[bool] = mapped_column(default=True)
    nome: Mapped[str | None] = mapped_column(default=None)


@mapped_as_dataclass(table_registry)
class Turma:
    __tablename__ = 'turmas'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    nome: Mapped[str] = mapped_column()
    materia: Mapped[str]
    codigo: Mapped[str | None] = mapped_column(default=None)
    curso_id: Mapped[UUID | None] = mapped_column(default=None)
    periodo_letivo: Mapped[str | None] = mapped_column(default=None)
    capacidade: Mapped[int | None] = mapped_column(default=None)
    professor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("professores.id"), default=None
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        init=False,
        default=datetime.now
    )

    professor: Mapped[Professor | None] = relationship(
        back_populates='turmas', default=None
    )
    alunos: Mapped[list[Aluno]] = relationship(
        secondary='turma_aluno', back_populates='turmas', default_factory=list
    )
    horarios: Mapped[list['Horario']] = relationship(
        back_populates='turma', cascade='all, delete-orphan', default_factory=list
    )

    documentos: Mapped[list[str]] = mapped_column(JSON, default=list)
    avisos: Mapped[list[dict]] = mapped_column(JSON, default=list)
    encerrada_em: Mapped[datetime | None] = mapped_column(
        DateTime, default=None
    )


@mapped_as_dataclass(table_registry)
class TurmaAluno:
    __tablename__ = "turma_aluno"

    turma_id: Mapped[UUID] = mapped_column(
        ForeignKey("turmas.id"), primary_key=True
    )
    aluno_id: Mapped[UUID] = mapped_column(
        ForeignKey("alunos.id"), primary_key=True
    )
    nota_final: Mapped[float | None] = mapped_column(default=None)
    frequencia_final: Mapped[int | None] = mapped_column(default=None)
    situacao: Mapped[str | None] = mapped_column(default=None)


class DiaSemana(enum.Enum):
    segunda = 'Segunda'
    terca = 'Terça'
    quarta = 'Quarta'
    quinta = 'Quinta'
    sexta = 'Sexta'


@mapped_as_dataclass(table_registry)
class Horario:
    __tablename__ = 'horarios'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    turma_id: Mapped[UUID] = mapped_column(
        ForeignKey("turmas.id")
    )
    professor_id: Mapped[UUID] = mapped_column(
        ForeignKey("professores.id")
    )
    dia_semana: Mapped[DiaSemana]
    horario_inicio: Mapped[time] = mapped_column(Time)
    horario_fim: Mapped[time] = mapped_column(Time)
    local: Mapped[str]

    professor: Mapped[Professor] = relationship(back_populates='horarios', init=False)
    turma: Mapped[Turma] = relationship(back_populates='horarios', init=False)


@mapped_as_dataclass(table_registry)
class Modulo:
    __tablename__ = 'modulos'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    turma_id: Mapped[UUID] = mapped_column(ForeignKey('turmas.id'))
    titulo: Mapped[str]
    ordem: Mapped[int]
    publicado: Mapped[bool] = mapped_column(default=True)


@mapped_as_dataclass(table_registry)
class Material:
    __tablename__ = 'materiais'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    modulo_id: Mapped[UUID] = mapped_column(ForeignKey('modulos.id'))
    titulo: Mapped[str]
    tipo: Mapped[str]
    ordem: Mapped[int]
    descricao: Mapped[str | None] = mapped_column(default=None)


@mapped_as_dataclass(table_registry)
class AcessoMaterial:
    __tablename__ = 'acessos_material'

    material_id: Mapped[UUID] = mapped_column(
        ForeignKey('materiais.id'), primary_key=True
    )
    aluno_id: Mapped[UUID] = mapped_column(
        ForeignKey('alunos.id'), primary_key=True
    )
    aberto_em: Mapped[datetime] = mapped_column(
        DateTime, init=False, default=datetime.now
    )


@mapped_as_dataclass(table_registry)
class Atividade:
    __tablename__ = 'atividades'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    turma_id: Mapped[UUID] = mapped_column(ForeignKey('turmas.id'))
    titulo: Mapped[str]
    tipo: Mapped[str]
    categoria: Mapped[str]
    prazo: Mapped[datetime] = mapped_column(DateTime)
    pontos: Mapped[float | None] = mapped_column(default=None)
    descricao: Mapped[str | None] = mapped_column(default=None)
    publicada: Mapped[bool] = mapped_column(default=True)
    modulo_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('modulos.id'), default=None
    )


@mapped_as_dataclass(table_registry)
class Entrega:
    __tablename__ = 'entregas'

    atividade_id: Mapped[UUID] = mapped_column(
        ForeignKey('atividades.id'), primary_key=True
    )
    aluno_id: Mapped[UUID] = mapped_column(
        ForeignKey('alunos.id'), primary_key=True
    )
    entregue_em: Mapped[datetime] = mapped_column(
        DateTime, init=False, default=datetime.now
    )


@mapped_as_dataclass(table_registry)
class Avaliacao:
    __tablename__ = 'avaliacoes'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    turma_id: Mapped[UUID] = mapped_column(ForeignKey('turmas.id'))
    nome: Mapped[str]
    tipo: Mapped[str]
    data: Mapped[date]
    peso: Mapped[float]


@mapped_as_dataclass(table_registry)
class Nota:
    __tablename__ = 'notas'

    avaliacao_id: Mapped[UUID] = mapped_column(
        ForeignKey('avaliacoes.id'), primary_key=True
    )
    aluno_id: Mapped[UUID] = mapped_column(
        ForeignKey('alunos.id'), primary_key=True
    )
    valor: Mapped[float]
    lancada_em: Mapped[datetime] = mapped_column(
        DateTime, init=False, default=datetime.now
    )


@mapped_as_dataclass(table_registry)
class Chamada:
    __tablename__ = 'chamadas'
    __table_args__ = (UniqueConstraint('turma_id', 'data'),)

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, init=False
    )
    turma_id: Mapped[UUID] = mapped_column(ForeignKey('turmas.id'))
    data: Mapped[date]


@mapped_as_dataclass(table_registry)
class Presenca:
    __tablename__ = 'presencas'

    chamada_id: Mapped[UUID] = mapped_column(
        ForeignKey('chamadas.id'), primary_key=True
    )
    aluno_id: Mapped[UUID] = mapped_column(
        ForeignKey('alunos.id'), primary_key=True
    )
    presente: Mapped[bool]
