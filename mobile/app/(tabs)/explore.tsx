import { CameraType, CameraView, useCameraPermissions } from "expo-camera";

import { Button, StyleSheet, Text, TouchableOpacity, View } from "react-native";

import { useState } from "react";

import ReceiptScanner from "@/components/receipt-scanner";

export default function TabTwoScreen() {
  return <ReceiptScanner />;
}
