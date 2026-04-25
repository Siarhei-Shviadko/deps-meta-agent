from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Response, status

from deps_meta_agent.application import CommandAgenticManifestService
from deps_meta_agent.containers import Containers
from deps_meta_agent.domain.model import RawAgentEndpoint, RawAgenticManifest

from ...endpoint_marker import MarkerRoute
from ...endpoint_visibility import Visibility
from ...serializers import RegisterManifestRequest, RegisterManifestResponse

__all__ = ["manifests_router"]


manifests_router = APIRouter(prefix="/manifests", tags=["Manifests"], route_class=MarkerRoute)


@manifests_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"visibility": Visibility.PUBLIC},
    response_model=RegisterManifestResponse,
)
@inject
def register_manifest(
    request: RegisterManifestRequest,
    service: CommandAgenticManifestService = Depends(Provide[Containers.command_agentic_manifest_service]),
):
    return RegisterManifestResponse.from_domain(
        service.register(
            RawAgenticManifest(
                code=request.code,
                name=request.name,
                description=request.description,
                endpoint=RawAgentEndpoint(url=request.url, timeout=request.timeout),
            ),
        ),
    )


@manifests_router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra={"visibility": Visibility.INTERNAL},
)
@inject
def delete_manifests(
    codes: list[str] = Query(..., description="List of manifest codes to delete", alias="code"),
    service: CommandAgenticManifestService = Depends(Provide[Containers.command_agentic_manifest_service]),
):
    service.delete(codes)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
