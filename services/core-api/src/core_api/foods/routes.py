import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from core_api.auth.deps import get_current_user
from core_api.db.models import Food
from core_api.db.session import get_db
from core_api.foods.off_client import OffUnavailableError, fetch_product
from core_api.foods.schemas import FoodManualIn, FoodOut

router = APIRouter(prefix="/alimentos", tags=["foods"],
                   dependencies=[Depends(get_current_user)])


def _to_out(food: Food) -> FoodOut:
    return FoodOut(id=str(food.id), barcode=food.barcode, name=food.name,
                   food_group=food.food_group, nutrition=food.nutrition,
                   allergen_flags=food.allergen_flags, flags=food.flags,
                   source=food.source)


@router.get("/barcode/{codigo}", response_model=FoodOut,
            summary="Busca alimento por código de barras (cache local → Open Food Facts)")
def get_by_barcode(codigo: str, db: Session = Depends(get_db)) -> FoodOut:
    """Busca o alimento pelo código de barras EAN/UPC.
    Consulta primeiro o banco local; se não encontrar, busca na API Open Food Facts
    e persiste o resultado para requisições futuras.
    Retorna 404 se o código não for encontrado; 502 se o Open Food Facts estiver indisponível.
    """
    food = db.scalar(select(Food).where(Food.barcode == codigo))
    if food is not None:
        return _to_out(food)

    try:
        normalized = fetch_product(codigo)
    except OffUnavailableError:
        raise HTTPException(status_code=502,
                            detail="Base de produtos externa indisponível; tente o input manual")
    if normalized is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado na base externa")

    food = Food(**normalized)
    db.add(food)
    db.commit()
    return _to_out(food)


@router.post("", response_model=FoodOut, status_code=201,
             summary="Cadastra alimento manualmente")
def create_manual(body: FoodManualIn, db: Session = Depends(get_db)) -> FoodOut:
    """Cadastra um alimento com informações nutricionais fornecidas manualmente (SCRUM-15).
    Útil quando o produto não está disponível na base Open Food Facts.
    """
    food = Food(name=body.name, food_group=body.food_group, nutrition=body.nutrition,
                allergen_flags=body.allergen_flags, flags=body.flags, source="MANUAL")
    db.add(food)
    db.commit()
    return _to_out(food)


@router.get("/{alimento_id}", response_model=FoodOut, summary="Busca alimento por id")
def get_by_id(alimento_id: uuid.UUID, db: Session = Depends(get_db)) -> FoodOut:
    """Retorna os dados de um alimento pelo seu UUID. Retorna 404 se não encontrado."""
    food = db.get(Food, alimento_id)
    if food is None:
        raise HTTPException(status_code=404, detail="Alimento não encontrado")
    return _to_out(food)
