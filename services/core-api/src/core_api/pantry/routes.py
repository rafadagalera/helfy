import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from core_api.auth.deps import get_current_user, require_owner
from core_api.db.models import Food, PantryItem, User
from core_api.db.session import get_db
from core_api.foods.off_client import OffUnavailableError, fetch_product
from core_api.foods.routes import _to_out as food_to_out
from core_api.pantry.schemas import PantryAddIn, PantryItemOut

router = APIRouter(prefix="/dispensa", tags=["pantry"])


def _resolve_food(body: PantryAddIn, db: Session) -> Food:
    if body.alimento_id:
        food = db.get(Food, uuid.UUID(body.alimento_id))
        if food is None:
            raise HTTPException(status_code=404, detail="Alimento não encontrado")
        return food
    food = db.scalar(select(Food).where(Food.barcode == body.codigo_barras))
    if food is not None:
        return food
    try:
        normalized = fetch_product(body.codigo_barras)
    except OffUnavailableError:
        raise HTTPException(status_code=502, detail="Base de produtos externa indisponível")
    if normalized is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado na base externa")
    food = Food(**normalized)
    db.add(food)
    db.flush()
    return food


@router.get("/{usuario_id}", response_model=list[PantryItemOut],
            summary="Lista a dispensa do usuário")
def list_pantry(usuario_id: uuid.UUID, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)) -> list[PantryItemOut]:
    require_owner(user, usuario_id)
    rows = db.execute(
        select(PantryItem, Food).join(Food, PantryItem.food_id == Food.id)
        .where(PantryItem.user_id == usuario_id).order_by(Food.name)
    ).all()
    return [PantryItemOut(food=food_to_out(food),
                          quantidade=float(item.quantity) if item.quantity is not None else None)
            for item, food in rows]


@router.post("/{usuario_id}/adicionar", response_model=PantryItemOut, status_code=201,
             summary="Adiciona alimento à dispensa por id ou código de barras")
def add_item(usuario_id: uuid.UUID, body: PantryAddIn,
             user: User = Depends(get_current_user),
             db: Session = Depends(get_db)) -> PantryItemOut:
    require_owner(user, usuario_id)
    food = _resolve_food(body, db)
    item = db.get(PantryItem, (usuario_id, food.id))
    if item is None:
        item = PantryItem(user_id=usuario_id, food_id=food.id)
        db.add(item)
    item.quantity = body.quantidade
    db.commit()
    return PantryItemOut(food=food_to_out(food), quantidade=body.quantidade)


@router.delete("/{usuario_id}/{alimento_id}", status_code=204,
               summary="Remove alimento da dispensa")
def remove_item(usuario_id: uuid.UUID, alimento_id: uuid.UUID,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)) -> Response:
    require_owner(user, usuario_id)
    item = db.get(PantryItem, (usuario_id, alimento_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Item não está na dispensa")
    db.delete(item)
    db.commit()
    return Response(status_code=204)
