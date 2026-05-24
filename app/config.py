from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    INTERNAL_BOT_SECRET: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE: int = 30
    ALGORITHM: str = "HS256"
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "db"
    DB_PORT: int = 5433
    DB_NAME: str = "todos"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
