import { MaterialIcons } from "@expo/vector-icons";

import { ScrollView, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { CaptureOption } from "@/components/capture-option";
import { GuidelineItem } from "@/components/guideline-item";
import { Header } from "@/components/header";
import { Colors } from "@/constants/colors";

export default function CapturePage() {
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
          <Text
            className="text-on-surface mb-2 text-3xl tracking-tight"
            style={{ fontFamily: "Manrope_800ExtraBold" }}
          >
            Capture Data
          </Text>
          <Text
            className="text-on-surface-variant text-base"
            style={{ fontFamily: "Inter_400Regular" }}
          >
            Submit high-quality visual data for field analysis.
          </Text>
        </View>

        {/* Store Input */}
        <View className="bg-surface-container-low mb-8 rounded-xl p-5">
          <Text
            className="text-on-surface-variant mb-3 text-sm"
            style={{ fontFamily: "Inter_600SemiBold" }}
          >
            Store Name/ID
          </Text>
          <View className="bg-surface-container-lowest border-outline-variant/15 flex-row items-center rounded-lg border px-4 py-3.5">
            <MaterialIcons
              name="store"
              size={20}
              color={Colors.outline}
              style={{ marginRight: 10 }}
            />
            <TextInput
              className="text-on-surface flex-1 text-base"
              placeholder="Enter store name or scan ID..."
              placeholderTextColor={Colors.outlineVariant}
              style={{ fontFamily: "Inter_400Regular" }}
            />
          </View>
        </View>

        {/* Capture Options */}
        <View className="mb-10 flex-col gap-4">
          <CaptureOption
            icon="inventory-2"
            title="Shelf Audit"
            subtitle="Capture product placement"
            variant="filled"
          />
          <CaptureOption
            icon="receipt-long"
            title="Receipt"
            subtitle="Verify sales records"
            variant="outlined"
          />
        </View>

        {/* Quality Guidelines */}
        <View className="mb-10">
          <View className="mb-5 flex-row items-center gap-3">
            <View className="bg-secondary h-6 w-1 rounded-full" />
            <Text
              className="text-on-surface text-xl"
              style={{ fontFamily: "Manrope_700Bold" }}
            >
              Quality Guidelines
            </Text>
          </View>
          <View className="gap-3">
            <GuidelineItem
              icon="light-mode"
              title="Ensure good lighting"
              description="Avoid glares and shadows on surfaces."
            />
            <GuidelineItem
              icon="center-focus-strong"
              title="Keep images in focus"
              description="Ensure text and labels are clearly readable."
            />
            <GuidelineItem
              icon="crop-free"
              title="Capture full shelves"
              description="Include as much of the display as possible."
            />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
