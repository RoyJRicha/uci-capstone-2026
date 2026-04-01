import { MaterialIcons } from "@expo/vector-icons";

import { ScrollView, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Header } from "@/components/header";
import { SubmissionItem } from "@/components/submission-item";
import { Colors, Shadows } from "@/constants/colors";

export default function HistoryPage() {
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
        {/* Page Title */}
        <View className="mb-8">
          <View className="bg-secondary-container mb-3 self-start rounded-full px-3 py-1">
            <Text
              className="text-secondary text-[10px] tracking-widest uppercase"
              style={{ fontFamily: "Inter_600SemiBold" }}
            >
              Activity Log
            </Text>
          </View>
          <Text
            className="text-on-surface text-3xl tracking-tight"
            style={{ fontFamily: "Manrope_800ExtraBold" }}
          >
            Submission <Text className="text-primary bold">History</Text>
          </Text>
        </View>

        {/* Lifetime Earnings Card */}
        <View
          className="bg-primary-fixed mb-10 rounded-xl p-6"
          style={Shadows.editorial}
        >
          <View className="mb-4 flex-row items-start justify-between">
            <MaterialIcons name="payments" size={30} color={Colors.primary} />
            <Text
              className="text-primary text-xs tracking-tight uppercase"
              style={{ fontFamily: "Inter_700Bold" }}
            >
              Lifetime Earnings
            </Text>
          </View>
          <Text
            className="text-on-primary-fixed text-4xl tracking-tighter"
            style={{ fontFamily: "Manrope_800ExtraBold" }}
          >
            $1,240.50
          </Text>
        </View>

        {/* Recent Submissions */}
        <Text
          className="text-on-surface-variant mb-5 ml-1 text-xs tracking-widest uppercase"
          style={{ fontFamily: "Inter_700Bold" }}
        >
          Recent Submissions
        </Text>

        <View className="mb-10 gap-4">
          <SubmissionItem
            name="Nike Flagship Store"
            date="Oct 22, 2023 • 09:15 AM"
            status="Pending Review"
            amount="$18.50"
          />
          <SubmissionItem
            name="Target Supercenter"
            date="Oct 20, 2023 • 02:30 PM"
            status="Approved"
            statusColor={Colors.secondary}
            amount="$12.00"
          />
          <SubmissionItem
            name="Trader Joe's"
            date="Oct 18, 2023 • 11:45 AM"
            status="Approved"
            statusColor={Colors.secondary}
            amount="$15.00"
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
