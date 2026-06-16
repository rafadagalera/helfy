import { CameraView, useCameraPermissions } from "expo-camera";
import { useRouter } from "expo-router";
import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { useAddPantryItem, useCreateManualFood } from "../src/api/hooks";
import { Button, ErrorText, Input, Screen, Title } from "../src/components/ui";
import { useSession } from "../src/session/SessionProvider";
import { colors, spacing } from "../src/theme";

type Tab = "camera" | "manual";

export default function AddFood() {
  const router = useRouter();
  const { user } = useSession();
  const [tab, setTab] = useState<Tab>("camera");
  const addToP = useAddPantryItem(user?.id ?? "");
  const createFood = useCreateManualFood();

  return (
    <Screen>
      <Title>Adicionar alimento</Title>
      <View style={styles.tabs}>
        <TabButton label="Câmera" active={tab === "camera"} onPress={() => setTab("camera")} />
        <TabButton label="Manual" active={tab === "manual"} onPress={() => setTab("manual")} />
      </View>

      {tab === "camera" ? (
        <CameraTab addToP={addToP} onDone={() => router.back()} />
      ) : (
        <ManualTab addToP={addToP} createFood={createFood} onDone={() => router.back()} />
      )}
    </Screen>
  );
}

function TabButton({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={label}
      style={[styles.tab, active && styles.tabActive]}
    >
      <Text style={[styles.tabText, active && styles.tabTextActive]}>{label}</Text>
    </Pressable>
  );
}

function CameraTab({
  addToP, onDone,
}: {
  addToP: ReturnType<typeof useAddPantryItem>;
  onDone: () => void;
}) {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);

  if (!permission?.granted) {
    return (
      <View style={styles.center}>
        <Text style={{ color: colors.muted, marginBottom: spacing.md }}>
          Permissão de câmera necessária
        </Text>
        <Button title="Permitir câmera" onPress={requestPermission} />
      </View>
    );
  }

  if (addToP.isPending) {
    return <View style={styles.center}><ActivityIndicator color={colors.primary} /></View>;
  }

  return (
    <CameraView
      style={styles.camera}
      facing="back"
      onBarcodeScanned={scanned ? undefined : ({ data }) => {
        setScanned(true);
        addToP.mutate({ codigo_barras: data }, { onSuccess: onDone });
      }}
    />
  );
}

function ManualTab({
  addToP, createFood, onDone,
}: {
  addToP: ReturnType<typeof useAddPantryItem>;
  createFood: ReturnType<typeof useCreateManualFood>;
  onDone: () => void;
}) {
  const [name, setName] = useState("");

  const error = createFood.error?.message ?? addToP.error?.message;
  const loading = createFood.isPending || addToP.isPending;

  function submit() {
    if (!name.trim()) return;
    createFood.mutate(
      { name: name.trim() },
      {
        onSuccess: (food) => {
          addToP.mutate({ alimento_id: food.id }, { onSuccess: onDone });
        },
      },
    );
  }

  return (
    <View>
      <Input label="Nome do alimento" value={name} onChangeText={setName}
             placeholder="Ex: Arroz integral" />
      <ErrorText>{error}</ErrorText>
      <Button title="Adicionar" onPress={submit} loading={loading} />
    </View>
  );
}

const styles = StyleSheet.create({
  tabs: { flexDirection: "row", marginBottom: spacing.md },
  tab: {
    flex: 1, paddingVertical: spacing.sm, alignItems: "center",
    borderBottomWidth: 2, borderBottomColor: colors.border,
  },
  tabActive: { borderBottomColor: colors.primary },
  tabText: { color: colors.muted, fontWeight: "600" },
  tabTextActive: { color: colors.primary },
  camera: { flex: 1, minHeight: 300, borderRadius: 12, overflow: "hidden" },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.lg },
});
