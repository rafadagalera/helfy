import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { ScrollView, Text, View } from "react-native";
import { useProfile, useSaveProfile } from "../../src/api/hooks";
import type { ActivityLevel, Allergen, DietType, Goal, Restriction } from "../../src/api/types";
import {
  ACTIVITY_LEVELS, ALLERGENS, DIETS, GOALS, RESTRICTIONS,
} from "../../src/constants/profile";
import { Button, Chip, ErrorText, Input, Screen, Title } from "../../src/components/ui";
import { useSession } from "../../src/session/SessionProvider";
import { colors, spacing } from "../../src/theme";

const STEPS = ["Sobre você", "Seu objetivo", "Sua alimentação", "Saúde"] as const;

function toggle<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((i) => i !== item) : [...list, item];
}

export default function Onboarding() {
  const router = useRouter();
  const { user } = useSession();
  const existing = useProfile(user?.id);
  const save = useSaveProfile(user?.id ?? "");

  const [step, setStep] = useState(0);
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

  useEffect(() => {
    const p = existing.data;
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
  }, [existing.data]);

  const step0Valid = !!age && !!heightCm && !!weightKg;
  const step1Valid = goal !== null;

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
      { onSuccess: () => router.replace("/(tabs)") },
    );
  }

  return (
    <Screen>
      <ScrollView showsVerticalScrollIndicator={false}>
        <Text style={{ color: colors.muted, marginBottom: spacing.xs }}>
          Passo {step + 1} de {STEPS.length}
        </Text>
        <Title>{STEPS[step]}</Title>

        {step === 0 && (
          <View>
            <Input label="Idade" value={age} onChangeText={setAge}
                   keyboardType="number-pad" placeholder="Ex: 30" />
            <Input label="Altura (cm)" value={heightCm} onChangeText={setHeightCm}
                   keyboardType="decimal-pad" placeholder="Ex: 170" />
            <Input label="Peso (kg)" value={weightKg} onChangeText={setWeightKg}
                   keyboardType="decimal-pad" placeholder="Ex: 70" />
            <Button title="Continuar" onPress={() => step0Valid && setStep(1)} />
          </View>
        )}

        {step === 1 && (
          <View>
            <Text style={s.label}>Qual o seu objetivo?</Text>
            <View style={s.chips}>
              {GOALS.map((g) => (
                <Chip key={g.value} label={g.label}
                      selected={goal === g.value} onPress={() => setGoal(g.value)} />
              ))}
            </View>
            <Text style={s.label}>Nível de atividade física</Text>
            <View style={s.chips}>
              {ACTIVITY_LEVELS.map((a) => (
                <Chip key={a.value} label={a.label}
                      selected={activity === a.value} onPress={() => setActivity(a.value)} />
              ))}
            </View>
            <Button title="Continuar" onPress={() => step1Valid && setStep(2)} />
            <Button title="Voltar" variant="outline" onPress={() => setStep(0)} />
          </View>
        )}

        {step === 2 && (
          <View>
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
            <Button title="Continuar" onPress={() => setStep(3)} />
            <Button title="Voltar" variant="outline" onPress={() => setStep(1)} />
          </View>
        )}

        {step === 3 && (
          <View>
            <Text style={{ color: colors.muted, marginBottom: spacing.sm }}>
              Opcional — deixe em branco se não souber. Esses dados refinam o seu score.
            </Text>
            <Input label="Colesterol total (mg/dL)" value={cholesterol}
                   onChangeText={setCholesterol} keyboardType="number-pad"
                   placeholder="Ex: 180" />
            <Input label="Glicemia de jejum (mg/dL)" value={glucose}
                   onChangeText={setGlucose} keyboardType="number-pad"
                   placeholder="Ex: 95" />
            <ErrorText>{save.error?.message}</ErrorText>
            <Button title="Concluir" onPress={submit} loading={save.isPending} />
            <Button title="Voltar" variant="outline" onPress={() => setStep(2)} />
          </View>
        )}
      </ScrollView>
    </Screen>
  );
}

const s = {
  label: {
    color: colors.text, fontWeight: "600" as const,
    marginTop: spacing.sm, marginBottom: spacing.xs,
  },
  chips: { flexDirection: "row" as const, flexWrap: "wrap" as const },
};
