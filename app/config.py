from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1

    # Google Login
    GOOGLE_CLIENT_ID: str = ""

    # Password reset / Email verification
    RESET_TOKEN_EXPIRE_MINUTES: int = 10

    #url of frontend and ai servers
    FRONTEND_URL: str 
    FRONTEND_URL_RAILWAY: str
    FRONTEND_URL_RAILWAY2: str
    AI_SERVICE_URL: str

    # SMTP (Gmail)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_EMAIL: str
    SMTP_PASSWORD: str

    # Brevo Email API
    #BREVO_API_KEY: str
    #BREVO_SENDER_EMAIL: str
    #BREVO_SENDER_NAME: str = "Ghusn"

    
    MAX_IMAGE_SIZE_MB: int = 5

    #supabase storage

    SUPABASE_URL: str
    SUPABASE_SECRET_KEY: str
    SUPABASE_BUCKET: str

    model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore"
        )
    


settings = Settings()

