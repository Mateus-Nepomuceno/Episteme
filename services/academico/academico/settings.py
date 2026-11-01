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
    TURMA_API_URL: str = Field(init=False)
    IDENTIDADE_API_URL: str = 'http://127.0.0.1:8000'
    CORS_ORIGINS: str = 'http://localhost:5173'

    @property
    def origens_cors(self) -> list[str]:
        return [
            origem.strip()
            for origem in self.CORS_ORIGINS.split(',')
            if origem.strip()
        ]
