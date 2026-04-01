import { MaterialIcons } from "@expo/vector-icons";

import { Text, View } from "react-native";

import { Colors } from "@/constants/colors";

interface GuidelineItemProps {
  icon: keyof typeof MaterialIcons.glyphMap;
  title: string;
  description: string;
}

export function GuidelineItem({
  icon,
  title,
  description,
}: GuidelineItemProps) {
  return (
    <View className="bg-surface-container-lowest border-secondary flex-row items-center gap-4 rounded-xl border-l-4 p-4">
      <View className="bg-secondary-container/30 rounded-lg p-2.5">
        <MaterialIcons name={icon} size={22} color={Colors.secondary} />
      </View>
      <View className="flex-1">
        <Text
          className="text-on-surface text-sm"
          style={{ fontFamily: "Inter_600SemiBold" }}
        >
          {title}
        </Text>
        <Text
          className="text-on-surface-variant mt-0.5 text-xs"
          style={{ fontFamily: "Inter_400Regular" }}
        >
          {description}
        </Text>
      </View>
    </View>
  );
}
