from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    app_password: str = ""

    @property
    def local_llm_keys(self) -> dict[str, str]:
        """개발 편의용. production 이면 무조건 빈 dict."""
        if self.environment == "production":
            return {}
        candidates = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }
        return {k: v for k, v in candidates.items() if v}


@lru_cache
def get_settings() -> Settings:
    return Settings()
