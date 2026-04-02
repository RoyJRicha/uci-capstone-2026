import { MaterialIcons } from "@expo/vector-icons";
import { CameraView, useCameraPermissions } from "expo-camera";
import { router, useLocalSearchParams } from "expo-router";

import { Image, Modal, Text, View } from "react-native";

import { useEffect, useRef, useState } from "react";

import { useIsFocused } from "@react-navigation/native";

import { AnimatedPressable } from "@/components/animated-pressable";
import { useDetector } from "@/hooks/use-detector";
import { useDeviceStability } from "@/hooks/use-device-stability";
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

  const cameraRef = useRef<CameraView>(null);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [capturedBase64, setCapturedBase64] = useState<string | null>(null);

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
      capturedBase64
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
          // add analyzeShelf maybe (but mostly leave it to human input for now)
          detector.analyzeReceipt(corrected.base64!);
        });
    }, 100);

    return () => {
      clearTimeout(timerId);
    };
  }, [detector, isStable, isCameraReady, capturedBase64]);

  async function capture() {
    if (!cameraRef.current || !isCameraReady || capturedBase64) {
      return;
    }

    await cameraRef
      .current!.takePictureAsync({
        base64: true,
        exif: true,
        shutterSound: false,
      })
      .then((picture) => ensurePortrait(picture))
      .then((corrected) => {
        setCapturedBase64(corrected.base64!);
      });
  }

  async function submit() {
    // mess with capturedbase64 and type
    router.navigate("/history");
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
        visible={!!capturedBase64}
        transparent
        animationType="slide"
        onRequestClose={() => setCapturedBase64(null)}
      >
        <View className="flex-1 justify-end bg-black/90">
          <View className="rounded-t-2xl bg-white p-6">
            {/* Preview thumbnail */}
            <Image
              source={{ uri: "data:image/jpeg;base64," + capturedBase64 }}
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
                <Text
                  className="text-white"
                  style={{ fontFamily: "Inter_600SemiBold" }}
                >
                  Send Photo
                </Text>
              </AnimatedPressable>
              <AnimatedPressable
                onPress={() => setCapturedBase64(null)}
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
