import { screen, userEvent, waitFor } from "@testing-library/react-native";
import PantryTab from "../app/(tabs)/pantry";
import { fakeUser, renderWithProviders } from "../src/test-utils";

const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof fetch;

const fakeFood = { id: "f1", name: "Arroz", barcode: null };
const fakePantryItem = { id: "pi1", user_id: fakeUser.id, food_id: "f1", food: fakeFood };
const fakeScore = { user_id: fakeUser.id, food_id: "f1", score: 0.85, justification: "Rico em fibras" };

function mockFetch(pantryItems: typeof fakePantryItem[], scoreItems: typeof fakeScore[]) {
  fetchMock.mockImplementation((url: string, init?: RequestInit) => {
    if (url.includes("/dispensa/") && (!init?.method || init.method === "GET")) {
      return Promise.resolve({
        ok: true, status: 200, json: () => Promise.resolve(pantryItems),
      });
    }
    if (url.includes("/score")) {
      return Promise.resolve({
        ok: true, status: 200, json: () => Promise.resolve(scoreItems),
      });
    }
    if (url.includes("/dispensa/") && init?.method === "DELETE") {
      return Promise.resolve({ ok: true, status: 204, json: () => Promise.resolve(null) });
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
  });
}

afterEach(() => fetchMock.mockReset());

test("exibe estado vazio quando dispensa está vazia", async () => {
  mockFetch([], []);
  await renderWithProviders(<PantryTab />);
  await waitFor(() =>
    expect(screen.getByText(/Sua dispensa está vazia/)).toBeTruthy()
  );
});

test("exibe alimentos com score", async () => {
  mockFetch([fakePantryItem], [fakeScore]);
  await renderWithProviders(<PantryTab />);
  await waitFor(() => expect(screen.getByText("Arroz")).toBeTruthy());
  expect(screen.getByText("8.5")).toBeTruthy();
  expect(screen.getByText("Rico em fibras")).toBeTruthy();
});

test("botão Remover chama API", async () => {
  mockFetch([fakePantryItem], [fakeScore]);
  await renderWithProviders(<PantryTab />);
  await waitFor(() => expect(screen.getByText("Arroz")).toBeTruthy());
  const user = userEvent.setup();
  await user.press(screen.getByRole("button", { name: "Remover Arroz" }));
  await waitFor(() =>
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/dispensa/"),
      expect.objectContaining({ method: "DELETE" }),
    )
  );
});
