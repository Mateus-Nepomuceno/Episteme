from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from turma.models import DiaSemana


class Mensagem(BaseModel):
    mensagem: str


# Filter
class FiltroPaginacao(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)


# Aluno schemas
class AlunoCreate(BaseModel):
    usuario_id: UUID
    matricula_id: str
    # UUID do curso, o mesmo identificador usado pelo serviço acadêmico.
    curso_id: str
    ativo: bool = True

    @field_validator('curso_id')
    @classmethod
    def validar_curso_id(cls, valor: str) -> str:
        try:
            return str(UUID(valor))
        except ValueError:
            mensagem = (
                'curso_id deve ser o identificador (UUID) do curso '
                'cadastrado no serviço acadêmico'
            )
            raise ValueError(mensagem)


class AlunoPublic(BaseModel):
    id: UUID
    usuario_id: UUID
    matricula_id: str
    curso_id: str
    ativo: bool
    model_config = ConfigDict(from_attributes=True)


class AlunoList(BaseModel):
    alunos: list[AlunoPublic]


# Professor schemas
class ProfessorCreate(BaseModel):
    usuario_id: UUID
    matricula_id: str
    ativo: bool = True


class ProfessorPublic(BaseModel):
    id: UUID
    usuario_id: UUID
    matricula_id: str
    ativo: bool
    model_config = ConfigDict(from_attributes=True)


class ProfessorList(BaseModel):
    professores: list[ProfessorPublic]


# Turma schemas
PERIODO_LETIVO_PATTERN = r'^\d{4}\.[12]$'


class TurmaCreate(BaseModel):
    nome: str
    codigo: str
    materia: str
    curso_id: UUID
    periodo_letivo: str = Field(pattern=PERIODO_LETIVO_PATTERN)
    capacidade: int = Field(gt=0)
    professor_id: UUID | None = None

    aluno_ids: list[UUID] = Field(default_factory=list)
    documentos: list[str] = Field(default_factory=list)
    avisos: list[str] = Field(default_factory=list)


class HorarioTurmaPublic(BaseModel):
    dia_semana: DiaSemana
    horario_inicio: time
    horario_fim: time
    local: str
    model_config = ConfigDict(from_attributes=True)


class ProfessorTurmaPublic(BaseModel):
    id: UUID
    matricula_id: str
    model_config = ConfigDict(from_attributes=True)


class TurmaPublic(BaseModel):
    id: UUID
    nome: str
    codigo: str | None
    materia: str
    curso_id: UUID | None
    periodo_letivo: str | None
    capacidade: int | None
    professor: ProfessorPublic | None
    alunos: list[AlunoPublic]
    horarios: list[HorarioTurmaPublic]
    documentos: list[str]
    avisos: list[str]
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class TurmaList(BaseModel):
    turmas: list[TurmaPublic]


# Oferta de turma para matrícula. Não inclui os alunos matriculados,
# apenas a quantidade de vagas restantes.
class TurmaOfertaPublic(BaseModel):
    id: UUID
    nome: str
    codigo: str | None
    materia: str
    curso_id: UUID | None
    periodo_letivo: str | None
    capacidade: int | None
    vagas_disponiveis: int | None
    professor: ProfessorTurmaPublic | None
    horarios: list[HorarioTurmaPublic]


class TurmaOfertaList(BaseModel):
    turmas: list[TurmaOfertaPublic]


# Horario schemas
class HorarioCreate(BaseModel):
    turma_id: UUID
    professor_id: UUID
    dia_semana: DiaSemana
    horario_inicio: str  # HH:MM
    horario_fim: str  # HH:MM
    local: str


class HorarioPublic(BaseModel):
    id: UUID
    turma: TurmaPublic
    professor: ProfessorPublic
    dia_semana: DiaSemana
    horario_inicio: time
    horario_fim: time
    local: str
    model_config = ConfigDict(from_attributes=True)


class HorarioList(BaseModel):
    horarios: list[HorarioPublic]
