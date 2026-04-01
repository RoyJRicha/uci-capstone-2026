import { MaterialIcons } from "@expo/vector-icons";

import { ScrollView, Text, View } from "react-native";
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
  const tabBarHeight = 8 + 56 + insets.bottom;

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
          paddingTop: 24,
          paddingBottom: tabBarHeight + 20,
        }}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero Section */}
        <View className="mb-10">
          <Text
            className="text-on-surface mb-1 text-3xl leading-tight tracking-tight"
            style={{ fontFamily: "Manrope_800ExtraBold" }}
          >
            Your local store,{"\n"}
            <Text className="text-primary">your global impact.</Text>
          </Text>
          <Text
            className="text-on-surface-variant mt-3 text-base"
            style={{ fontFamily: "Inter_400Regular" }}
          >
            Your contributions empower the world’s biggest brands with local,
            human insights.
          </Text>
        </View>

        <View className="mb-8">
          <StatCard value="2" label="Active Assignments" />
        </View>

        {/* Nearby Opportunities */}
        <View
          className="bg-surface-container-low mb-8 overflow-hidden rounded-xl p-6"
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
              Recommended
            </Text>
          </View>
        </ScrollView>

        {/* Assignment Cards */}
        <View className="flex-col gap-8">
          <AssignmentCard
            name="Whole Foods Market"
            address="1550 N Kingsbury St, Chicago, IL"
            duration="15 min"
            distance="0.4 mi"
            reward="$12.00"
            tag="Recommended"
          />
          <AssignmentCard
            name="Costco Wholesale"
            address="1430 S Ashland Ave, Chicago, IL 60608"
            duration="31 min"
            distance="4.4 mi"
            reward="$14.00"
            tag="Recommended"
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
