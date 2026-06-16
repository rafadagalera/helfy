import { ActivityIndicator, FlatList, StyleSheet, Text, View } from "react-native";
import { useSuggestedRecipes } from "../../src/api/hooks";
import type { RecipeOut } from "../../src/api/types";
import { Screen, Title } from "../../src/components/ui";
import { useSession } from "../../src/session/SessionProvider";
import { colors, spacing } from "../../src/theme";

export default function HomeTab() {
  const { user } = useSession();
  const recipes = useSuggestedRecipes(user?.id);

  if (recipes.isLoading) {
    return <Screen><ActivityIndicator color={colors.primary} /></Screen>;
  }

  if (recipes.isError) {
    return (
      <Screen>
        <Title>Receitas</Title>
        <Text style={styles.muted}>Erro ao carregar receitas. Tente novamente.</Text>
      </Screen>
    );
  }

  const data = recipes.data?.receitas ?? [];

  return (
    <Screen>
      <Title>Receitas</Title>
      {data.length === 0 && (
        <Text style={styles.empty}>
          Nenhuma receita disponível. Adicione itens à sua dispensa.
        </Text>
      )}
      <FlatList
        data={data}
        keyExtractor={(r) => r.id}
        renderItem={({ item }) => <RecipeCard recipe={item} />}
      />
    </Screen>
  );
}

function RecipeCard({ recipe }: { recipe: RecipeOut }) {
  const ingredientNames = recipe.ingredientes_faltantes.join(", ");
  return (
    <View style={styles.card}>
      <Text style={styles.recipeName}>{recipe.name}</Text>
      {ingredientNames.length > 0 && (
        <Text style={styles.ingredients}>{ingredientNames}</Text>
      )}
      <Text style={styles.instructions} numberOfLines={2}>{recipe.instructions}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  empty: { color: colors.muted, textAlign: "center", marginTop: spacing.lg },
  muted: { color: colors.muted },
  card: {
    backgroundColor: colors.card, borderRadius: 10, padding: spacing.md,
    marginBottom: spacing.sm, borderWidth: 1, borderColor: colors.border,
  },
  recipeName: { color: colors.text, fontWeight: "700", fontSize: 16, marginBottom: spacing.xs },
  ingredients: { color: colors.primary, fontSize: 13, marginBottom: spacing.xs },
  instructions: { color: colors.muted, fontSize: 13, lineHeight: 18 },
});
