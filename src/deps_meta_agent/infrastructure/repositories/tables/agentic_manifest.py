from sqlalchemy import Column, DateTime, String, Table
from sqlalchemy.dialects.postgresql import JSONB

from deps_meta_agent.extras import metadata

__all__ = ["agentic_manifest_table"]


agentic_manifest_table = Table(
    "agentic-manifest",
    metadata,
    Column("code", String(150), primary_key=True),
    Column("name", String(150), nullable=False),
    Column("description", String(2000), nullable=False),
    Column("endpoint", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
