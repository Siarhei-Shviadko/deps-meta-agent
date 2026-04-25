from .base import NotFoundError

__all__ = ["ManifestNotFound"]


class ManifestNotFound(NotFoundError):
    code = "manifest_not_found"

    def __init__(self, code: str) -> None:
        super().__init__(f"Manifest with code `{code}` not found.")
