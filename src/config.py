from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_DSN: str = 'sqlite+aiosqlite:///database.sqlite'


settings = Settings()
