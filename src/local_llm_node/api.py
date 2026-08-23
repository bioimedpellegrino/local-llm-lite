"""HTTP API routes."""

from fastapi import APIRouter, HTTPException, Request, status

from local_llm_node import __version__
from local_llm_node.backends.base import InferenceBackend
from local_llm_node.exceptions import BackendUnavailableError, ModelNotFoundError
from local_llm_node.machine import discover_machine_info
from local_llm_node.schemas import (
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    MachineInfoResponse,
    ModelListResponse,
)

router = APIRouter()


def _get_backend(request: Request) -> InferenceBackend:
    """Return the inference backend configured on the application."""
    return request.app.state.inference_backend


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health(request: Request) -> HealthResponse:
    """Return API health and inference backend availability."""
    backend_health = await _get_backend(request).health()
    return HealthResponse(
        status="ok" if backend_health.status == "available" else "degraded",
        service="local-llm-node",
        version=__version__,
        backend=backend_health,
    )


@router.get(
    "/model_list",
    response_model=ModelListResponse,
    responses={503: {"description": "Inference backend unavailable"}},
    tags=["models"],
)
async def model_list(request: Request) -> ModelListResponse:
    """Return the models available through the configured backend."""
    try:
        models = await _get_backend(request).list_models()
    except BackendUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    return ModelListResponse(models=models, count=len(models))


@router.post(
    "/generate",
    response_model=GenerateResponse,
    responses={
        404: {"description": "Requested model not found"},
        503: {"description": "Inference backend unavailable"},
    },
    tags=["inference"],
)
async def generate(
    generation_request: GenerateRequest,
    request: Request,
) -> GenerateResponse:
    """Generate one complete answer for a prompt."""
    try:
        return await _get_backend(request).generate(generation_request)
    except ModelNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except BackendUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get(
    "/machine_info",
    response_model=MachineInfoResponse,
    tags=["system"],
)
def machine_info() -> MachineInfoResponse:
    """Return hardware resources visible to the service."""
    return discover_machine_info()
