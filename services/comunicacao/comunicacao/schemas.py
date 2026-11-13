from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ComunicadoCreate(BaseModel):
    titulo: str = Field(min_length=1)
    resumo: str = Field(min_length=1)
    corpo: str = Field(min_length=1)
    publicado: bool = True


class ComunicadoPublic(BaseModel):
    id: UUID
    titulo: str
    resumo: str
    corpo: str
    publicado: bool
    publicado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class ComunicadoList(BaseModel):
    comunicados: list[ComunicadoPublic]


class Mensagem(BaseModel):
    mensagem: str
