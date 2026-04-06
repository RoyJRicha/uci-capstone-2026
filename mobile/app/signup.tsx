import { MaterialIcons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";

import {
  ActivityIndicator,
  Alert,
  Platform,
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

const smallText = Platform.OS === "ios" ? "text-base" : "text-sm";

export default function Signup() {
  const { signUp } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const passwordRef = useRef<TextInput>(null);

  async function handleSignUp() {
    if (!name.trim()) {
      Alert.alert("Validation Error", "Please enter your name.");
      return;
    }
    if (!email.trim()) {
      Alert.alert("Validation Error", "Please enter your email address.");
      return;
    }
    if (!password.trim()) {
      Alert.alert("Validation Error", "Please enter your password.");
      return;
    }
    if (!termsAccepted) {
      Alert.alert(
        "Validation Error",
        "Please accept the Terms of Service and Privacy Policy.",
      );
      return;
    }

    setIsLoading(true);

    try {
      await signUp(email, password, name);
      router.replace("/(tabs)");
    } catch (error) {
      Alert.alert(
        "Sign Up Error",
        "Failed to sign up. Please try again later.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <ScrollView contentContainerClassName="bg-surface flex-1 flex-col justify-center">
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
            {/* Welcome header */}
            <View className="mb-8.5">
              <Text
                className="text-on-surface mb-4 text-3xl tracking-tight"
                style={{ fontFamily: "Manrope_800ExtraBold" }}
              >
                Create account
              </Text>
              <Text
                className={`text-on-surface-variant ${smallText}`}
                style={{ fontFamily: "Inter_400Regular" }}
              >
                Start your journey to empowering local commerce.
              </Text>
            </View>

            {/* ── form fields ── */}
            <View className="gap-6">
              {/* name */}
              <View className="gap-2">
                <Text
                  className={`text-on-surface-variant ${smallText}`}
                  style={{ fontFamily: "Inter_400Regular" }}
                >
                  Full Name
                </Text>
                <View className="bg-surface-container-low flex-row items-center rounded-lg">
                  <View className="pl-4">
                    <MaterialIcons
                      name="person"
                      size={20}
                      color={name ? Colors.primary : Colors.onSurfaceVariant}
                    />
                  </View>
                  <TextInput
                    className={`font-body text-on-surface flex-1 py-3 pr-4 pl-3 ${smallText} ${Platform.OS === "ios" ? "leading-0" : ""}`}
                    placeholder="Enter your full name"
                    placeholderTextColor="rgba(114,119,132,0.5)"
                    value={name}
                    onChangeText={setName}
                    keyboardType="default"
                    autoCapitalize="none"
                    autoCorrect={false}
                    autoComplete="email"
                    returnKeyType="next"
                    editable={!isLoading}
                    onSubmitEditing={() => passwordRef.current?.focus()}
                  />
                </View>
              </View>

              {/* Email */}
              <View className="gap-2">
                <Text
                  className={`text-on-surface-variant ${smallText}`}
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
                    className={`font-body text-on-surface flex-1 py-3 pr-4 pl-3 ${smallText} ${Platform.OS === "ios" ? "leading-0" : ""}`}
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
                    className={`text-on-surface-variant ${smallText}`}
                    style={{ fontFamily: "Inter_400Regular" }}
                  >
                    Password
                  </Text>
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
                    className={`font-body text-on-surface flex-1 py-3 pr-4 pl-3 ${smallText}`}
                    placeholder="Min. 6 characters"
                    placeholderTextColor="rgba(114,119,132,0.5)"
                    value={password}
                    onChangeText={setPassword}
                    autoComplete="password"
                    returnKeyType="go"
                    editable={!isLoading}
                    onSubmitEditing={handleSignUp}
                    passwordRules={"minlength: 6;"}
                  />
                </View>
              </View>

              {/* checkbox */}
              <Pressable
                onPress={() => {
                  setTermsAccepted((prev) => !prev);
                }}
                disabled={isLoading}
                className="flex-row items-start gap-3 py-2"
                hitSlop={{ top: 15, left: 15, right: 15, bottom: 15 }}
              >
                <View
                  className="mt-0.5 h-5 w-5 items-center justify-center rounded"
                  style={{
                    backgroundColor: termsAccepted ? Colors.primary : "#f2f3fc",
                  }}
                >
                  {termsAccepted && (
                    <MaterialIcons name="check" size={16} color="white" />
                  )}
                </View>
                <Text className={`text-on-surface-variant flex-1 ${smallText}`}>
                  I agree to the{" "}
                  <Text
                    className="text-primary font-medium"
                    suppressHighlighting
                  >
                    Terms of Service
                  </Text>{" "}
                  and{" "}
                  <Text
                    className="text-primary font-medium"
                    suppressHighlighting
                  >
                    Privacy Policy
                  </Text>
                  .
                </Text>
              </Pressable>

              {/* Sign Up button */}
              <Pressable
                onPress={handleSignUp}
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
                      <Text
                        className={`font-headline text-on-primary ${smallText} font-bold`}
                      >
                        Create Account
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
            <Pressable
              className="mt-3 w-fit items-center pt-6"
              onPress={() => router.replace("/login")}
              hitSlop={{ right: 5, bottom: 5 }}
            >
              <Text
                className={`text-on-surface-variant ${smallText}`}
                style={{ fontFamily: "Inter_400Regular" }}
              >
                {"Already have an account? "}
                <Text
                  className={`text-primary ${smallText}`}
                  style={{ fontFamily: "Inter_600SemiBold" }}
                  suppressHighlighting
                >
                  Sign in
                </Text>
              </Text>
            </Pressable>
          </View>
        </View>
      </View>
    </ScrollView>
  );
}
