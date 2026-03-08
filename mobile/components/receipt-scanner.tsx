import {
  CameraOrientation,
  CameraView,
  useCameraPermissions,
} from "expo-camera";

import { Image, StyleSheet, Text, View } from "react-native";

import { useEffect, useRef, useState } from "react";

import { useIsFocused } from "@react-navigation/native";

import { useDetector } from "@/hooks/use-detector";
import { useDeviceStability } from "@/hooks/use-device-stability";
import { useJerkCorrection } from "@/hooks/use-jerk-correction";
import { DetectorResult } from "@/services/detector-service";

type Status = "moving" | DetectorResult;

const statusMessages: Record<Status, { color: string; message: string }> = {
  moving: { color: "#facc15", message: "📱 Hold camera steady" },
  notFound: { color: "#ffffff", message: "🔍 Point camera at receipt" },
  tooClose: { color: "#f87171", message: "⬇️  Move further away" },
  tooFar: { color: "#facc15", message: "⬆️  Move closer to receipt" },
  good: { color: "#4ade80", message: "✅  Ready for capture!" },
};

export default function ReceiptScanner() {
  const isFocused = useIsFocused();
  const [permission, requestPermission] = useCameraPermissions();
  const detector = useDetector();
  const isStable = useDeviceStability();
  const orientation = useJerkCorrection();

  const cameraRef = useRef<CameraView>(null);

  const [isCameraReady, setIsCameraReady] = useState(false);
  const [capturedBase64, setCapturedBase64] = useState<string | null>(null);

  const status: keyof typeof statusMessages = !isStable
    ? "moving"
    : detector.result;

  // passive image analysis
  useEffect(() => {
    if (
      !detector.isReady ||
      detector.isLoading ||
      !isStable ||
      !cameraRef.current ||
      !isCameraReady
      // || capturedBase64
    ) {
      return;
    }

    cameraRef.current
      .takePictureAsync({
        base64: true,
        shutterSound: false,
        skipProcessing: false,
      })
      .then((picture) => {
        const rotation = orientation.getRotation();
        return orientation.ensurePortrait(picture, rotation);
      })
      .then((corrected) => {
        setCapturedBase64(corrected.base64!);
        detector.analyzeReceipt(corrected.base64!);
      });
  }, [detector, isStable, isCameraReady, capturedBase64, orientation]);

  // auto capture when status is good
  // useEffect(() => {
  //   if (
  //     !cameraRef.current ||
  //     !isCameraReady ||
  //     capturedBase64 ||
  //     status !== "good"
  //   ) {
  //     return;
  //   }

  //   const timer = setTimeout(() => {
  //     cameraRef.current!.takePictureAsync({
  //       base64: true,
  //       shutterSound: false,
  //     })
  // .then((picture) => detector.analyzeReceipt(picture.base64!))
  //   }, 100);

  //   return () => clearTimeout(timer);
  // }, [isCameraReady, capturedBase64, status]);

  return !permission ? (
    // error: no permission
    <View />
  ) : !permission.granted ? (
    // permission screen
    <View style={styles.center}>
      <Text onPress={requestPermission} className="text-white">
        Grant Camera Permission
      </Text>
    </View>
  ) : (
    // captured photo view
    <View style={styles.container}>
      {false ? (
        <View style={styles.camera}>
          <Image
            source={{ uri: "data:image/jpeg;base64," + capturedBase64 }}
            resizeMode="contain"
          />
          <Text
            onPress={() => setCapturedBase64(null)}
            style={styles.bannerText}
          >
            Tap to dismiss
          </Text>
        </View>
      ) : (
        isFocused && (
          // live camera view
          <>
            <Image
              source={{ uri: "data:image/jpeg;base64," + capturedBase64 }}
              style={StyleSheet.absoluteFill}
              resizeMode="contain"
              className="top-0 right-0 z-10 w-1/3"
            />
            <CameraView
              ref={cameraRef}
              animateShutter={false}
              onCameraReady={() => setIsCameraReady(true)}
              pictureSize="640x480"
              style={styles.camera}
            />
            {/* dimmed overlay with transparent center */}
            <View style={[styles.overlay, StyleSheet.absoluteFill]}>
              <View style={styles.maskTop} />
              <View style={styles.maskMiddle}>
                <View style={styles.maskSide} />
                {/* receipt frame */}
                <View
                  style={[
                    styles.frame,
                    { borderColor: statusMessages[status].color },
                  ]}
                />
                <View style={styles.maskSide} />
              </View>
              <View style={styles.maskBottom} />
            </View>
            {/* status label */}
            <View style={styles.banner}>
              <Text style={styles.bannerText}>
                {statusMessages[status].message}
              </Text>
            </View>
          </>
        )
      )}
    </View>
  );
}

const FRAME_WIDTH = 300;
const FRAME_HEIGHT = 420;

const styles = StyleSheet.create({
  container: { flex: 1 },
  cameraContainer: { flex: 1 }, // ← add this
  camera: { flex: 1 },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },

  overlay: { ...StyleSheet.absoluteFillObject },
  maskTop: { flex: 1, backgroundColor: "#00000088" },
  maskBottom: { flex: 1, backgroundColor: "#00000088" },
  maskMiddle: { flexDirection: "row", height: FRAME_HEIGHT },
  maskSide: { flex: 1, backgroundColor: "#00000088" },

  frame: {
    width: FRAME_WIDTH,
    height: FRAME_HEIGHT,
    borderWidth: 2,
    borderRadius: 4,
  },

  banner: {
    position: "absolute",
    bottom: 60,
    alignSelf: "center",
    backgroundColor: "#00000099",
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    marginVertical: "auto",
  },
  bannerText: { color: "#fff", fontSize: 15, fontWeight: "600" },
});
