import { screen, userEvent } from "@testing-library/react-native";
import ProfileTab from "../app/(tabs)/profile";
import { fakeUser, renderWithProviders } from "../src/test-utils";

const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof fetch;

const fakeProfile = {
  id: "p1", user_id: fakeUser.id,
  age: 28, height_cm: 175, weight_kg: 72,
  goal: "weight_loss" as const,
  diet_type: "omnivore" as const,
  activity_level: "lightly_active" as const,
  restrictions: [], allergies: [],
  preferences: [],
  cholesterol: null, glucose: null,
};

beforeEach(() => {
  fetchMock.mockImplementation((url: string) => {
    if (url.includes("/perfil/")) {
      return Promise.resolve({
        ok: true, status: 200, json: () => Promise.resolve(fakeProfile),
      });
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
  });
});
afterEach(() => fetchMock.mockReset());

test("exibe dados do perfil no modo leitura", async () => {
  await renderWithProviders(<ProfileTab />);
  expect(await screen.findByText(fakeUser.name)).toBeTruthy();
  expect(screen.getByText("28 anos")).toBeTruthy();
  expect(screen.getByRole("button", { name: "Editar" })).toBeTruthy();
});

test("botão Editar exibe formulário de edição", async () => {
  await renderWithProviders(<ProfileTab />);
  await screen.findByRole("button", { name: "Editar" });
  const user = userEvent.setup();
  await user.press(screen.getByRole("button", { name: "Editar" }));
  expect(screen.getByText("Editar perfil")).toBeTruthy();
  expect(screen.getByRole("button", { name: "Salvar" })).toBeTruthy();
});
