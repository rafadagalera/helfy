import type { ActivityLevel, Allergen, DietType, Goal, Restriction } from "../api/types";

export const GOALS: { value: Goal; label: string }[] = [
  { value: "EMAGRECER", label: "Emagrecer" },
  { value: "GANHAR_MASSA", label: "Ganhar massa" },
  { value: "MANTER", label: "Manter-me saudável" },
];

export const DIETS: { value: DietType; label: string }[] = [
  { value: "omnivore", label: "Onívoro" },
  { value: "vegetarian", label: "Vegetariano" },
  { value: "vegan", label: "Vegano" },
  { value: "keto", label: "Keto" },
  { value: "pescatarian", label: "Pescetariano" },
  { value: "paleo", label: "Paleo" },
];

export const ACTIVITY_LEVELS: { value: ActivityLevel; label: string }[] = [
  { value: "sedentary", label: "Sedentário" },
  { value: "lightly_active", label: "Levemente ativo" },
  { value: "moderately_active", label: "Moderadamente ativo" },
  { value: "very_active", label: "Muito ativo" },
];

export const ALLERGENS: { value: Allergen; label: string }[] = [
  { value: "gluten", label: "Glúten" },
  { value: "lactose", label: "Lactose" },
  { value: "nuts", label: "Castanhas e nozes" },
  { value: "shellfish", label: "Crustáceos" },
  { value: "eggs", label: "Ovos" },
  { value: "soy", label: "Soja" },
];

export const RESTRICTIONS: { value: Restriction; label: string }[] = [
  { value: "low_sodium", label: "Pouco sódio" },
  { value: "low_sugar", label: "Pouco açúcar" },
  { value: "low_fat", label: "Pouca gordura" },
  { value: "high_protein", label: "Rico em proteína" },
  { value: "low_carb", label: "Low carb" },
];

export const FOOD_GROUPS: { value: string; label: string }[] = [
  { value: "grain", label: "Grãos" },
  { value: "vegetable", label: "Vegetais" },
  { value: "fruit", label: "Frutas" },
  { value: "meat", label: "Carnes" },
  { value: "fish", label: "Peixes" },
  { value: "dairy", label: "Laticínios" },
  { value: "egg", label: "Ovos" },
  { value: "legume", label: "Leguminosas" },
  { value: "other", label: "Outros" },
];

export function labelFor<T extends string>(
  options: { value: T; label: string }[], value: T | null | undefined,
): string {
  return options.find((o) => o.value === value)?.label ?? String(value ?? "—");
}
