"""Helfy Core API — Swagger em /docs, ReDoc em /redoc (spec §7)."""
from fastapi import FastAPI

from core_api.auth.routes import router as auth_router
from core_api.profile.routes import router as profile_router

app = FastAPI(
    title="Helfy Core API",
    description="API de produto do Helfy: autenticação, perfil de saúde, alimentos, "
                "dispensa digital, score nutricional e receitas sugeridas.",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(profile_router)


@app.get("/health", tags=["system"], summary="Status do serviço")
def health() -> dict:
    return {"status": "ok"}
