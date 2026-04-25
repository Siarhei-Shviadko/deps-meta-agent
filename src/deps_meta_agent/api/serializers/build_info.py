from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict

__all__ = ["BuildInfoSerializer"]


class BuildInfoSerializer(BaseModel):
    build_tag: str = Field(default="", alias="buildTag")
    build_date: str = Field(default="", alias="buildDate")
    commit_hash: str = Field(default="", alias="commitHash")

    model_config = SettingsConfigDict(validate_by_name=True)
