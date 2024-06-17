from fastapi import FastAPI
from routes.user_route import router as user_router
from routes.appointments_route import router as appointments_router
from routes.admin_route import router as admin_router

app = FastAPI()

app.include_router(user_router, prefix="/v1", tags=["users"])
app.include_router(appointments_router, prefix="/v1", tags=["appointments"])
app.include_router(admin_router, prefix="/v1/admin", tags=["admin"])





