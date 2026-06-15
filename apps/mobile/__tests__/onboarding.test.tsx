import { screen, userEvent, waitFor } from "@testing-library/react-native";
import Onboarding from "../app/onboarding/index";
import { renderWithProviders } from "../src/test-utils";

const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof fetch;

beforeEach(() => {
  fetchMock.mockResolvedValue({
    ok: false, status: 404, json: () => Promise.resolve({ detail: "sem perfil" }),
  });
});
afterEach(() => fetchMock.mockReset());

test("passo 1 renderiza dados básicos e avança ao preencher", async () => {
  await renderWithProviders(<Onboarding />);
  expect(screen.getByText("Sobre você")).toBeTruthy();
  const user = userEvent.setup();
  await user.type(screen.getByPlaceholderText("Ex: 30"), "30");
  await user.type(screen.getByPlaceholderText("Ex: 170"), "170");
  await user.type(screen.getByPlaceholderText("Ex: 70"), "70");
  await user.press(screen.getByRole("button", { name: "Continuar" }));
  await waitFor(() => expect(screen.getByText("Seu objetivo")).toBeTruthy());
});
