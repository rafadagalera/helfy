import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react-native";
import type { ReactElement } from "react";
import { SessionContext, type Session } from "./session/SessionProvider";

export const fakeUser = { id: "u1", email: "ana@helfy.app", name: "Ana" };

export async function renderWithProviders(ui: ReactElement, session: Partial<Session> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const value: Session = {
    ready: true,
    user: fakeUser,
    signIn: jest.fn(),
    signOut: jest.fn(),
    ...session,
  };
  return render(
    <QueryClientProvider client={qc}>
      <SessionContext.Provider value={value}>{ui}</SessionContext.Provider>
    </QueryClientProvider>,
  );
}
