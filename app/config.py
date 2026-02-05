from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./alma.db"
    API_KEY: str = "changeme-to-a-secure-key"
    UPLOAD_DIR: str = "./uploads"
    ATTORNEY_EMAIL: str = "attorney@alma.com"
    AUTH_ENABLED: bool = True

    model_config = {"env_file": ".env"}


settings = Settings()
