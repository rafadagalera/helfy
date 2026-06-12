from pydantic import BaseModel, Field


class RecipeOut(BaseModel):
    id: str = Field(description="UUID da receita")
    name: str = Field(description="Nome da receita")
    instructions: str = Field(description="Modo de preparo")
    coverage: float = Field(
        ge=0.0, le=1.0,
        description="Proporção dos ingredientes da receita disponíveis na dispensa (0.0–1.0)")
    score_medio: float | None = Field(
        description="Média dos scores dos ingredientes disponíveis; "
                    "null quando a engine está indisponível (modo degradado)")
    ingredientes_faltantes: list[str] = Field(
        description="UUIDs dos ingredientes ausentes na dispensa do usuário")


class RecipeSuggestionResponse(BaseModel):
    receitas: list[RecipeOut] = Field(
        description="Receitas sugeridas ordenadas por score médio desc "
                    "(ou cobertura desc no modo degradado)")
    scored: bool = Field(
        description="True se os scores foram calculados pela engine; "
                    "False indica modo degradado — engine indisponível, ordenação por cobertura")
