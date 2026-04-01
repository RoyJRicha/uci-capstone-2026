import { Text, View } from "react-native";

import { Shadows } from "@/constants/colors";

interface StatCardProps {
  value: string;
  label: string;
}

export function StatCard({ value, label }: StatCardProps) {
  return (
    <View
      className="bg-surface-container-low min-w-35 items-center justify-center rounded-xl p-6"
      style={Shadows.editorial}
    >
      <Text
        className="text-primary text-4xl tracking-tight"
        style={{ fontFamily: "Manrope_800ExtraBold" }}
      >
        {value}
      </Text>
      <Text
        className="text-on-surface-variant mt-1 text-[10px] tracking-widest uppercase"
        style={{ fontFamily: "Inter_700Bold" }}
      >
        {label}
      </Text>
    </View>
  );
}
