from typing import Any

from deps_asb import ASBSettings
from deps_kafka import KafkaSettings
from deps_message_flow import MessagingDriverEnum
from deps_rabbitmq import RabbitMQTLSSettings
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from deps_meta_agent.extras import DatabaseSettings, ServiceInfoSettings
from deps_meta_agent.infrastructure.agent.settings import OrchestratorSettings


class Settings(BaseSettings):
    env: str = "development"
    version: str = "1.0"

    logger_level: str = Field("INFO", json_schema_extra={"env": "LOG_LEVEL"})

    info: ServiceInfoSettings = ServiceInfoSettings()
    database: DatabaseSettings = DatabaseSettings()
    orchestrator: OrchestratorSettings = OrchestratorSettings()

    agentic_ai_url: str
    agentic_ai_timeout: int = 120

    messaging_driver: MessagingDriverEnum = Field(
        MessagingDriverEnum.RABBITMQ,
        json_schema_extra={"env": "MESSAGING_DRIVER"},
    )
    messaging_driver_settings: Any = Field(None, json_schema_extra={"env": "MESSAGING_DRIVER_SETTINGS"})
    message_broker_connection_string: str

    documentation_enabled: bool = True
    instrumentation_enabled: bool = False

    meta_agent_url: str

    model_config = SettingsConfigDict(use_enum_values=True, case_sensitive=False)

    @field_validator("messaging_driver_settings", mode="before")
    @classmethod
    def validate_messaging_driver_settings(cls, _: Any, info: ValidationInfo) -> Any:
        messaging_driver = info.data.get("messaging_driver")

        if not messaging_driver:
            raise ValueError("Invalid messaging driver")

        driver = MessagingDriverEnum(messaging_driver)
        if driver == MessagingDriverEnum.ASB:
            return ASBSettings()
        elif driver == MessagingDriverEnum.KAFKA:
            return KafkaSettings()
        elif driver == MessagingDriverEnum.RABBITMQ:
            return RabbitMQTLSSettings().model_dump()

        raise ValueError(f"Driver {driver} is not implemented")
