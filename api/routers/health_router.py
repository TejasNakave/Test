"""from fastapi import APIRouter, HTTPException

Health Router - System health and status endpointsfrom ..schemas import HealthResponse

"""from ..config import settings

from fastapi import APIRouterimport httpx

import timeimport asyncio

import psutilfrom datetime import datetime

import osimport logging

from datetime import datetime

router = APIRouter()

from api.schemas import HealthResponselogger = logging.getLogger(__name__)

from api.config import settings

@router.get("/health", response_model=HealthResponse)

router = APIRouter(prefix="/api/v1", tags=["health"])async def health_check() -> HealthResponse:

    """

# Track startup time    Health check endpoint for monitoring service status and dependencies

startup_time = time.time()    """

    services = {}

@router.get("/health", response_model=HealthResponse)    

async def health_check():    try:

    """        # Check vector database connection

    Comprehensive health check endpoint        try:

    """            async with httpx.AsyncClient(timeout=5.0) as client:

    current_time = time.time()                response = await client.get(f"{settings.VECTOR_DB_URL}/health")

    uptime = current_time - startup_time                services["vector_db"] = "healthy" if response.status_code == 200 else "unhealthy"

            except Exception as e:

    # Check system components            logger.warning(f"Vector DB health check failed: {str(e)}")

    components = {            services["vector_db"] = "unhealthy"

        "api_server": "healthy",        

        "vector_database": "checking...",        # Check LLM API connection (if configured)

        "openai_api": "configured" if settings.OPENAI_API_KEY else "not_configured",        if settings.LLM_API_KEY:

        "document_loader": "available",            try:

    }                async with httpx.AsyncClient(timeout=5.0) as client:

                        headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}

    # Check vector database                    response = await client.get(f"{settings.LLM_BASE_URL}/models", headers=headers)

    try:                    services["llm_api"] = "healthy" if response.status_code == 200 else "unhealthy"

        if os.path.exists(settings.VECTOR_DB_PATH):            except Exception as e:

            components["vector_database"] = "available"                logger.warning(f"LLM API health check failed: {str(e)}")

        else:                services["llm_api"] = "unhealthy"

            components["vector_database"] = "not_found"        else:

    except Exception:            services["llm_api"] = "not_configured"

        components["vector_database"] = "error"        

            # Check database connection (basic check)

    # System statistics        try:

    statistics = {            # This would be replaced with actual DB health check

        "cpu_percent": psutil.cpu_percent(),            # For now, just assume it's healthy if we can import the logger service

        "memory_percent": psutil.virtual_memory().percent,            from ..services.logger import LoggerService

        "disk_usage_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,            services["database"] = "healthy"

        "uptime_seconds": uptime,        except Exception as e:

        "uptime_formatted": format_uptime(uptime)            logger.warning(f"Database health check failed: {str(e)}")

    }            services["database"] = "unhealthy"

            

    return HealthResponse(        overall_status = "healthy" if all(

        status="healthy",            status in ["healthy", "not_configured"] for status in services.values()

        version=settings.APP_VERSION,        ) else "degraded"

        uptime_seconds=uptime,        

        components=components,        return HealthResponse(

        statistics=statistics            status=overall_status,

    )            version="1.0.0",

            timestamp=datetime.now(),

@router.get("/health/simple")            services=services

async def simple_health_check():        )

    """        

    Simple health check for load balancers    except Exception as e:

    """        logger.error(f"Health check failed: {str(e)}")

    return {"status": "ok", "timestamp": datetime.now().isoformat()}        return HealthResponse(

            status="unhealthy",

@router.get("/version")            version="1.0.0",

async def get_version():            timestamp=datetime.now(),

    """            services={"error": str(e)}

    Get application version information        )

    """

    return {@router.get("/health/detailed")

        "app_name": settings.APP_NAME,async def detailed_health_check():

        "version": settings.APP_VERSION,    """

        "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",    Detailed health check with more comprehensive service testing

        "platform": psutil.platform.system()    """

    }    checks = {}

    

def format_uptime(uptime_seconds: float) -> str:    # Basic API health

    """Format uptime in human-readable format"""    basic_health = await health_check()

    days = int(uptime_seconds // 86400)    checks["basic"] = basic_health.dict()

    hours = int((uptime_seconds % 86400) // 3600)    

    minutes = int((uptime_seconds % 3600) // 60)    # Additional checks

    seconds = int(uptime_seconds % 60)    try:

            # Memory usage check

    if days > 0:        import psutil

        return f"{days}d {hours}h {minutes}m {seconds}s"        memory = psutil.virtual_memory()

    elif hours > 0:        checks["memory"] = {

        return f"{hours}h {minutes}m {seconds}s"            "used_percent": memory.percent,

    elif minutes > 0:            "available_mb": memory.available // (1024 * 1024),

        return f"{minutes}m {seconds}s"            "status": "healthy" if memory.percent < 90 else "warning"

    else:        }

        return f"{seconds}s"    except ImportError:
        checks["memory"] = {"status": "unavailable", "message": "psutil not installed"}
    except Exception as e:
        checks["memory"] = {"status": "error", "message": str(e)}
    
    try:
        # Disk usage check
        import shutil
        disk_usage = shutil.disk_usage(".")
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        checks["disk"] = {
            "used_percent": disk_percent,
            "free_gb": disk_usage.free // (1024**3),
            "status": "healthy" if disk_percent < 90 else "warning"
        }
    except Exception as e:
        checks["disk"] = {"status": "error", "message": str(e)}
    
    # Configuration check
    checks["configuration"] = {
        "debug_mode": settings.DEBUG,
        "vector_db_configured": bool(settings.VECTOR_DB_URL),
        "llm_configured": bool(settings.LLM_API_KEY),
        "jwt_configured": bool(settings.JWT_SECRET_KEY != "your-secret-key"),
        "status": "healthy"
    }
    
    return {
        "timestamp": datetime.now(),
        "overall_status": basic_health.status,
        "checks": checks
    }