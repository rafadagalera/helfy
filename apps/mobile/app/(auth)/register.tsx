import { useMutation } from "@tanstack/react-query";
import { Link, useRouter } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, Text, View } from "react-native";
import { api } from "../../src/api/client";
import type { TokenOut, UserOut } from "../../src/api/types";
import { Button, ErrorText, Input, Screen, Title } from "../../src/components/ui";
import { useSession } from "../../src/session/SessionProvider";
import { colors, spacing } from "../../src/theme";

export default function Register() {
  const router = useRouter();
  const { signIn } = useSession();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const register = useMutation({
    mutationFn: async () => {
      await api<UserOut>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ name: name.trim(), email: email.trim(), password }),
      });
      return api<TokenOut>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });
    },
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
        <Title>Criar conta</Title>
        <Input label="Nome" value={name} onChangeText={setName}
               autoCapitalize="words" placeholder="Seu nome" />
        <Input label="E-mail" value={email} onChangeText={setEmail}
               keyboardType="email-address" placeholder="voce@email.com" />
        <Input label="Senha" value={password} onChangeText={setPassword}
               secureTextEntry placeholder="Mínimo 8 caracteres" />
        <ErrorText>{register.error?.message}</ErrorText>
        <Button title="Cadastrar" onPress={() => register.mutate()}
                loading={register.isPending} />
        <View style={{ marginTop: spacing.md, alignItems: "center" }}>
          <Link href="/(auth)/login">
            <Text style={{ color: colors.primary }}>Já tem conta? Entrar</Text>
          </Link>
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}
