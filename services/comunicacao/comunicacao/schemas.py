from datetime import UTC, datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)


def _normalizar_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def _validar_texto(
    valor: str | None,
    campo: str,
    max_tam: int,
    obrigatorio: bool = True,
) -> str | None:
    if valor is None:
        if obrigatorio:
            raise ValueError(f'{campo} é obrigatório.')
        return None
    if not isinstance(valor, str):
        raise ValueError(f'{campo} deve ser uma sequência de caracteres (string).')
    limpo = valor.strip()
    if not limpo:
        raise ValueError(
            f'{campo} não pode ser vazio ou conter apenas espaços em branco.'
        )
    if len(limpo) > max_tam:
        raise ValueError(
            f'{campo} excede o limite máximo permitido de {max_tam} caracteres.'
        )
    return limpo


class ComunicadoCreate(BaseModel):
    titulo: str
    resumo: str
    corpo: str
    publicado: bool = True
    inicio_em: datetime | None = None
    expira_em: datetime | None = None

    @field_validator('titulo')
    @classmethod
    def validar_titulo(cls, v: str) -> str:
        return _validar_texto(v, 'Título', 200, obrigatorio=True)

    @field_validator('resumo')
    @classmethod
    def validar_resumo(cls, v: str) -> str:
        return _validar_texto(v, 'Resumo', 500, obrigatorio=True)

    @field_validator('corpo')
    @classmethod
    def validar_corpo(cls, v: str) -> str:
        return _validar_texto(v, 'Corpo', 20000, obrigatorio=True)

    @model_validator(mode='after')
    def validar_periodo(self):
        inicio = _normalizar_utc(self.inicio_em)
        expira = _normalizar_utc(self.expira_em)
        if inicio and expira and expira <= inicio:
            raise ValueError(
                'A data de término deve ser posterior à data de início'
            )
        return self


class ComunicadoUpdate(BaseModel):
    titulo: str | None = None
    resumo: str | None = None
    corpo: str | None = None
    publicado: bool | None = None
    inicio_em: datetime | None = None
    expira_em: datetime | None = None
    versao: int | None = None

    @field_validator('titulo')
    @classmethod
    def validar_titulo(cls, v: str | None) -> str | None:
        return _validar_texto(v, 'Título', 200, obrigatorio=False)

    @field_validator('resumo')
    @classmethod
    def validar_resumo(cls, v: str | None) -> str | None:
        return _validar_texto(v, 'Resumo', 500, obrigatorio=False)

    @field_validator('corpo')
    @classmethod
    def validar_corpo(cls, v: str | None) -> str | None:
        return _validar_texto(v, 'Corpo', 20000, obrigatorio=False)

    @model_validator(mode='after')
    def validar_periodo(self):
        inicio = _normalizar_utc(self.inicio_em)
        expira = _normalizar_utc(self.expira_em)
        if inicio and expira and expira <= inicio:
            raise ValueError(
                'A data de término deve ser posterior à data de início'
            )
        return self


class ComunicadoPublic(BaseModel):
    id: UUID
    titulo: str
    resumo: str
    corpo: str
    publicado: bool = True
    publicado_em: datetime
    inicio_em: datetime | None = None
    expira_em: datetime | None = None
    versao: int = 1
    atualizado_em: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_serializer(
        'publicado_em',
        'inicio_em',
        'expira_em',
        'atualizado_em',
        when_used='json',
    )
    def serialize_datetime_utc(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt.isoformat().replace('+00:00', 'Z')


class ComunicadoList(BaseModel):
    comunicados: list[ComunicadoPublic]


class Mensagem(BaseModel):
    mensagem: str


