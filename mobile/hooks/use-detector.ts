import { useEffect, useState } from "react";

import { DetectorResult, DetectorService } from "@/services/detector-service";

export function useDetector() {
  const [isReady, setIsReady] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<DetectorResult>("notFound");
  const [error, setError] = useState<Error | undefined>(undefined);

  useEffect(() => {
    const unsubscribe = DetectorService.subscribe((msg) => {
      switch (msg.type) {
        case "READY":
          setIsReady(true);
          break;
        case "RESULT":
          setResult(msg.message);
          setIsLoading(false);
          break;
        case "ERROR":
          setError(msg.message);
          setIsLoading(false);
          break;
      }
    });

    return unsubscribe;
  }, []);

  return {
    isReady,
    isLoading,
    result,
    error,

    analyzeReceipt: (base64Image: string) => {
      setIsLoading(true);
      DetectorService.analyzeReceipt(base64Image);
    },

    analyzeShelf: (base64Image: string) => {
      setIsLoading(true);
      DetectorService.analyzeShelf(base64Image);
    },

    setLogging: DetectorService.setLogging,
  };
}
