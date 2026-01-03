from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Cermis Audio API"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str
    API_TOKEN: str

    class Config:
        env_file = ".env"

settings = Settings()
