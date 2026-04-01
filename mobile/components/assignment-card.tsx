import { MaterialIcons } from "@expo/vector-icons";
import { useRouter } from "expo-router";

import { Text, View } from "react-native";

import { GradientButton } from "@/components/gradient-button";
import { Colors, Shadows } from "@/constants/colors";

interface AssignmentCardProps {
  name: string;
  address: string;
  duration: string;
  distance: string;
  reward: string;
  tag?: string;
}

export function AssignmentCard({
  name,
  address,
  duration,
  distance,
  reward,
  tag,
}: AssignmentCardProps) {
  const router = useRouter();

  return (
    <View
      className="bg-surface-container-lowest border-secondary rounded-xl border-l-4 p-5"
      style={Shadows.editorial}
    >
      <View className="mb-4 flex-row items-start gap-4">
        <View className="bg-surface-container-low h-14 w-14 items-center justify-center rounded-xl">
          <MaterialIcons name="store" size={28} color={Colors.secondary} />
        </View>
        <View className="flex-1">
          <View className="mb-1 flex-row flex-wrap items-center gap-2">
            <Text
              className="text-on-surface text-lg tracking-tight"
              style={{ fontFamily: "Manrope_700Bold" }}
            >
              {name}
            </Text>
            {tag && (
              <View className="bg-tertiary-container rounded-full px-2 py-0.5">
                <Text
                  className="text-on-tertiary-container text-[10px] uppercase"
                  style={{ fontFamily: "Inter_700Bold" }}
                >
                  {tag}
                </Text>
              </View>
            )}
          </View>
          <View className="mb-3 flex-row items-center gap-1">
            <MaterialIcons
              name="location-on"
              size={14}
              color={Colors.onSurfaceVariant}
            />
            <Text
              className="text-on-surface-variant text-sm"
              style={{ fontFamily: "Inter_400Regular" }}
            >
              {address}
            </Text>
          </View>
          <View className="flex-row gap-4">
            <View className="flex-row items-center gap-1.5">
              <MaterialIcons
                name="schedule"
                size={14}
                color={Colors.onSurfaceVariant}
              />
              <Text
                className="text-on-surface-variant text-xs"
                style={{ fontFamily: "Inter_700Bold" }}
              >
                {duration}
              </Text>
            </View>
            <View className="flex-row items-center gap-1.5">
              <MaterialIcons
                name="straighten"
                size={14}
                color={Colors.onSurfaceVariant}
              />
              <Text
                className="text-on-surface-variant text-xs"
                style={{ fontFamily: "Inter_700Bold" }}
              >
                {distance}
              </Text>
            </View>
          </View>
        </View>
      </View>

      <View className="border-surface-container-low flex-row items-center justify-between border-t pt-4">
        <View>
          <Text
            className="text-on-surface-variant text-[10px] tracking-wider uppercase opacity-60"
            style={{ fontFamily: "Inter_700Bold" }}
          >
            Reward
          </Text>
          <Text
            className="text-primary text-2xl tracking-tight"
            style={{ fontFamily: "Manrope_800ExtraBold" }}
          >
            {reward}
          </Text>
        </View>
        <GradientButton
          label="Accept"
          onPress={() => router.push("/capture")}
        />
      </View>
    </View>
  );
}
