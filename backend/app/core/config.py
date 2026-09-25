from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "WhistleDrop API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # PostgreSQL Database URL
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/whistledrop"

    # JWT Authentication for Moderators
    JWT_SECRET: str = "default_dev_secret_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Case code server-side secret key for HMAC-SHA256 hashing
    CASE_CODE_SALT: str = "default_case_code_salt"

    # Frontend URL for production CORS configuration (e.g. Vercel deployment)
    FRONTEND_URL: Optional[str] = None

    # Temporary admin recovery secret (enabled only when explicitly set via environment variable)
    ADMIN_RECOVERY_SECRET: Optional[str] = None


    # Object Storage (Supabase Storage for evidence files)
    STORAGE_PROVIDER: str = "auto"  # "auto", "supabase", or "local"
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "whistledrop-evidence"
    STORAGE_LOCAL_FALLBACK_DIR: str = ".evidence_storage"

    # Allowed CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            v_clean = v.strip()
            # Standardize postgresql drivers for psycopg 3
            if v_clean.startswith("postgres://"):
                return v_clean.replace("postgres://", "postgresql+psycopg://", 1)
            elif v_clean.startswith("postgresql+psycopg2://"):
                return v_clean.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
            elif v_clean.startswith("postgresql://") and not v_clean.startswith("postgresql+"):
                return v_clean.replace("postgresql://", "postgresql+psycopg://", 1)
            return v_clean
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.FRONTEND_URL:
            clean_url = self.FRONTEND_URL.strip().rstrip("/")
            if clean_url and clean_url not in self.CORS_ORIGINS:
                self.CORS_ORIGINS.append(clean_url)

        if self.ENVIRONMENT.lower() == "production":
            if self.JWT_SECRET == "default_dev_secret_change_in_production":
                raise ValueError("JWT_SECRET must be configured with a secure key in production.")
            if self.CASE_CODE_SALT == "default_case_code_salt":
                raise ValueError("CASE_CODE_SALT must be configured with a secure secret key in production.")
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError(
                    "Production database must be PostgreSQL (Supabase). SQLite is strictly prohibited in production."
                )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
