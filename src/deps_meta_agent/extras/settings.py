from pydantic_settings import BaseSettings, SettingsConfigDict

from .database_session import DBDialect, DBDriver

__all__ = ["SSLSettings", "DatabaseSettings", "ServiceInfoSettings"]


class SSLSettings(BaseSettings):
    key: str = ""
    cert: str = ""
    rootcert: str = ""
    mode: str = "verify-full"

    model_config = SettingsConfigDict(env_prefix="DATABASE_SSL_")


class DatabaseSettings(BaseSettings):
    user: str
    password: str
    host: str
    port: str
    db: str
    ssl: SSLSettings = SSLSettings()
    dialect: DBDialect = DBDialect.POSTGRES
    driver: DBDriver = DBDriver.PSYCOPG2
    require_secure_transport: bool = False
    pool_size: int = 10

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class ServiceInfoSettings(BaseSettings):
    tag: str = ""
    date: str = ""
    hash: str = ""

    model_config = SettingsConfigDict(env_prefix="SERVICE_INFO_")
