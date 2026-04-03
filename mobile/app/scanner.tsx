import { MaterialIcons } from "@expo/vector-icons";
import { CameraView, useCameraPermissions } from "expo-camera";
import { router, useLocalSearchParams } from "expo-router";

import { ActivityIndicator } from "react-native";
import { Image, Modal, Text, View } from "react-native";
import Toast from "react-native-toast-message";

import { useEffect, useRef, useState } from "react";

import { useIsFocused } from "@react-navigation/native";

import { AnimatedPressable } from "@/components/animated-pressable";
import { useDetector } from "@/hooks/use-detector";
import { useDeviceStability } from "@/hooks/use-device-stability";
import { useImageUpload } from "@/hooks/use-image-upload";
import { ensurePortrait } from "@/lib/ensure-portrait";
import { DetectorResult } from "@/services/detector-service";

type Status = "moving" | DetectorResult;

const statusMessages: Record<
  Status,
  {
    receipt: { color: string; message: string };
    shelf: { color: string; message: string };
  }
> = {
  moving: {
    receipt: { color: "#facc15", message: "📱  Hold camera steady" },
    shelf: { color: "#facc15", message: "📱  Hold camera steady" },
  },
  notFound: {
    receipt: { color: "#facc15", message: "🔍  Point camera at receipt" },
    shelf: { color: "#facc15", message: "🔍  Point camera at shelf" },
  },
  tooClose: {
    receipt: { color: "#f87171", message: "⬇️  Move further away" },
    shelf: { color: "#f87171", message: "⬇️  Move further away" },
  },
  tooFar: {
    receipt: { color: "#facc15", message: "⬆️  Move closer to receipt" },
    shelf: { color: "#facc15", message: "⬆️  Move closer to shelf" },
  },
  good: {
    receipt: { color: "#4ade80", message: "✅  Ready for capture!" },
    shelf: { color: "#4ade80", message: "✅  Ready for capture!" },
  },
};

export default function Scanner() {
  const { type } = useLocalSearchParams<{
    type: "shelf" | "receipt";
  }>();
  const isFocused = useIsFocused();
  const [permission, requestPermission] = useCameraPermissions();
  const detector = useDetector();
  const isStable = useDeviceStability();
  const imageUpload = useImageUpload();

  const cameraRef = useRef<CameraView>(null);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [capturedImageURI, setCapturedImageURI] = useState<string | null>(null);

  const status: keyof typeof statusMessages = !isStable
    ? "moving"
    : detector.result;

  // camera permissions
  useEffect(() => {
    if (!permission || !permission.granted) {
      requestPermission();
    }
  }, [permission, requestPermission]);

  // passive image analysis
  useEffect(() => {
    if (
      !detector.isReady ||
      detector.isLoading ||
      !isStable ||
      !cameraRef.current ||
      !isCameraReady ||
      capturedImageURI
    ) {
      return;
    }

    const timerId = setTimeout(() => {
      cameraRef
        .current!.takePictureAsync({
          base64: true,
          exif: true,
          shutterSound: false,
          skipProcessing: true,
        })
        .then((picture) => ensurePortrait(picture))
        .then((corrected) => {
          if (type === "shelf") {
            detector.analyzeShelf(corrected.base64!);
          } else {
            detector.analyzeReceipt(corrected.base64!);
          }
        });
    }, 50); // delay every N milliseconds for performance

    return () => {
      clearTimeout(timerId);
    };
  }, [detector, isStable, isCameraReady, capturedImageURI, type]);

  async function capture() {
    if (!cameraRef.current || !isCameraReady || capturedImageURI) {
      return;
    }

    await cameraRef
      .current!.takePictureAsync({
        exif: true,
        shutterSound: false,
      })
      .then((picture) => ensurePortrait(picture))
      .then((corrected) => {
        setCapturedImageURI(corrected.uri);
      });
  }

  async function submit() {
    if (imageUpload.loading) {
      return;
    }

    const { success, data } = await imageUpload.uploadImage(
      capturedImageURI!,
      type,
    );

    if (!success) {
      Toast.show({
        type: "error",
        text1: "Upload failed. Please try again later.",
        text1Style: { fontSize: 13 },
      });
      console.error("image upload error:", data);
    } else {
      Toast.show({
        type: "success",
        text1: "Upload successful!",
        text1Style: { fontSize: 13 },
      });
      router.navigate("/history");
    }
  }

  if (!permission || !permission.granted || !isFocused) {
    return null;
  }

  return (
    <View className="flex-1">
      <CameraView
        ref={cameraRef}
        animateShutter={false}
        onCameraReady={() => setIsCameraReady(true)}
        pictureSize="640x480"
        ratio="4:3"
        style={{ flex: 1 }}
      />
      <View className="absolute top-11 ml-1 flex-row items-center gap-2.5 rounded-full bg-[#00000080] pt-1.5 pr-5 pb-2 pl-2">
        <MaterialIcons
          onPress={() => router.back()}
          name="chevron-left"
          size={32}
          color="white"
          className="pt-0.5"
        />
        <Text
          className="text-lg text-white"
          style={{ fontFamily: "Manrope_800ExtraBold" }}
        >
          Scan {type === "shelf" ? "Shelf" : "Receipt"}
        </Text>
      </View>
      <Text
        className="absolute bottom-[26%] w-fit self-center rounded-full border-[1.5] bg-[#00000080] pt-1 pr-4 pb-1.5 pl-3.5 text-white"
        style={{
          fontFamily: "Manrope_700Bold",
          borderColor: statusMessages[status][type].color,
        }}
      >
        {statusMessages[status][type].message}
      </Text>
      <AnimatedPressable
        onPress={capture}
        className="absolute bottom-[14.5%] h-20 w-20 self-center rounded-full border-5 bg-white"
      />
      {/* send photo pop-up */}
      <Modal
        visible={!!capturedImageURI}
        transparent
        animationType="slide"
        onRequestClose={() => setCapturedImageURI(null)}
      >
        <View className="flex-1 justify-end bg-black/90">
          <View className="rounded-t-2xl bg-white p-6">
            {/* Preview thumbnail */}
            <Image
              source={{ uri: capturedImageURI! }}
              resizeMode="contain"
              className="mt-1.5 mb-4 aspect-3/4 h-[45vh] self-center rounded-2xl"
            />
            <Text
              className="text-on-surface mb-1 text-xl"
              style={{ fontFamily: "Manrope_800ExtraBold" }}
            >
              Use this photo?
            </Text>
            <Text
              className="text-on-surface-variant mb-5 text-sm"
              style={{ fontFamily: "Inter_400Regular" }}
            >
              Make sure that prices are clear and visible.
            </Text>
            <View className="gap-3">
              <AnimatedPressable
                onPress={submit}
                className="bg-primary-container items-center rounded-full py-3"
              >
                <View className="flex-row items-center gap-2.5">
                  <Text
                    className={
                      imageUpload.loading ? "text-white/70" : "text-white"
                    }
                    style={{ fontFamily: "Inter_600SemiBold" }}
                  >
                    Send Photo
                  </Text>
                  {imageUpload.loading ? (
                    <ActivityIndicator size="small" className="text-white/70" />
                  ) : null}
                </View>
              </AnimatedPressable>
              <AnimatedPressable
                onPress={() =>
                  !imageUpload.loading && setCapturedImageURI(null)
                }
                className="items-center rounded-full bg-gray-100 py-3 shadow-lg"
              >
                <Text
                  className="text-on-surface"
                  style={{ fontFamily: "Inter_600SemiBold" }}
                >
                  Retake
                </Text>
              </AnimatedPressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}
