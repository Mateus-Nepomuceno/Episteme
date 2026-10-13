from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    curso_id: str
    ativo: bool = True


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
class TurmaCreate(BaseModel):
    nome: str
    professor_id: UUID
    materia: str

    aluno_ids: list[UUID] = Field(default_factory=list)
    documentos: list[str] = Field(default_factory=list)
    avisos: list[str] = Field(default_factory=list)


class TurmaPublic(BaseModel):
    id: UUID
    nome: str
    professor: ProfessorPublic
    materia: str
    alunos: list[AlunoPublic]
    documentos: list[str]
    avisos: list[str]
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class TurmaList(BaseModel):
    turmas: list[TurmaPublic]


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
