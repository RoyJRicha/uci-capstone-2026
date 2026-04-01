import { MaterialIcons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";

import { Text, View } from "react-native";

import { AnimatedPressable } from "@/components/animated-pressable";
import { Colors, Shadows } from "@/constants/colors";

interface CaptureOptionProps {
  icon: keyof typeof MaterialIcons.glyphMap;
  title: string;
  subtitle: string;
  variant: "filled" | "outlined";
  onPress?: () => void;
}

export function CaptureOption({
  icon,
  title,
  subtitle,
  variant,
  onPress,
}: CaptureOptionProps) {
  if (variant === "filled") {
    return (
      <AnimatedPressable onPress={onPress} style={Shadows.editorial}>
        <LinearGradient
          colors={["#00458f", "#005cbb"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          className="items-center rounded-xl p-6"
        >
          <View className="mb-4 rounded-full bg-white/10 p-4">
            <MaterialIcons name={icon} size={36} color="#ffffff" />
          </View>
          <Text
            className="mb-1 text-lg text-white"
            style={{ fontFamily: "Manrope_700Bold" }}
          >
            {title}
          </Text>
          <Text
            className="text-center text-sm text-white/80"
            style={{ fontFamily: "Inter_500Medium" }}
          >
            {subtitle}
          </Text>
        </LinearGradient>
      </AnimatedPressable>
    );
  }

  return (
    <AnimatedPressable
      onPress={onPress}
      className="bg-surface-container-lowest border-outline-variant/15 flex-1 items-center rounded-xl border p-6"
      style={Shadows.small}
    >
      <View className="bg-primary-fixed mb-4 rounded-full p-4">
        <MaterialIcons name={icon} size={36} color={Colors.primary} />
      </View>
      <Text
        className="text-on-surface mb-1 text-lg"
        style={{ fontFamily: "Manrope_700Bold" }}
      >
        {title}
      </Text>
      <Text
        className="text-on-surface-variant text-center text-sm"
        style={{ fontFamily: "Inter_500Medium" }}
      >
        {subtitle}
      </Text>
    </AnimatedPressable>
  );
}
