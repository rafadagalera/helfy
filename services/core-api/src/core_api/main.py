"""Helfy Core API — Swagger em /docs, ReDoc em /redoc (spec §7)."""
from fastapi import FastAPI

app = FastAPI(
    title="Helfy Core API",
    description="API de produto do Helfy: autenticação, perfil de saúde, alimentos, "
                "dispensa digital, score nutricional e receitas sugeridas.",
    version="1.0.0",
)


@app.get("/health", tags=["system"], summary="Status do serviço")
def health() -> dict:
    return {"status": "ok"}
