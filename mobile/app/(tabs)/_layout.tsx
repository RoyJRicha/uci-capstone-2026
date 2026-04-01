import { MaterialIcons } from "@expo/vector-icons";
import { Tabs } from "expo-router";

import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Colors } from "@/constants/colors";

type TabIconName = "assignment" | "receipt-long" | "history" | "person";

function TabIcon({
  name,
  color,
  size,
}: {
  name: TabIconName;
  color: string;
  size: number;
}) {
  return <MaterialIcons name={name} size={size} color={color} />;
}

export default function TabsLayout() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = 56 + insets.bottom;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: Colors.primary,
        tabBarInactiveTintColor: Colors.onSurfaceVariant,
        tabBarLabelStyle: {
          fontFamily: "Inter_600SemiBold",
          fontSize: 9,
          textTransform: "uppercase",
          letterSpacing: 0.5,
        },
        tabBarStyle: {
          borderTopWidth: 0,
          paddingTop: 4,
          height: tabBarHeight,
          shadowColor: "#191c22",
          shadowOffset: { width: 0, height: -10 },
          shadowOpacity: 0.06,
          shadowRadius: 30,
          elevation: 8,
          borderTopLeftRadius: 16,
          borderTopRightRadius: 16,
          position: "absolute",
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color, size }) => (
            <TabIcon name="assignment" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="capture"
        options={{
          title: "Capture",
          tabBarIcon: ({ color, size }) => (
            <TabIcon name="receipt-long" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: "History",
          tabBarIcon: ({ color, size }) => (
            <TabIcon name="history" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: "Profile",
          tabBarIcon: ({ color, size }) => (
            <TabIcon name="person" color={color} size={size} />
          ),
        }}
      />
    </Tabs>
  );
}
