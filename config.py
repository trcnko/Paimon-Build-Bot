from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    api_key: SecretStr
    base_url: str
    model_name: str
    genshin_url: str
    bot_token: SecretStr

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()