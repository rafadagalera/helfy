from pydantic import BaseModel, Field, model_validator

from core_api.foods.schemas import FoodOut


class PantryAddIn(BaseModel):
    """Adiciona por id OU por código de barras (exatamente um dos dois)."""
    alimento_id: str | None = Field(
        default=None,
        description="UUID do alimento já cadastrado no sistema")
    codigo_barras: str | None = Field(
        default=None,
        description="Código de barras EAN/UPC; busca ou cria o alimento via Open Food Facts")
    quantidade: float | None = Field(
        default=None,
        description="Quantidade em unidade livre (ex: 500 para 500g, 2 para 2 unidades)")

    @model_validator(mode="after")
    def exactly_one_identifier(self):
        if bool(self.alimento_id) == bool(self.codigo_barras):
            raise ValueError("Informe alimento_id OU codigo_barras")
        return self


class PantryItemOut(BaseModel):
    food: FoodOut = Field(description="Dados completos do alimento")
    quantidade: float | None = Field(description="Quantidade registrada na dispensa")
