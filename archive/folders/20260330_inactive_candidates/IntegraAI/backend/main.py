from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.advanced_services import router as advanced_router
from app.api.projects import router as projects_router
from app.config import settings
from app.database import Base, engine
from app.schemas import ApiStatus


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IntegraAI API",
    version=settings.app_version,
    description="Smart mechanical consultancy platform for Saudi engineering offices.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router, prefix=f"{settings.api_prefix}/projects", tags=["projects"])
app.include_router(advanced_router, prefix=settings.api_prefix, tags=["advanced-services"])


@app.get("/", response_model=ApiStatus)
def root():
    return ApiStatus(status="ok", service=settings.app_name, version=settings.app_version)


@app.get("/health", response_model=ApiStatus)
def health():
    return ApiStatus(status="healthy", service=settings.app_name, version=settings.app_version)


@app.get(f"{settings.api_prefix}/status", response_model=ApiStatus)
def api_status():
    return ApiStatus(status="ok", service="IntegraAI-API", version=settings.app_version)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
