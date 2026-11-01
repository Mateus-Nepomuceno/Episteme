from datetime import date, datetime, time
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from turma.models import DiaSemana


class Mensagem(BaseModel):
    mensagem: str


class FiltroPaginacao(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)


class AlunoCreate(BaseModel):
    usuario_id: UUID
    matricula_id: str
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


PERIODO_LETIVO_PATTERN = r'^\d{4}\.[12]$'


class AvisoTurma(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    autor: str = Field(min_length=1)
    data: date
    titulo: str = Field(min_length=1)
    mensagem: str = Field(min_length=1)


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
    avisos: list[AvisoTurma] = Field(default_factory=list)


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
    avisos: list[AvisoTurma]
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class TurmaList(BaseModel):
    turmas: list[TurmaPublic]


class TurmaAlunoPublic(BaseModel):
    id: UUID
    nome: str
    codigo: str | None
    materia: str
    curso_id: UUID | None
    periodo_letivo: str | None
    capacidade: int | None
    professor: ProfessorTurmaPublic | None
    horarios: list[HorarioTurmaPublic]
    model_config = ConfigDict(from_attributes=True)


class TurmaAlunoList(BaseModel):
    turmas: list[TurmaAlunoPublic]


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


class HorarioCreate(BaseModel):
    turma_id: UUID
    professor_id: UUID
    dia_semana: DiaSemana
    horario_inicio: time
    horario_fim: time
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
