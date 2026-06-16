import { useRouter } from "expo-router";
import { useState } from "react";
import { ScrollView, Text, View } from "react-native";
import { useProfile, useSaveProfile } from "../../src/api/hooks";
import type { ActivityLevel, Allergen, DietType, Goal, Restriction } from "../../src/api/types";
import {
  ACTIVITY_LEVELS, ALLERGENS, DIETS, GOALS, RESTRICTIONS, labelFor,
} from "../../src/constants/profile";
import { Button, Chip, ErrorText, Input, Screen, Title } from "../../src/components/ui";
import { useSession } from "../../src/session/SessionProvider";
import { colors, spacing } from "../../src/theme";

function toggle<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((i) => i !== item) : [...list, item];
}

export default function ProfileTab() {
  const router = useRouter();
  const { user, signOut } = useSession();
  const existing = useProfile(user?.id);
  const save = useSaveProfile(user?.id ?? "");
  const [editing, setEditing] = useState(false);

  const p = existing.data;

  const [age, setAge] = useState("");
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [goal, setGoal] = useState<Goal | null>(null);
  const [activity, setActivity] = useState<ActivityLevel>("lightly_active");
  const [diet, setDiet] = useState<DietType>("omnivore");
  const [restrictions, setRestrictions] = useState<Restriction[]>([]);
  const [allergies, setAllergies] = useState<Allergen[]>([]);
  const [cholesterol, setCholesterol] = useState("");
  const [glucose, setGlucose] = useState("");

  function startEdit() {
    if (!p) return;
    setAge(String(p.age));
    setHeightCm(String(p.height_cm));
    setWeightKg(String(p.weight_kg));
    setGoal(p.goal);
    setActivity(p.activity_level);
    setDiet(p.diet_type);
    setRestrictions(p.restrictions);
    setAllergies(p.allergies);
    setCholesterol(p.cholesterol != null ? String(p.cholesterol) : "");
    setGlucose(p.glucose != null ? String(p.glucose) : "");
    setEditing(true);
  }

  function submit() {
    if (!goal) return;
    save.mutate(
      {
        age: parseInt(age, 10),
        height_cm: parseFloat(heightCm),
        weight_kg: parseFloat(weightKg),
        goal,
        diet_type: diet,
        activity_level: activity,
        cholesterol: cholesterol ? parseInt(cholesterol, 10) : null,
        glucose: glucose ? parseInt(glucose, 10) : null,
        restrictions,
        preferences: [],
        allergies,
      },
      { onSuccess: () => setEditing(false) },
    );
  }

  if (existing.isLoading) {
    return <Screen><Text style={{ color: colors.muted }}>Carregando…</Text></Screen>;
  }

  if (!editing) {
    return (
      <Screen>
        <ScrollView showsVerticalScrollIndicator={false}>
          <Title>{user?.name ?? user?.email}</Title>
          <Text style={{ color: colors.muted, marginBottom: spacing.md }}>{user?.email}</Text>
          {p && (
            <View>
              <Row label="Idade" value={`${p.age} anos`} />
              <Row label="Altura" value={`${p.height_cm} cm`} />
              <Row label="Peso" value={`${p.weight_kg} kg`} />
              <Row label="Objetivo" value={labelFor(GOALS, p.goal)} />
              <Row label="Atividade" value={labelFor(ACTIVITY_LEVELS, p.activity_level)} />
              <Row label="Dieta" value={labelFor(DIETS, p.diet_type)} />
              {p.cholesterol != null && <Row label="Colesterol" value={`${p.cholesterol} mg/dL`} />}
              {p.glucose != null && <Row label="Glicemia" value={`${p.glucose} mg/dL`} />}
            </View>
          )}
          <Button title="Editar" onPress={startEdit} />
          <Button title="Sair" variant="danger" onPress={async () => {
            await signOut();
            router.replace("/(auth)/login");
          }} />
        </ScrollView>
      </Screen>
    );
  }

  return (
    <Screen>
      <ScrollView showsVerticalScrollIndicator={false}>
        <Title>Editar perfil</Title>
        <Input label="Idade" value={age} onChangeText={setAge}
               keyboardType="number-pad" placeholder="Ex: 30" />
        <Input label="Altura (cm)" value={heightCm} onChangeText={setHeightCm}
               keyboardType="decimal-pad" placeholder="Ex: 170" />
        <Input label="Peso (kg)" value={weightKg} onChangeText={setWeightKg}
               keyboardType="decimal-pad" placeholder="Ex: 70" />
        <Text style={s.label}>Objetivo</Text>
        <View style={s.chips}>
          {GOALS.map((g) => (
            <Chip key={g.value} label={g.label}
                  selected={goal === g.value} onPress={() => setGoal(g.value)} />
          ))}
        </View>
        <Text style={s.label}>Atividade física</Text>
        <View style={s.chips}>
          {ACTIVITY_LEVELS.map((a) => (
            <Chip key={a.value} label={a.label}
                  selected={activity === a.value} onPress={() => setActivity(a.value)} />
          ))}
        </View>
        <Text style={s.label}>Tipo de dieta</Text>
        <View style={s.chips}>
          {DIETS.map((d) => (
            <Chip key={d.value} label={d.label}
                  selected={diet === d.value} onPress={() => setDiet(d.value)} />
          ))}
        </View>
        <Text style={s.label}>Restrições nutricionais</Text>
        <View style={s.chips}>
          {RESTRICTIONS.map((r) => (
            <Chip key={r.value} label={r.label} selected={restrictions.includes(r.value)}
                  onPress={() => setRestrictions(toggle(restrictions, r.value))} />
          ))}
        </View>
        <Text style={s.label}>Alergias alimentares</Text>
        <View style={s.chips}>
          {ALLERGENS.map((a) => (
            <Chip key={a.value} label={a.label} selected={allergies.includes(a.value)}
                  onPress={() => setAllergies(toggle(allergies, a.value))} />
          ))}
        </View>
        <Input label="Colesterol (mg/dL)" value={cholesterol}
               onChangeText={setCholesterol} keyboardType="number-pad" placeholder="Ex: 180" />
        <Input label="Glicemia (mg/dL)" value={glucose}
               onChangeText={setGlucose} keyboardType="number-pad" placeholder="Ex: 95" />
        <ErrorText>{save.error?.message}</ErrorText>
        <Button title="Salvar" onPress={submit} loading={save.isPending} />
        <Button title="Cancelar" variant="outline" onPress={() => setEditing(false)} />
      </ScrollView>
    </Screen>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={s.row}>
      <Text style={s.rowLabel}>{label}</Text>
      <Text style={s.rowValue}>{value}</Text>
    </View>
  );
}

const s = {
  label: {
    color: colors.text, fontWeight: "600" as const,
    marginTop: spacing.sm, marginBottom: spacing.xs,
  },
  chips: { flexDirection: "row" as const, flexWrap: "wrap" as const },
  row: {
    flexDirection: "row" as const, justifyContent: "space-between" as const,
    paddingVertical: spacing.xs, borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  rowLabel: { color: colors.muted },
  rowValue: { color: colors.text, fontWeight: "500" as const },
};
