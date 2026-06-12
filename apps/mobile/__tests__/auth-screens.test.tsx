import { screen } from "@testing-library/react-native";
import Login from "../app/(auth)/login";
import Register from "../app/(auth)/register";
import { renderWithProviders } from "../src/test-utils";

test("login renderiza campos e botão", async () => {
  await renderWithProviders(<Login />, { user: null });
  expect(screen.getByText("Entrar no Helfy")).toBeTruthy();
  expect(screen.getByText("E-mail")).toBeTruthy();
  expect(screen.getByText("Senha")).toBeTruthy();
  expect(screen.getByText("Entrar")).toBeTruthy();
});

test("registro renderiza campos e botão", async () => {
  await renderWithProviders(<Register />, { user: null });
  expect(screen.getByText("Criar conta")).toBeTruthy();
  expect(screen.getByText("Nome")).toBeTruthy();
  expect(screen.getByText("Cadastrar")).toBeTruthy();
});
