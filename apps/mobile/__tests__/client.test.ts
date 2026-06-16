import { api, ApiError, setAuthToken } from "../src/api/client";

const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof fetch;

function jsonResponse(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  };
}

afterEach(() => {
  fetchMock.mockReset();
  setAuthToken(null);
});

test("api envia Authorization quando há token", async () => {
  fetchMock.mockResolvedValue(jsonResponse(200, { ok: true }));
  setAuthToken("tok-123");
  await api("/auth/me");
  const [, init] = fetchMock.mock.calls[0];
  expect(init.headers.Authorization).toBe("Bearer tok-123");
});

test("api lança ApiError com status e detail em erro HTTP", async () => {
  fetchMock.mockResolvedValue(jsonResponse(409, { detail: "E-mail já cadastrado" }));
  await expect(api("/auth/register", { method: "POST" })).rejects.toMatchObject({
    status: 409,
    message: "E-mail já cadastrado",
  });
});

test("api retorna undefined em 204", async () => {
  fetchMock.mockResolvedValue({ ok: true, status: 204, json: () => Promise.reject() });
  await expect(api("/dispensa/u/f", { method: "DELETE" })).resolves.toBeUndefined();
});

test("ApiError é instanceof Error", () => {
  expect(new ApiError(500, "x")).toBeInstanceOf(Error);
});
