# bot/config.py
from pydantic import BaseSettings, SecretStr


class Settings(BaseSettings):
    bot_token: SecretStr
    openai_api_key: SecretStr
    use_webhook: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
