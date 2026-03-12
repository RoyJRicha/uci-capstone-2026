import { CameraCapturedPicture } from "expo-camera";
import { ImageManipulator } from "expo-image-manipulator";

const exifRotationMap: Record<number, number> = {
  1: 90,
  3: -90,
  6: 0,
  8: 180,
};

export async function ensurePortrait(photo: CameraCapturedPicture) {
  let rotation = exifRotationMap[photo.exif["Orientation"] as number] ?? 0;

  let context = ImageManipulator.manipulate(photo.uri);
  if (rotation !== 0) {
    context.rotate(rotation);
  }

  const renderedImage = await context.renderAsync();
  return renderedImage.saveAsync({ base64: true });
}
