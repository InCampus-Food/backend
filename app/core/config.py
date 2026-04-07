from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: str = "redis://localhost:6379"
    MIDTRANS_SERVER_KEY: str
    MIDTRANS_CLIENT_KEY: str
    MIDTRANS_IS_PRODUCTION: bool = False
    COOKIE_SECURE: bool = False  # Set True in production (HTTPS)
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
