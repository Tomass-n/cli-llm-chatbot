"""
Endpoint de health check.

Separamos cada grupo de endpoints en su propio archivo para:
1. Archivos pequeños y fáciles de entender
2. Equipos pueden trabajar en paralelo
3. Fácil de encontrar dónde está cada endpoint
"""

from fastapi import APIRouter

from app.config import get_settings
from app.models.schemas import HealthResponse

# Crea un router para este grupo de endpoints
# prefix="" porque /health va en la raíz
router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Verifica que la API está funcionando.

    Usado por:
    - Load balancers para saber si el servidor está healthy
    - Sistemas de monitoreo (UptimeRobot, etc.)
    - Tu propio dashboard para ver status

    Returns:
        HealthResponse con status "ok" y versión de la API
    """
    settings = get_settings()
    return HealthResponse(status="ok", version=settings.app_version)
