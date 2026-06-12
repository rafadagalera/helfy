from pydantic import BaseModel, model_validator

from core_api.foods.schemas import FoodOut


class PantryAddIn(BaseModel):
    """Adiciona por id OU por código de barras (exatamente um dos dois)."""
    alimento_id: str | None = None
    codigo_barras: str | None = None
    quantidade: float | None = None

    @model_validator(mode="after")
    def exactly_one_identifier(self):
        if bool(self.alimento_id) == bool(self.codigo_barras):
            raise ValueError("Informe alimento_id OU codigo_barras")
        return self


class PantryItemOut(BaseModel):
    food: FoodOut
    quantidade: float | None
