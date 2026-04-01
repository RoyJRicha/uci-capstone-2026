import { MaterialIcons } from "@expo/vector-icons";

import { Text, View } from "react-native";

import { Colors, Shadows } from "@/constants/colors";

interface SubmissionItemProps {
  name: string;
  date: string;
  status: string;
  statusColor?: string;
  amount: string;
}

export function SubmissionItem({
  name,
  date,
  status,
  statusColor,
  amount,
}: SubmissionItemProps) {
  const color = statusColor ?? Colors.primary;

  return (
    <View
      className="bg-surface-container-lowest border-primary rounded-xl border-l-4 p-5"
      style={Shadows.small}
    >
      <View className="mb-2 flex-row items-start justify-between">
        <Text
          className="text-on-surface flex-1 text-lg tracking-tight"
          style={{ fontFamily: "Manrope_700Bold" }}
        >
          {name}
        </Text>
        <Text
          className="text-on-surface-variant text-xs"
          style={{ fontFamily: "Inter_500Medium" }}
        >
          {date}
        </Text>
      </View>
      <View className="flex-row items-center justify-between">
        <View className="flex-row items-center gap-1.5">
          <MaterialIcons name="pending" size={16} color={color} />
          <Text
            className="text-xs"
            style={{ fontFamily: "Inter_700Bold", color }}
          >
            {status}
          </Text>
        </View>
        <Text
          className="text-on-surface text-xl"
          style={{ fontFamily: "Manrope_700Bold" }}
        >
          {amount}
        </Text>
      </View>
    </View>
  );
}
