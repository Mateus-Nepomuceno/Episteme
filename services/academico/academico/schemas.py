from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Mensagem(BaseModel):
    mensagem: str


# Filter
class FiltroPaginacao(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)


# Disciplina schemas
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


# Curso schemas
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
