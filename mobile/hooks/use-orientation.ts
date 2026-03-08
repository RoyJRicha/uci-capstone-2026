import { CameraCapturedPicture, CameraOrientation } from "expo-camera";
import { ImageManipulator } from "expo-image-manipulator";

import { Platform } from "react-native";

import { useState } from "react";

export function useOrientation() {
  const [iosOrientation, setIosOrientation] =
    useState<CameraOrientation>("portrait");

  async function ensurePortrait(photo: CameraCapturedPicture) {
    const isLandscape = photo.width > photo.height;

    // android only, test ios
    if (Platform.OS === "android") {
      console.log("orientation", photo.exif["Orientation"]);
    } else {
      console.log("orientation", photo.exif);
    }

    const map: Record<number, number> = {
      1: 90,
      6: 0,
      8: 180,
      3: -90,
    };

    let rotation = map[photo.exif["Orientation"]] ?? 0;

    let context = ImageManipulator.manipulate(photo.uri);
    context.rotate(rotation);

    const renderedImage = await context.renderAsync();
    const result = await renderedImage.saveAsync({ base64: true });
    return result;
  }

  return { ensurePortrait };
}
