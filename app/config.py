from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    bot_token: str
    admin_ids: List[int]
    postgres_dsn: str
    salt_price: int

    class Config:
        env_file = ".env"

def load_config():
    return Settings()
