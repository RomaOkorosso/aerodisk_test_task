# here will be all imports from all sub-modules
from app.src.auth import (
    auth_router,
    auth_service,
    auth_crud,
    auth_models,
    auth_schemas,
    auth_constants,
)
from app.src.disk_manager import (
    disk_manager_router,
    disk_manager_service,
    disk_manager_crud,
    disk_manager_models,
    disk_manager_schemas,
    disk_manager_init_db,
)
