import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type {
  FoodManualIn, FoodOut, PantryAddIn, PantryItemOut, ProfileIn, ProfileOut,
  RecipeSuggestionResponse, ScoreOut,
} from "./types";

export const keys = {
  profile: (userId: string) => ["profile", userId] as const,
  pantry: (userId: string) => ["pantry", userId] as const,
  scores: (userId: string, foodIds: string[]) => ["scores", userId, ...foodIds] as const,
  recipes: (userId: string) => ["recipes", userId] as const,
};

export function useProfile(userId: string | undefined) {
  return useQuery({
    queryKey: keys.profile(userId ?? ""),
    queryFn: () => api<ProfileOut>(`/perfil/${userId}`),
    enabled: !!userId,
    retry: false,
  });
}

export function useSaveProfile(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ProfileIn) =>
      api<ProfileOut>(`/perfil/${userId}`, { method: "PUT", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries(),
  });
}

export function usePantry(userId: string | undefined) {
  return useQuery({
    queryKey: keys.pantry(userId ?? ""),
    queryFn: () => api<PantryItemOut[]>(`/dispensa/${userId}`),
    enabled: !!userId,
  });
}

export function useAddPantryItem(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PantryAddIn) =>
      api<PantryItemOut>(`/dispensa/${userId}/adicionar`, {
        method: "POST", body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.pantry(userId) });
      qc.invalidateQueries({ queryKey: keys.recipes(userId) });
    },
  });
}

export function useRemovePantryItem(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (alimentoId: string) =>
      api<void>(`/dispensa/${userId}/${alimentoId}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.pantry(userId) });
      qc.invalidateQueries({ queryKey: keys.recipes(userId) });
    },
  });
}

export function useCreateManualFood() {
  return useMutation({
    mutationFn: (body: FoodManualIn) =>
      api<FoodOut>("/alimentos", { method: "POST", body: JSON.stringify(body) }),
  });
}

export function useScores(userId: string | undefined, foodIds: string[]) {
  return useQuery({
    queryKey: keys.scores(userId ?? "", foodIds),
    queryFn: () =>
      api<ScoreOut[]>("/score", {
        method: "POST",
        body: JSON.stringify({ usuario_id: userId, alimento_ids: foodIds }),
      }),
    enabled: !!userId && foodIds.length > 0,
    retry: false,
  });
}

export function useSuggestedRecipes(userId: string | undefined) {
  return useQuery({
    queryKey: keys.recipes(userId ?? ""),
    queryFn: () => api<RecipeSuggestionResponse>(`/receitas/sugeridas/${userId}`),
    enabled: !!userId,
  });
}
