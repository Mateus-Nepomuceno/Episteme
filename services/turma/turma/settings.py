from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    DATABASE_URL: str = Field(init=False)
    SECRET_KEY: str = Field(init=False)
    ALGORITHM: str = Field(init=False)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(init=False)
    # URL base do serviço acadêmico, usada para validar o curso do aluno.
    ACADEMICO_API_URL: str | None = None
