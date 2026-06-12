import type { ReactNode } from "react";
import {
  ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View,
  type TextInputProps,
} from "react-native";
import { colors, spacing } from "../theme";

export function Screen({ children }: { children: ReactNode }) {
  return <View style={styles.screen}>{children}</View>;
}

export function Title({ children }: { children: ReactNode }) {
  return <Text style={styles.title}>{children}</Text>;
}

export function ErrorText({ children }: { children: ReactNode }) {
  if (!children) return null;
  return <Text style={styles.error}>{String(children)}</Text>;
}

export function Button({
  title, onPress, loading = false, variant = "primary",
}: {
  title: string;
  onPress: () => void;
  loading?: boolean;
  variant?: "primary" | "outline" | "danger";
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={loading}
      style={[styles.button, variant === "outline" && styles.buttonOutline,
              variant === "danger" && styles.buttonDanger]}
    >
      {loading ? (
        <ActivityIndicator color={variant === "outline" ? colors.primary : "#fff"} />
      ) : (
        <Text style={[styles.buttonText, variant === "outline" && styles.buttonTextOutline]}>
          {title}
        </Text>
      )}
    </Pressable>
  );
}

export function Input({ label, ...props }: TextInputProps & { label: string }) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        placeholderTextColor={colors.muted}
        autoCapitalize="none"
        {...props}
      />
    </View>
  );
}

export function Chip({
  label, selected, onPress,
}: { label: string; selected: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[styles.chip, selected && styles.chipSelected]}>
      <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{label}</Text>
    </Pressable>
  );
}

export function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <Text style={styles.scoreNa}>—</Text>;
  const bg = score >= 0.7 ? colors.primary : score >= 0.4 ? colors.warning : colors.danger;
  return (
    <View style={[styles.score, { backgroundColor: bg }]}>
      <Text style={styles.scoreText}>{(score * 10).toFixed(1)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg, padding: spacing.md },
  title: { fontSize: 24, fontWeight: "700", color: colors.text, marginBottom: spacing.md },
  error: { color: colors.danger, marginBottom: spacing.sm },
  button: {
    backgroundColor: colors.primary, borderRadius: 8, padding: spacing.md,
    alignItems: "center", marginVertical: spacing.xs,
  },
  buttonOutline: {
    backgroundColor: "transparent", borderWidth: 1, borderColor: colors.primary,
  },
  buttonDanger: { backgroundColor: colors.danger },
  buttonText: { color: "#fff", fontWeight: "600", fontSize: 16 },
  buttonTextOutline: { color: colors.primary },
  field: { marginBottom: spacing.sm },
  label: { color: colors.muted, marginBottom: spacing.xs, fontSize: 13 },
  input: {
    backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border,
    borderRadius: 8, padding: spacing.sm + 2, fontSize: 16, color: colors.text,
  },
  chip: {
    borderWidth: 1, borderColor: colors.border, borderRadius: 16,
    paddingHorizontal: spacing.sm + 4, paddingVertical: spacing.xs + 2,
    marginRight: spacing.xs, marginBottom: spacing.xs, backgroundColor: colors.card,
  },
  chipSelected: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipText: { color: colors.text },
  chipTextSelected: { color: "#fff" },
  score: { borderRadius: 12, paddingHorizontal: spacing.sm, paddingVertical: 2 },
  scoreText: { color: "#fff", fontWeight: "700", fontSize: 13 },
  scoreNa: { color: colors.muted },
});
