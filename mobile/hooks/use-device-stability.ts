import { Accelerometer } from "expo-sensors";

import { useEffect, useRef, useState } from "react";

export function useDeviceStability(threshold = 0.06, settleDuration = 100) {
  const [isStable, setIsStable] = useState(false);

  const last = useRef<{ x: number; y: number; z: number } | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const waitingToSettle = useRef(false); // track if timer is already running

  useEffect(() => {
    Accelerometer.setUpdateInterval(100);

    const listener = Accelerometer.addListener((a) => {
      if (last.current === null) {
        last.current = a;
        return;
      }

      const delta =
        Math.abs(a.x - last.current.x) +
        Math.abs(a.y - last.current.y) +
        Math.abs(a.z - last.current.z);

      last.current = a;

      if (delta > threshold) {
        // Movement detected — cancel any pending settle and mark unstable
        clearTimeout(timer.current);
        waitingToSettle.current = false;
        setIsStable(false);
      } else if (!waitingToSettle.current) {
        // Just became stable — start the settle timer once
        waitingToSettle.current = true;
        timer.current = setTimeout(() => {
          waitingToSettle.current = false;
          setIsStable(true);
        }, settleDuration);
      }
      // If already waiting to settle, do nothing — let the timer run
    });

    return () => {
      listener.remove();
      clearTimeout(timer.current);
    };
  }, [threshold, settleDuration]);

  return isStable;
}
