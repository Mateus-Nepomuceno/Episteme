from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class Mensagem(BaseModel):
    mensagem: str


# Usuario schemas
class UsuarioSchema(BaseModel):
    nome: str
    email: EmailStr
    cpf: str
    telefone: str
    e_admin: bool = False


class UsuarioCreate(UsuarioSchema):
    senha: str


class UsuarioPublic(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    e_admin: bool


# JWT
class Token(BaseModel):
    access_token: str
    token_type: str


# Filter
class FiltroPaginacao(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)
