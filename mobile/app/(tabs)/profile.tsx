import { MaterialIcons } from "@expo/vector-icons";

import { Pressable, ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { AnimatedPressable } from "@/components/animated-pressable";
import { Header } from "@/components/header";
import { Colors, Shadows } from "@/constants/colors";

export default function ProfilePage() {
  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: Colors.surface }}
      edges={["top"]}
    >
      <Header />
      <ScrollView
        className="flex-1"
        contentContainerClassName="px-6 py-8 pb-28"
        showsVerticalScrollIndicator={false}
      >
        {/* User Info */}
        <View className="mb-10">
          <Text
            className="text-on-surface mb-1 text-3xl tracking-tight"
            style={{ fontFamily: "Manrope_800ExtraBold" }}
          >
            Alex Harrington
          </Text>
          <Text
            className="text-on-surface-variant mb-6 text-base"
            style={{ fontFamily: "Inter_500Medium" }}
          >
            alex.harrington@research-pro.io
          </Text>

          {/* Total Earnings */}
          <View
            className="bg-surface-container-lowest border-secondary self-start rounded-xl border-l-4 px-6 py-4"
            style={Shadows.editorial}
          >
            <Text
              className="text-on-surface-variant mb-1 text-[11px] tracking-widest uppercase"
              style={{ fontFamily: "Inter_700Bold" }}
            >
              Total Earnings
            </Text>
            <Text
              className="text-primary text-2xl"
              style={{ fontFamily: "Manrope_700Bold" }}
            >
              $4,852.50
            </Text>
          </View>
        </View>

        {/* Payment Methods */}
        <View
          className="bg-surface-container-lowest border-primary mb-6 rounded-xl border-l-4 p-6"
          style={Shadows.editorial}
        >
          <View className="mb-4 flex-row items-center gap-3">
            <MaterialIcons name="payments" size={24} color={Colors.primary} />
            <Text
              className="text-on-surface text-xl"
              style={{ fontFamily: "Manrope_700Bold" }}
            >
              Payment Methods
            </Text>
          </View>
          <View className="bg-surface-container-low flex-row items-center gap-3 rounded-lg p-4">
            <MaterialIcons
              name="credit-card"
              size={24}
              color={Colors.onSurfaceVariant}
            />
            <View>
              <Text
                className="text-on-surface text-sm"
                style={{ fontFamily: "Inter_600SemiBold" }}
              >
                Visa •••• 4289
              </Text>
              <Text
                className="text-on-surface-variant text-xs"
                style={{ fontFamily: "Inter_400Regular" }}
              >
                Expires 08/26
              </Text>
            </View>
          </View>
        </View>

        {/* Settings Section */}
        <View
          className="bg-surface-container-lowest mb-6 rounded-xl p-6"
          style={Shadows.small}
        >
          <View className="mb-4 flex-row items-center gap-3">
            <MaterialIcons
              name="settings"
              size={24}
              color={Colors.onSurfaceVariant}
            />
            <Text
              className="text-on-surface text-xl"
              style={{ fontFamily: "Manrope_700Bold" }}
            >
              Settings
            </Text>
          </View>
          {["Notifications", "Privacy", "Help & Support"].map((item) => (
            <Pressable
              key={item}
              className="border-surface-container-low flex-row items-center justify-between border-b py-4 active:opacity-60"
            >
              <Text
                className="text-on-surface text-sm"
                style={{ fontFamily: "Inter_500Medium" }}
              >
                {item}
              </Text>
              <MaterialIcons
                name="chevron-right"
                size={20}
                color={Colors.onSurfaceVariant}
              />
            </Pressable>
          ))}
        </View>

        {/* Sign Out */}
        <AnimatedPressable className="bg-error-container/20 active:bg-error-container/40 flex-row items-center justify-center gap-2 rounded-xl py-4">
          <MaterialIcons name="logout" size={20} color={Colors.error} />
          <Text
            className="text-error text-sm"
            style={{ fontFamily: "Inter_700Bold" }}
          >
            Sign Out
          </Text>
        </AnimatedPressable>
      </ScrollView>
    </SafeAreaView>
  );
}
