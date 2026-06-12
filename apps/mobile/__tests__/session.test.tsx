import { Text } from "react-native";
import { render, screen, waitFor } from "@testing-library/react-native";
import * as SecureStore from "expo-secure-store";
import { SessionProvider, useSession } from "../src/session/SessionProvider";

const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof fetch;

function Probe() {
  const { ready, user } = useSession();
  return <Text>{ready ? (user ? `user:${user.name}` : "anon") : "loading"}</Text>;
}

afterEach(() => fetchMock.mockReset());

test("sem token no storage, fica pronto como anônimo", async () => {
  (SecureStore.getItemAsync as jest.Mock).mockResolvedValueOnce(null);
  render(<SessionProvider><Probe /></SessionProvider>);
  await waitFor(() => expect(screen.getByText("anon")).toBeTruthy());
});

test("com token válido, carrega o usuário de /auth/me", async () => {
  (SecureStore.getItemAsync as jest.Mock).mockResolvedValueOnce("tok-1");
  fetchMock.mockResolvedValue({
    ok: true, status: 200,
    json: () => Promise.resolve({ id: "u1", email: "a@b.c", name: "Ana" }),
  });
  render(<SessionProvider><Probe /></SessionProvider>);
  await waitFor(() => expect(screen.getByText("user:Ana")).toBeTruthy());
});

test("token inválido (401) é descartado e vira anônimo", async () => {
  (SecureStore.getItemAsync as jest.Mock).mockResolvedValueOnce("tok-expirado");
  fetchMock.mockResolvedValue({
    ok: false, status: 401, json: () => Promise.resolve({ detail: "expirado" }),
  });
  render(<SessionProvider><Probe /></SessionProvider>);
  await waitFor(() => expect(screen.getByText("anon")).toBeTruthy());
  expect(SecureStore.deleteItemAsync).toHaveBeenCalled();
});
