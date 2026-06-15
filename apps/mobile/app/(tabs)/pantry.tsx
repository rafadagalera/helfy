import { useRouter } from "expo-router";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useRemovePantryItem, usePantry, useScores } from "../../src/api/hooks";
import type { PantryItemOut, ScoreOut } from "../../src/api/types";
import { Screen, ScoreBadge, Title } from "../../src/components/ui";
import { useSession } from "../../src/session/SessionProvider";
import { colors, spacing } from "../../src/theme";

export default function PantryTab() {
  const router = useRouter();
  const { user } = useSession();
  const pantry = usePantry(user?.id);
  const foodIds = (pantry.data ?? []).map((item) => item.food_id);
  const scores = useScores(user?.id, foodIds);
  const remove = useRemovePantryItem(user?.id ?? "");

  const scoreMap = new Map<string, ScoreOut>(
    (scores.data ?? []).map((s) => [s.food_id, s]),
  );

  function scoreFor(foodId: string): number | null {
    return scoreMap.get(foodId)?.score ?? null;
  }

  function justificationFor(foodId: string): string | null {
    return scoreMap.get(foodId)?.justification ?? null;
  }

  if (pantry.isLoading) {
    return <Screen><ActivityIndicator color={colors.primary} /></Screen>;
  }

  return (
    <Screen>
      <Title>Dispensa</Title>
      {pantry.data?.length === 0 && (
        <Text style={styles.empty}>
          Sua dispensa está vazia. Adicione itens pelo botão +.
        </Text>
      )}
      <FlatList
        data={pantry.data ?? []}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <PantryRow
            item={item}
            score={scoreFor(item.food_id)}
            justification={justificationFor(item.food_id)}
            onRemove={() => remove.mutate(item.food_id)}
          />
        )}
      />
      <Pressable
        style={styles.fab}
        onPress={() => router.push("/add-food")}
        accessibilityRole="button"
        accessibilityLabel="Adicionar alimento"
      >
        <Text style={styles.fabText}>+</Text>
      </Pressable>
    </Screen>
  );
}

function PantryRow({
  item, score, justification, onRemove,
}: {
  item: PantryItemOut;
  score: number | null;
  justification: string | null;
  onRemove: () => void;
}) {
  return (
    <View style={styles.row}>
      <View style={styles.rowInfo}>
        <Text style={styles.foodName}>{item.food.name}</Text>
        {justification && (
          <Text style={styles.justification}>{justification}</Text>
        )}
      </View>
      <View style={styles.rowRight}>
        <ScoreBadge score={score} />
        <Pressable
          onPress={onRemove}
          style={styles.removeBtn}
          accessibilityRole="button"
          accessibilityLabel={`Remover ${item.food.name}`}
        >
          <Text style={styles.removeBtnText}>Remover</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  empty: { color: colors.muted, textAlign: "center", marginTop: spacing.lg },
  row: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  rowInfo: { flex: 1, marginRight: spacing.sm },
  rowRight: { alignItems: "flex-end", gap: spacing.xs },
  foodName: { color: colors.text, fontWeight: "500", fontSize: 15 },
  justification: { color: colors.muted, fontSize: 12, marginTop: 2 },
  fab: {
    position: "absolute", bottom: spacing.lg, right: spacing.lg,
    width: 52, height: 52, borderRadius: 26,
    backgroundColor: colors.primary, alignItems: "center", justifyContent: "center",
    elevation: 4,
  },
  fabText: { color: "#fff", fontSize: 28, lineHeight: 32 },
  removeBtn: {
    backgroundColor: colors.danger, borderRadius: 6,
    paddingHorizontal: spacing.sm, paddingVertical: spacing.xs,
  },
  removeBtnText: { color: "#fff", fontSize: 12 },
});
