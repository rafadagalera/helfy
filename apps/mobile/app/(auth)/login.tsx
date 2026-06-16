import { useMutation } from "@tanstack/react-query";
import { Link, useRouter } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, Text, View } from "react-native";
import { api } from "../../src/api/client";
import type { TokenOut } from "../../src/api/types";
import { Button, ErrorText, Input, Screen, Title } from "../../src/components/ui";
import { useSession } from "../../src/session/SessionProvider";
import { colors, spacing } from "../../src/theme";

export default function Login() {
  const router = useRouter();
  const { signIn } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const login = useMutation({
    mutationFn: () =>
      api<TokenOut>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      }),
    onSuccess: async (data) => {
      await signIn(data.access_token);
      router.replace("/");
    },
  });

  return (
    <Screen>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={{ flex: 1, justifyContent: "center" }}
      >
        <Title>Entrar no Helfy</Title>
        <Input label="E-mail" value={email} onChangeText={setEmail}
               keyboardType="email-address" placeholder="voce@email.com" />
        <Input label="Senha" value={password} onChangeText={setPassword}
               secureTextEntry placeholder="••••••••" />
        <ErrorText>{login.error?.message}</ErrorText>
        <Button title="Entrar" onPress={() => login.mutate()} loading={login.isPending} />
        <View style={{ marginTop: spacing.md, alignItems: "center" }}>
          <Link href="/(auth)/register">
            <Text style={{ color: colors.primary }}>Não tem conta? Cadastre-se</Text>
          </Link>
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}
