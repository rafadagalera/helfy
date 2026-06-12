import { Redirect } from "expo-router";
import { ActivityIndicator, View } from "react-native";
import { useProfile } from "../src/api/hooks";
import { useSession } from "../src/session/SessionProvider";
import { colors } from "../src/theme";

export default function Entry() {
  const { ready, user } = useSession();
  const profile = useProfile(user?.id);

  if (!ready || (user && profile.isLoading)) {
    return (
      <View style={{ flex: 1, justifyContent: "center", backgroundColor: colors.bg }}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }
  if (!user) return <Redirect href="/(auth)/login" />;
  if (profile.error) return <Redirect href="/onboarding" />;
  return <Redirect href="/(tabs)" />;
}
