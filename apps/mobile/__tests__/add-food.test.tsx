// jest.mock calls are hoisted before imports, so mockBack must be declared here
// using a module-scoped variable captured via closure in the factory.
const mockBack = jest.fn();

jest.mock("expo-router", () => {
  const React = require("react");
  return {
    useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: mockBack }),
    useLocalSearchParams: () => ({}),
    useFocusEffect: (cb: () => void) => React.useEffect(cb, []),
    Redirect: () => null,
    Link: ({ children }: { children: React.ReactNode }) => children,
    Stack: Object.assign(() => null, { Screen: () => null }),
    Tabs: Object.assign(() => null, { Screen: () => null }),
  };
});

import { screen, userEvent, waitFor } from "@testing-library/react-native";
import AddFood from "../app/add-food";
import { fakeUser, renderWithProviders } from "../src/test-utils";

const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof fetch;

afterEach(() => {
  fetchMock.mockReset();
  mockBack.mockReset();
});

test("aba Câmera renderiza visualização padrão com permissão concedida", async () => {
  fetchMock.mockResolvedValue({ ok: false, status: 404, json: () => Promise.resolve({}) });
  await renderWithProviders(<AddFood />);
  expect(screen.getByRole("button", { name: "Câmera" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Manual" })).toBeTruthy();
});

test("aba Manual renderiza formulário de adição manual", async () => {
  fetchMock.mockResolvedValue({ ok: false, status: 404, json: () => Promise.resolve({}) });
  await renderWithProviders(<AddFood />);
  const user = userEvent.setup();
  await user.press(screen.getByRole("button", { name: "Manual" }));
  expect(screen.getByText("Nome do alimento")).toBeTruthy();
});

test("formulário manual submete e navega para trás", async () => {
  fetchMock.mockImplementation((url: string, init?: RequestInit) => {
    if (url.includes("/alimentos") && init?.method === "POST") {
      return Promise.resolve({
        ok: true, status: 201, json: () => Promise.resolve({ id: "f99", name: "Banana" }),
      });
    }
    if (url.includes("/adicionar")) {
      return Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve({ id: "pi99", user_id: fakeUser.id, food_id: "f99", food: { id: "f99", name: "Banana" } }),
      });
    }
    return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) });
  });

  await renderWithProviders(<AddFood />);
  const user = userEvent.setup();
  await user.press(screen.getByRole("button", { name: "Manual" }));
  await user.type(screen.getByPlaceholderText("Ex: Arroz integral"), "Banana");
  await user.press(screen.getByRole("button", { name: "Adicionar" }));
  await waitFor(() => expect(mockBack).toHaveBeenCalled());
});
