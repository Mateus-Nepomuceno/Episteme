from uuid import UUID
from datetime import datetime

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

class CadastroAcademicoResponse(BaseModel):
    mensagem: str
    usuario_id: UUID
    aluno_id: UUID
    curso_id: str

class SolicitacaoMatriculaCreate(BaseModel):
    periodo_letivo: str = Field(pattern=r'^\d{4}\.[12]$')
    turmas_ids: list[UUID] = Field(min_length=1)


class SolicitacaoMatriculaResponse(BaseModel):
    mensagem: str
    id: UUID
    protocolo: UUID
    usuario_id: UUID
    aluno_id: UUID
    curso_id: UUID
    periodo_letivo: str
    turmas_ids: list[UUID]
    situacao: str
    data_solicitacao: datetime

    model_config = ConfigDict(from_attributes=True)