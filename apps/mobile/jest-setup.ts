jest.mock("expo-router", () => {
  const React = require("react");
  return {
    useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn() }),
    useLocalSearchParams: () => ({}),
    useFocusEffect: (cb: () => void) => React.useEffect(cb, []),
    Redirect: () => null,
    Link: ({ children }: { children: React.ReactNode }) => children,
    Stack: Object.assign(() => null, { Screen: () => null }),
    Tabs: Object.assign(() => null, { Screen: () => null }),
  };
});

jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn().mockResolvedValue(null),
  setItemAsync: jest.fn().mockResolvedValue(undefined),
  deleteItemAsync: jest.fn().mockResolvedValue(undefined),
}));

jest.mock("expo-camera", () => ({
  CameraView: () => null,
  useCameraPermissions: () => [{ granted: true }, jest.fn()],
}));
