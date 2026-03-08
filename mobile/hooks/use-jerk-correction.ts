import { CameraCapturedPicture } from "expo-camera";
import { ImageManipulator } from "expo-image-manipulator";
import { Gyroscope } from "expo-sensors";

import { useCallback, useEffect, useRef } from "react";

/**
 * Tracks the direction of the last significant rotation (jerk)
 * using the gyroscope z-axis (roll: phone rotating CW/CCW
 * in the plane of the screen).
 *
 * Returns a function that gives the recommended rotation
 * correction when the captured image is landscape but should
 * be portrait.
 */
export function useJerkCorrection() {
  // 'cw' (clockwise) or 'ccw' (counter-clockwise)
  const lastJerkDirection = useRef<any>(null);

  useEffect(() => {
    Gyroscope.setUpdateInterval(50); // 20 reads/sec for responsiveness

    const sub = Gyroscope.addListener(({ z }) => {
      // z-axis = roll (rotating phone in the plane of the screen)
      // z > 0 → CCW (tilting left)
      // z < 0 → CW  (tilting right)
      const THRESHOLD = 1.5; // rad/s — tweak if too sensitive or not enough

      if (Math.abs(z) > THRESHOLD) {
        lastJerkDirection.current = z > 0 ? "ccw" : "cw";
      }
    });

    return () => sub.remove();
  }, []);

  /**
   * Returns 90 or 270 based on the last detected jerk direction.
   * Falls back to 90 if no jerk was detected.
   */
  const getRotation = useCallback(() => {
    // ─── Default mapping ───
    // Jerked CCW (left)  → sensor stuck in "left landscape"  → rotate 90° CW to fix
    // Jerked CW  (right) → sensor stuck in "right landscape" → rotate 270° CW to fix
    //
    // ⚠️ If your device produces the opposite result, swap 90 ↔ 270 here.
    if (lastJerkDirection.current === "cw") {
      return 90;
    }
    return 270; // default / CCW jerk
  }, []);

  async function ensurePortrait(
    photo: CameraCapturedPicture,
    rotation: number,
  ) {
    const needsRotation = photo.width > photo.height;

    console.log(needsRotation, photo.width, photo.height, rotation);

    if (!needsRotation) {
      return photo;
    }

    let context = ImageManipulator.manipulate(photo.uri);
    context.rotate(rotation);

    const renderedImage = await context.renderAsync();
    const result = await renderedImage.saveAsync({ base64: true });
    return result;
  }

  return { getRotation, ensurePortrait };
}
