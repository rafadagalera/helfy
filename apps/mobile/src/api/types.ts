export type UserOut = { id: string; email: string; name: string };
export type TokenOut = { access_token: string; token_type: string };

export type Goal = "EMAGRECER" | "GANHAR_MASSA" | "MANTER";
export type DietType =
  | "omnivore" | "vegetarian" | "vegan" | "keto" | "pescatarian" | "paleo";
export type ActivityLevel =
  | "sedentary" | "lightly_active" | "moderately_active" | "very_active";
export type Allergen = "gluten" | "lactose" | "nuts" | "shellfish" | "eggs" | "soy";
export type Restriction =
  | "low_sodium" | "low_sugar" | "low_fat" | "high_protein" | "low_carb";

export type ProfileIn = {
  age: number;
  height_cm: number;
  weight_kg: number;
  goal: Goal;
  diet_type: DietType;
  activity_level: ActivityLevel;
  cholesterol: number | null;
  glucose: number | null;
  restrictions: Restriction[];
  preferences: string[];
  allergies: Allergen[];
};
export type ProfileOut = ProfileIn & { user_id: string };

export type FoodOut = {
  id: string;
  barcode: string | null;
  name: string;
  food_group: string;
  nutrition: Record<string, number>;
  allergen_flags: string[];
  flags: string[];
  source: string;
};
export type FoodManualIn = {
  name: string;
  food_group?: string;
  nutrition?: Record<string, number>;
  allergen_flags?: Allergen[];
  flags?: ("animal_product" | "meat" | "fish")[];
};

export type PantryAddIn = {
  alimento_id?: string;
  codigo_barras?: string;
  quantidade?: number | null;
};
export type PantryItemOut = { food: FoodOut; quantidade: number | null };

export type ScoreOut = { alimento_id: string; score: number; justificativa: string };

export type RecipeOut = {
  id: string;
  name: string;
  instructions: string;
  coverage: number;
  score_medio: number | null;
  ingredientes_faltantes: string[];
};
export type RecipeSuggestionResponse = { receitas: RecipeOut[]; scored: boolean };
