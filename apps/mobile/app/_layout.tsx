import { QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { queryClient } from "../src/api/queryClient";
import { SessionProvider } from "../src/session/SessionProvider";

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen
            name="add-food"
            options={{ presentation: "modal", headerShown: true, title: "Adicionar alimento" }}
          />
        </Stack>
      </SessionProvider>
    </QueryClientProvider>
  );
}
