from datetime import datetime, time, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    field_validator,
    model_validator,
)

MENSAGEM_FUSO_HORARIO = (
    "A data deve incluir o fuso horário, como -03:00 ou +00:00"
)
MENSAGEM_INTERVALO_INVALIDO = "A data final deve ser posterior à data inicial"


def _em_utc(valor: datetime) -> datetime:
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


class Mensagem(BaseModel):
    mensagem: str


class FiltroPaginacao(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)


class DisciplinaCreate(BaseModel):
    codigo: str
    nome: str
    carga_horaria: int
    tipo: str
    departamento: str
    creditos: int | None = None
    periodo_curricular: int | None = None
    ementa: str | None = None
    bibliografia: str | None = None
    pre_requisitos: str | None = None


class DisciplinaPublic(BaseModel):
    id: UUID
    codigo: str
    nome: str
    carga_horaria: int
    tipo: str
    departamento: str
    creditos: int | None
    periodo_curricular: int | None
    ementa: str | None
    bibliografia: str | None
    pre_requisitos: str | None
    model_config = ConfigDict(from_attributes=True)


class DisciplinaList(BaseModel):
    disciplinas: list[DisciplinaPublic]


class CursoCreate(BaseModel):
    codigo: str
    nome: str
    tipo_formacao: str
    modalidade: str
    nivel_academico: str
    carga_horaria_total: int
    campus: str
    duracao: int | None = None
    documentacao: str | None = None
    ativo: bool = True


class CursoPublic(BaseModel):
    id: UUID
    codigo: str
    nome: str
    tipo_formacao: str
    modalidade: str
    nivel_academico: str
    carga_horaria_total: int
    campus: str
    duracao: int | None
    documentacao: str | None
    ativo: bool
    model_config = ConfigDict(from_attributes=True)


class CursoList(BaseModel):
    cursos: list[CursoPublic]


class SolicitacaoMatriculaCreate(BaseModel):
    periodo_letivo: str = Field(pattern=r'^\d{4}\.[12]$')
    turmas_ids: list[UUID] = Field(min_length=1)


class SolicitacaoMatriculaResponse(BaseModel):
    id: UUID
    protocolo: UUID
    usuario_id: UUID
    aluno_id: UUID
    curso_id: UUID
    periodo_letivo: str
    turmas_ids: list[UUID]
    situacao: str
    data_solicitacao: datetime
    observacao: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SolicitacaoMatriculaCriadaResponse(SolicitacaoMatriculaResponse):
    mensagem: str


class SolicitacoesMatriculaList(BaseModel):
    solicitacoes: list[SolicitacaoMatriculaResponse]


class ObservacaoMatriculaUpdate(BaseModel):
    observacao: str | None = Field(default=None, max_length=1000)


class PeriodoMatriculaCreate(BaseModel):
    periodo_letivo: str = Field(
        pattern=r"^\d{4}\.[12]$",
    )
    data_inicial: datetime
    data_final: datetime
    cursos_ids: list[UUID] = Field(min_length=1)
    tipo: Literal["regular", "ajuste", "extraordinario"]
    turmas_ids: list[UUID] = Field(default_factory=list)

    @field_validator("data_inicial", "data_final")
    @classmethod
    def normalizar_data(cls, valor: datetime) -> datetime:
        if valor.tzinfo is None or valor.utcoffset() is None:
            raise ValueError(MENSAGEM_FUSO_HORARIO)

        return valor.astimezone(timezone.utc).replace(tzinfo=None)

    @model_validator(mode="after")
    def validar_intervalo(self):
        if self.data_final <= self.data_inicial:
            raise ValueError(MENSAGEM_INTERVALO_INVALIDO)
        return self


class PeriodoMatriculaResponse(BaseModel):
    id: UUID
    periodo_letivo: str
    data_inicial: Annotated[datetime, PlainSerializer(_em_utc)]
    data_final: Annotated[datetime, PlainSerializer(_em_utc)]
    cursos_ids: list[UUID]
    tipo: Literal["regular", "ajuste", "extraordinario"]
    turmas_ids: list[UUID]
    status: Literal["agendado", "aberto", "encerrado"]

    model_config = ConfigDict(from_attributes=True)


class PeriodoMatriculaCriadoResponse(PeriodoMatriculaResponse):
    mensagem: str


class PeriodosMatriculaList(BaseModel):
    periodos: list[PeriodoMatriculaResponse]


DiaSemanaFiltro = Literal["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]


class HorarioTurmaResponse(BaseModel):
    dia_semana: DiaSemanaFiltro
    horario_inicio: time
    horario_fim: time
    local: str


class ProfessorTurmaResponse(BaseModel):
    id: UUID
    matricula_id: str


class TurmaMatriculadaResponse(BaseModel):
    id: UUID
    nome: str
    codigo: str | None = None
    periodo_letivo: str | None = None
    professor: ProfessorTurmaResponse | None = None
    horarios: list[HorarioTurmaResponse] = Field(default_factory=list)


class DisciplinaMatriculadaResponse(DisciplinaPublic):
    turmas: list[TurmaMatriculadaResponse]


class MinhasDisciplinasResponse(BaseModel):
    disciplinas: list[DisciplinaMatriculadaResponse]


class TurmaDisponivelResponse(BaseModel):
    id: UUID
    nome: str
    codigo: str | None = None
    disciplina: str
    periodo_letivo: str
    capacidade: int | None = None
    vagas_disponiveis: int | None = None
    professor: ProfessorTurmaResponse | None = None
    professor_matricula_id: str | None = None
    horarios: list[HorarioTurmaResponse] = Field(default_factory=list)


class TurmasDisponiveisResponse(BaseModel):
    periodo_letivo: str
    turmas: list[TurmaDisponivelResponse]


class SituacaoAcademicaAlunoPublic(BaseModel):
    aluno_usuario_id: UUID
    matricula: str
    curso: CursoPublic
    ativo: bool
