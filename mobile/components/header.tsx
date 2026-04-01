import { MaterialIcons } from "@expo/vector-icons";

import { Pressable, Text, View } from "react-native";

import { Colors } from "@/constants/colors";

interface HeaderProps {
  title?: string;
}

export function Header({ title = "Wayvia Insider" }: HeaderProps) {
  return (
    <View className="bg-surface border-outline-variant/10 flex-row items-center justify-between border-b px-6 py-4">
      <View className="flex-row items-center gap-2">
        <MaterialIcons name="analytics" size={24} color={Colors.primary} />
        <Text
          className="text-primary text-xl tracking-tight"
          style={{ fontFamily: "Manrope_800ExtraBold" }}
        >
          {title}
        </Text>
      </View>
      <Pressable className="p-2 active:opacity-60">
        <MaterialIcons
          name="notifications"
          size={24}
          color={Colors.onSurfaceVariant}
        />
      </Pressable>
    </View>
  );
}
