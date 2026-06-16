import { screen, waitFor } from "@testing-library/react-native";
import HomeTab from "../app/(tabs)/index";
import { fakeUser, renderWithProviders } from "../src/test-utils";

const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof fetch;

afterEach(() => fetchMock.mockReset());

const fakeRecipe = {
  id: "r1", name: "Omelete",
  instructions: "Bata os ovos.",
  coverage: 1.0,
  score_medio: 0.85,
  ingredientes_faltantes: ["Ovo"],
};

test("exibe estado vazio quando não há receitas", async () => {
  fetchMock.mockResolvedValue({
    ok: true, status: 200,
    json: () => Promise.resolve({ receitas: [], scored: false }),
  });
  await renderWithProviders(<HomeTab />);
  await waitFor(() =>
    expect(screen.getByText(/Nenhuma receita disponível/)).toBeTruthy()
  );
});

test("exibe receitas sugeridas", async () => {
  fetchMock.mockResolvedValue({
    ok: true, status: 200,
    json: () => Promise.resolve({ receitas: [fakeRecipe], scored: true }),
  });
  await renderWithProviders(<HomeTab />);
  await waitFor(() => expect(screen.getByText("Omelete")).toBeTruthy());
  expect(screen.getByText("Ovo")).toBeTruthy();
});

test("exibe erro quando API falha", async () => {
  fetchMock.mockResolvedValue({
    ok: false, status: 503,
    json: () => Promise.resolve({ detail: "engine down" }),
  });
  await renderWithProviders(<HomeTab />);
  await waitFor(() =>
    expect(screen.getByText(/Erro ao carregar receitas/)).toBeTruthy()
  );
});
