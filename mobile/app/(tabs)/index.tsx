import { MaterialIcons } from "@expo/vector-icons";

import { Pressable, ScrollView, Text, View } from "react-native";
import {
  SafeAreaView,
  useSafeAreaInsets,
} from "react-native-safe-area-context";

import { AssignmentCard } from "@/components/assignment-card";
import { GradientButton } from "@/components/gradient-button";
import { Header } from "@/components/header";
import { StatCard } from "@/components/stat-card";
import { Colors, Shadows } from "@/constants/colors";

export default function HomePage() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = 8 + 8 + 56 + insets.bottom;

  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: Colors.surface }}
      edges={["top"]}
    >
      <Header />
      <ScrollView
        className="flex-1"
        contentContainerStyle={{
          paddingHorizontal: 24,
          paddingTop: 32,
          paddingBottom: tabBarHeight + 16,
        }}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero Section */}
        <View className="mb-10">
          <Text
            className="text-secondary mb-2 text-xs tracking-widest uppercase"
            style={{ fontFamily: "Inter_600SemiBold" }}
          >
            Available Missions
          </Text>
          <Text
            className="text-on-surface mb-1 text-3xl leading-tight tracking-tight"
            style={{ fontFamily: "Manrope_800ExtraBold" }}
          >
            Analyze the world{"\n"}
            <Text className="text-primary">around you.</Text>
          </Text>
          <Text
            className="text-on-surface-variant mt-3 text-base"
            style={{ fontFamily: "Inter_400Regular" }}
          >
            Your data-driven contributions shape the future of local commerce.
          </Text>
        </View>

        <View className="mb-8">
          <StatCard value="84%" label="Market Reach" />
        </View>

        {/* Nearby Opportunities */}
        <View
          className="bg-surface-container-low mb-4 overflow-hidden rounded-xl p-6"
          style={Shadows.editorial}
        >
          <Text
            className="text-on-surface mb-2 text-xl"
            style={{ fontFamily: "Manrope_700Bold" }}
          >
            Nearby Opportunities
          </Text>
          <Text
            className="text-on-surface-variant mb-5"
            style={{ fontFamily: "Inter_400Regular" }}
          >
            There are 12 high-priority audits within 2 miles of your current
            location.
          </Text>
          <GradientButton label="View Map" icon="map" />
        </View>

        {/* Rewards Card */}
        <View
          className="bg-primary mb-10 rounded-xl p-6"
          style={Shadows.editorial}
        >
          <MaterialIcons
            name="account-balance-wallet"
            size={36}
            color="#ffffff"
          />
          <View className="mt-4">
            <Text
              className="text-primary-fixed text-xs tracking-wider uppercase opacity-80"
              style={{ fontFamily: "Inter_600SemiBold" }}
            >
              Pending Rewards
            </Text>
            <Text
              className="text-3xl text-white"
              style={{ fontFamily: "Manrope_700Bold" }}
            >
              $142.50
            </Text>
          </View>
        </View>

        {/* Filter Chips */}
        <View className="mb-6 flex-row items-center justify-between">
          <Text
            className="text-on-surface text-xl"
            style={{ fontFamily: "Manrope_700Bold" }}
          >
            Requested Assignments
          </Text>
        </View>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          className="mb-6"
          contentContainerClassName="gap-2"
        >
          <View className="bg-surface-container-highest rounded-full px-4 py-2">
            <Text
              className="text-on-primary-fixed-variant text-sm"
              style={{ fontFamily: "Inter_700Bold" }}
            >
              All
            </Text>
          </View>
          <View className="rounded-full px-4 py-2">
            <Text
              className="text-on-surface-variant text-sm"
              style={{ fontFamily: "Inter_500Medium" }}
            >
              Retail
            </Text>
          </View>
          <View className="rounded-full px-4 py-2">
            <Text
              className="text-on-surface-variant text-sm"
              style={{ fontFamily: "Inter_500Medium" }}
            >
              Dining
            </Text>
          </View>
        </ScrollView>

        {/* Assignment Card */}
        <AssignmentCard
          name="Whole Foods Market"
          address="1550 N Kingsbury St, Chicago, IL"
          duration="15-min audit"
          distance="0.4 miles away"
          reward="$12.00"
          tag="Recommended"
        />
      </ScrollView>

      {/* FAB */}
      <Pressable
        className="bg-primary absolute right-6 bottom-24 z-40 h-14 w-14 items-center justify-center rounded-full active:scale-90"
        style={{
          bottom: tabBarHeight + 16, // ← sits just above the tab bar
          shadowColor: "#00458f",
          shadowOffset: { width: 0, height: 8 },
          shadowOpacity: 0.3,
          shadowRadius: 16,
          elevation: 8,
        }}
      >
        <MaterialIcons name="add" size={28} color="#ffffff" />
      </Pressable>
    </SafeAreaView>
  );
}
