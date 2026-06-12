"""
Cliente do Open Food Facts (SCRUM-14) e normalização para o formato canônico
do Helfy (mesmas chaves de nutrition que a score-engine espera).
"""
import logging

import httpx

from core_api.settings import settings

logger = logging.getLogger(__name__)

# en:fish fica de fora de propósito: alergia a peixe ≠ alergia a crustáceos, e o
# vocabulário da engine não tem "fish" como alérgeno — marcar errado é pior que omitir
OFF_ALLERGEN_MAP = {
    "en:gluten": "gluten", "en:milk": "lactose", "en:nuts": "nuts",
    "en:peanuts": "nuts", "en:crustaceans": "shellfish",
    "en:eggs": "eggs", "en:soybeans": "soy",
}

OFF_FOOD_GROUP_KEYWORDS = [
    ("meat", "meat"), ("poultry", "meat"), ("fishes", "fish"), ("seafood", "fish"),
    ("dairies", "dairy"), ("cheeses", "dairy"), ("yogurts", "dairy"),
    ("fruits", "fruit"), ("vegetables", "vegetable"), ("legumes", "legume"),
    ("cereals", "grain"), ("breads", "grain"), ("pastas", "grain"),
    ("snacks", "snack"), ("beverages", "beverage"), ("eggs", "egg"),
]

ANIMAL_GROUPS = {"meat", "fish", "dairy", "egg"}


def _food_group_from_categories(categories: list[str]) -> str:
    for keyword, group in OFF_FOOD_GROUP_KEYWORDS:
        if any(keyword in cat for cat in categories):
            return group
    return "other"


def normalize_off_product(barcode: str, product: dict) -> dict:
    """Converte um produto do OFF para o dict canônico do Food do Helfy."""
    nutriments = product.get("nutriments") or {}
    nutrition = {
        "energy_kcal_100g": float(nutriments.get("energy-kcal_100g") or 0),
        "proteins_100g": float(nutriments.get("proteins_100g") or 0),
        "carbohydrates_100g": float(nutriments.get("carbohydrates_100g") or 0),
        "fat_100g": float(nutriments.get("fat_100g") or 0),
        "saturated_fat_100g": float(nutriments.get("saturated-fat_100g") or 0),
        "fiber_100g": float(nutriments.get("fiber_100g") or 0),
        "sodium_mg_100g": float(nutriments.get("sodium_100g") or 0) * 1000.0,  # g → mg
        "sugar_100g": float(nutriments.get("sugars_100g") or 0),
    }
    allergens = sorted({OFF_ALLERGEN_MAP[tag]
                        for tag in product.get("allergens_tags") or []
                        if tag in OFF_ALLERGEN_MAP})
    food_group = _food_group_from_categories(product.get("categories_tags") or [])

    flags = []
    if food_group in ANIMAL_GROUPS:
        flags.append("animal_product")
    if food_group == "meat":
        flags.append("meat")
    if food_group == "fish":
        flags.append("fish")

    return {
        "barcode": barcode,
        "name": product.get("product_name") or f"Produto {barcode}",
        "food_group": food_group,
        "nutrition": nutrition,
        "allergen_flags": allergens,
        "flags": flags,
        "source": "OFF",
    }


class OffUnavailableError(Exception):
    pass


def fetch_product(barcode: str) -> dict | None:
    """Busca no OFF. Retorna o dict normalizado, None se não existe, ou levanta
    OffUnavailableError em falha de rede/timeout."""
    url = f"{settings.off_base_url}/api/v2/product/{barcode}.json"
    try:
        resp = httpx.get(url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Open Food Facts indisponível para %s: %s", barcode, exc)
        raise OffUnavailableError(str(exc)) from exc
    if data.get("status") != 1:
        return None
    return normalize_off_product(barcode, data["product"])
