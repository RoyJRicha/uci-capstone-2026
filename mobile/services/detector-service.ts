import { WebView } from "react-native-webview";

import EventEmitter from "eventemitter3";

const state = {
  isReady: false,
  isLoading: false,
  isLoggingEnabled: false,
  webViewRef: null as WebView | null,
  eventEmitter: new EventEmitter<"DetectorMessage">(),
};

export type DetectorResult = "notFound" | "tooClose" | "tooFar" | "good";

export type DetectorMessage =
  | { type: "READY"; message?: never }
  | { type: "ANALYZE_RECEIPT"; message: string }
  | { type: "ANALYZE_SHELF"; message: string }
  | { type: "RESULT"; message: DetectorResult }
  | { type: "ERROR"; message: Error }
  | { type: "LOG"; message: string };

export const DetectorService = {
  register: (ref: WebView | null) => {
    state.webViewRef = ref;
  },

  analyzeReceipt: (base64Image: string) => {
    if (!state.webViewRef) {
      console.error("DetectorProvider WebView not initialized");
      return;
    }

    if (state.isLoading) {
      return;
    }
    state.isLoading = true;

    state.webViewRef.postMessage(
      JSON.stringify({ type: "ANALYZE_RECEIPT", message: base64Image }),
    );
  },

  analyzeShelf: (base64Image: string) => {
    if (!state.webViewRef) {
      console.error("DetectorProvider WebView not initialized");
      return;
    }

    if (state.isLoading) {
      return;
    }
    state.isLoading = true;

    state.webViewRef.postMessage(
      JSON.stringify({ type: "ANALYZE_SHELF", message: base64Image }),
    );
  },

  emitMessage: (message: DetectorMessage) => {
    if (message.type === "READY") {
      state.isReady = true;
    } else if (message.type === "RESULT" || message.type === "ERROR") {
      state.isLoading = false;
    }

    state.eventEmitter.emit("DetectorMessage", message);

    if (state.isLoggingEnabled) {
      console.log(
        "[OpenCV]",
        message.type,
        typeof message.message === "object"
          ? JSON.stringify(message.message, null, 2)
          : (message.message ?? ""),
      );
    }
  },

  subscribe: (callback: (message: DetectorMessage) => void) => {
    state.eventEmitter.on("DetectorMessage", callback);

    if (state.isReady) {
      callback({ type: "READY" });
    }

    return () => {
      state.eventEmitter.off("DetectorMessage", callback);
    };
  },

  setLogging: (isEnabled: boolean) => {
    state.isLoggingEnabled = isEnabled;
  },
};
