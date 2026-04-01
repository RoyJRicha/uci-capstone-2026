import { MaterialIcons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";

import { Text } from "react-native";

import { AnimatedPressable } from "@/components/animated-pressable";
import { Shadows } from "@/constants/colors";

interface GradientButtonProps {
  label: string;
  icon?: keyof typeof MaterialIcons.glyphMap;
  onPress?: () => void;
  className?: string;
}

export function GradientButton({
  label,
  icon,
  onPress,
  className,
}: GradientButtonProps) {
  return (
    <AnimatedPressable
      onPress={onPress}
      className={className}
      style={Shadows.editorial}
    >
      <LinearGradient
        colors={["#00458f", "#005cc0"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={{ borderRadius: 9999 }}
        className="flex-row items-center justify-center gap-2 px-6 py-3"
      >
        <Text
          className="text-sm text-white"
          style={{ fontFamily: "Inter_700Bold" }}
        >
          {label}
        </Text>
        {icon && <MaterialIcons name={icon} size={18} color="#ffffff" />}
      </LinearGradient>
    </AnimatedPressable>
  );
}
