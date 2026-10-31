import re
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)

SENHA_MINIMA = 8
CPF_TAMANHO = 11
TELEFONE_TAMANHOS_NACIONAIS = {10, 11}
TELEFONE_TAMANHOS_COM_PAIS = {12, 13}


class Mensagem(BaseModel):
    mensagem: str


def _cpf_tem_digitos_verificadores_validos(cpf: str) -> bool:
    if cpf == cpf[0] * CPF_TAMANHO:
        return False

    for posicao in (9, 10):
        soma = sum(
            int(cpf[indice]) * ((posicao + 1) - indice)
            for indice in range(posicao)
        )
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[posicao]):
            return False

    return True


def normalizar_cpf(valor: str) -> str:
    digitos = re.sub(r'\D', '', valor)

    if len(digitos) != CPF_TAMANHO or not (
        _cpf_tem_digitos_verificadores_validos(digitos)
    ):
        raise ValueError('CPF inválido')

    return f'{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}'


def normalizar_telefone(valor: str) -> str:
    if not re.fullmatch(r'\+?[\d\s().-]+', valor):
        raise ValueError('Telefone inválido')

    digitos = re.sub(r'\D', '', valor)

    # Aceita o código do Brasil (55) antes do DDD, com ou sem o sinal "+".
    if len(digitos) in TELEFONE_TAMANHOS_COM_PAIS and digitos.startswith(
        '55'
    ):
        digitos = digitos[2:]

    if len(digitos) not in TELEFONE_TAMANHOS_NACIONAIS:
        raise ValueError(
            'Telefone inválido. Informe DDD e número, '
            'por exemplo (11) 99999-9999 ou +5511999998888'
        )

    return f'+55{digitos}'


# Usuario schemas
class UsuarioSchema(BaseModel):
    nome: str
    email: EmailStr
    cpf: str
    telefone: str
    e_admin: bool = False

    @field_validator('cpf')
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        return normalizar_cpf(valor)

    @field_validator('telefone')
    @classmethod
    def validar_telefone(cls, valor: str) -> str:
        return normalizar_telefone(valor)


class UsuarioCreate(UsuarioSchema):
    senha: str = Field(min_length=SENHA_MINIMA)


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
