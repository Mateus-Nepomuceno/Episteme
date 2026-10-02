from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TipoUsuario(Enum):
    ALUNO = 'ALUNO'
    PROFESSOR = 'PROFESSOR'
    ADMIN = 'ADMIN'


class Mensagem(BaseModel):
    mensagem: str


# Usuario schemas
class UsuarioSchema(BaseModel):
    nome: str
    email: EmailStr
    cpf: str
    telefone: str
    tipo: TipoUsuario


class UsuarioCreate(UsuarioSchema):
    senha: str


class UsuarioPublic(BaseModel):
    nome: str
    email: EmailStr


# Aluno schemas
class AlunoCreate(UsuarioCreate):
    matricula_id: str
    curso_id: str
    ativo: bool = True
    tipo: TipoUsuario = TipoUsuario.ALUNO


class AlunoPublic(UsuarioPublic):
    id: UUID
    matricula_id: str
    curso_id: str
    tipo: TipoUsuario = TipoUsuario.ALUNO
    model_config = ConfigDict(from_attributes=True)


class AlunoList(BaseModel):
    alunos: list[AlunoPublic]


# JWT
class Token(BaseModel):
    access_token: str
    token_type: str


# Filter
class FiltroPaginacao(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)


# Professor schemas
class ProfessorCreate(UsuarioCreate):
    matricula_id: str
    departamento_id: str
    ativo: bool = True
    tipo: TipoUsuario = TipoUsuario.PROFESSOR


class ProfessorPublic(UsuarioPublic):
    id: UUID
    matricula_id: str
    departamento_id: str
    tipo: TipoUsuario = TipoUsuario.PROFESSOR
    model_config = ConfigDict(from_attributes=True)


class ProfessorList(BaseModel):
    professores: list[ProfessorPublic]


# Admin schemas
class AdminCreate(UsuarioCreate):
    matricula_id: str
    setor: str
    ativo: bool = True
    tipo: TipoUsuario = TipoUsuario.ADMIN


class AdminPublic(UsuarioPublic):
    id: UUID
    matricula_id: str
    setor: str
    tipo: TipoUsuario = TipoUsuario.ADMIN
    model_config = ConfigDict(from_attributes=True)


class AdminList(BaseModel):
    admins: list[AdminPublic]
