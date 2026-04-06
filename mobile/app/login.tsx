import { MaterialIcons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";

import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
} from "react-native";

import { useRef, useState } from "react";

import { PasswordInput } from "@/components/password-input";
import { Colors } from "@/constants/colors";
import { useAuth } from "@/hooks/use-auth";

export default function LoginScreen() {
  const { signIn } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const passwordRef = useRef<TextInput>(null);

  async function handleSignIn() {
    if (!email.trim()) {
      Alert.alert("Validation Error", "Please enter your email address.");
      return;
    }
    if (!password.trim()) {
      Alert.alert("Validation Error", "Please enter your password.");
      return;
    }

    setIsLoading(true);

    try {
      await signIn(email, password);
      router.replace("/(tabs)");
    } catch (error) {
      Alert.alert(
        "Sign In Error",
        "Failed to sign in. Please try again later.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <ScrollView contentContainerClassName="flex-1 bg-surface flex-col justify-center">
      <View className="items-center justify-center p-6">
        <View
          className="bg-surface-container-low w-full max-w-300 flex-col overflow-hidden rounded-xl"
          style={{
            shadowColor: "#191c22",
            shadowOffset: { width: 0, height: 10 },
            shadowOpacity: 0.06,
            shadowRadius: 30,
            elevation: 8,
          }}
        >
          <View className="bg-surface-container-lowest w-full justify-center p-8">
            <View className="mb-8 -ml-1 flex-row items-center gap-2">
              <MaterialIcons
                name="analytics"
                size={28}
                color={Colors.primary}
              />
              <Text
                className="text-primary text-xl tracking-tight"
                style={{ fontFamily: "Manrope_800ExtraBold" }}
              >
                Wayvia Insider
              </Text>
            </View>

            {/* Welcome header */}
            <View className="mb-10">
              <Text
                className="text-on-surface mb-2 text-3xl tracking-tight"
                style={{ fontFamily: "Manrope_800ExtraBold" }}
              >
                Welcome back
              </Text>
              <Text
                className="text-on-surface-variant text-base"
                style={{ fontFamily: "Inter_400Regular" }}
              >
                Enter your credentials to access your insider portal.
              </Text>
            </View>

            {/* ── form fields ── */}
            <View className="gap-6">
              {/* Email */}
              <View className="gap-2">
                <Text
                  className="text-on-surface-variant text-sm"
                  style={{ fontFamily: "Inter_400Regular" }}
                >
                  Email Address
                </Text>
                <View className="bg-surface-container-low flex-row items-center rounded-lg">
                  <View className="pl-4">
                    <MaterialIcons
                      name="mail"
                      size={20}
                      color={email ? Colors.primary : Colors.onSurfaceVariant}
                    />
                  </View>
                  <TextInput
                    className="font-body text-on-surface flex-1 py-3 pr-4 pl-3 text-sm"
                    placeholder="name@company.com"
                    placeholderTextColor="rgba(114,119,132,0.5)"
                    value={email}
                    onChangeText={setEmail}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoCorrect={false}
                    autoComplete="email"
                    returnKeyType="next"
                    editable={!isLoading}
                    onSubmitEditing={() => passwordRef.current?.focus()}
                  />
                </View>
              </View>

              {/* Password */}
              <View className="gap-2">
                <View className="flex-row items-center justify-between">
                  <Text
                    className="text-on-surface-variant text-sm"
                    style={{ fontFamily: "Inter_400Regular" }}
                  >
                    Password
                  </Text>
                  <Pressable disabled={isLoading} hitSlop={8}>
                    <Text
                      className="text-primary text-sm"
                      style={{ fontFamily: "Inter_600SemiBold" }}
                    >
                      Forgot Password?
                    </Text>
                  </Pressable>
                </View>
                <View className="bg-surface-container-low flex-row items-center rounded-lg">
                  <View className="pl-4">
                    <MaterialIcons
                      name="lock"
                      size={20}
                      color={
                        password ? Colors.primary : Colors.onSurfaceVariant
                      }
                    />
                  </View>
                  <PasswordInput
                    ref={passwordRef}
                    className="font-body text-on-surface flex-1 py-3 pr-4 pl-3 text-sm"
                    placeholder="••••••••"
                    placeholderTextColor="rgba(114,119,132,0.5)"
                    value={password}
                    onChangeText={setPassword}
                    autoComplete="password"
                    returnKeyType="go"
                    editable={!isLoading}
                    onSubmitEditing={handleSignIn}
                  />
                </View>
              </View>

              {/* Sign In button */}
              <Pressable
                onPress={handleSignIn}
                disabled={isLoading}
                style={({ pressed }) => ({
                  transform: [{ scale: pressed ? 0.98 : 1 }],
                  opacity: isLoading ? 0.7 : 1,
                })}
              >
                <LinearGradient
                  colors={["#00458f", "#005cbb"]}
                  start={{ x: 0, y: 0.5 }}
                  end={{ x: 1, y: 0.5 }}
                  style={{
                    shadowColor: "#191c22",
                    shadowOffset: { width: 0, height: 10 },
                    shadowOpacity: 0.06,
                    shadowRadius: 30,
                    elevation: 4,
                    width: "100%",
                    flexDirection: "row",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 8,
                    borderRadius: 9999,
                    paddingVertical: 16,
                  }}
                >
                  {isLoading ? (
                    <ActivityIndicator color="white" />
                  ) : (
                    <>
                      <Text className="font-headline text-on-primary text-base font-bold">
                        Sign In
                      </Text>
                      <MaterialIcons
                        name="arrow-forward"
                        size={20}
                        color="white"
                      />
                    </>
                  )}
                </LinearGradient>
              </Pressable>
            </View>

            {/* Sign-up footer */}
            <View className="mt-3 items-center pt-8">
              <Text
                className="text-on-surface-variant text-sm"
                style={{ fontFamily: "Inter_400Regular" }}
              >
                {"Don't have an account? "}
                <Text
                  className="text-primary text-sm"
                  style={{ fontFamily: "Inter_600SemiBold" }}
                  onPress={() => router.replace("/signup")}
                  suppressHighlighting
                >
                  Sign up
                </Text>
              </Text>
            </View>
          </View>
        </View>
      </View>

      {/* footer text */}
      <Text className="font-label text-on-surface-variant p-2 text-center text-xs tracking-widest uppercase opacity-60">
        Trusted by the world’s greatest omnicommerce brands & partners
      </Text>
    </ScrollView>
  );
}
