from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    bot_token: str
    admin_ids: List[int]
    postgres_dsn: str
    salt_price: int
    card_number: str  # Новое поле для номера карты

    @field_validator("admin_ids", mode="before")
    @classmethod
    def split_admins(cls, v):
        if isinstance(v, str):
            return [int(x) for x in v.split(",") if x]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def load_config() -> Settings:
    return Settings()