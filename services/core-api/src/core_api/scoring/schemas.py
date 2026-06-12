import uuid

from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    usuario_id: uuid.UUID = Field(
        description="UUID do usuário; deve corresponder ao usuário autenticado")
    alimento_ids: list[uuid.UUID] = Field(
        min_length=1,
        description="UUIDs dos alimentos a pontuar (mínimo 1)")


class ScoreOut(BaseModel):
    alimento_id: str = Field(description="UUID do alimento")
    score: float = Field(
        ge=0.0, le=1.0,
        description="Score de compatibilidade nutricional "
                    "(0.0 = incompatível, 1.0 = ideal para o perfil)")
    justificativa: str = Field(
        description="Explicação em português do score para exibição ao usuário (SCRUM-19)")
