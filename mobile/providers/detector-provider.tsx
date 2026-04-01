import { Asset } from "expo-asset";
import { Directory, File, Paths } from "expo-file-system/next";

import { WebView } from "react-native-webview";

import { useEffect, useState } from "react";

import { DetectorMessage, DetectorService } from "@/services/detector-service";

export function DetectorProvider() {
  const [htmlUri, setHtmlUri] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const [htmlAsset] = await Asset.loadAsync(
        require("@/providers/detector.html"),
      );

      const dest = new Directory(Paths.document);
      const destHtml = new File(dest, "detector.html");

      const htmlFile = new File(htmlAsset.localUri!);
      const content = await htmlFile.text();
      destHtml.write(content);

      setHtmlUri(destHtml.uri);
    }
    load();
  }, []);

  return (
    htmlUri && (
      <WebView
        ref={DetectorService.register}
        source={{ uri: htmlUri }}
        onMessage={(event) => {
          const message: DetectorMessage = JSON.parse(event.nativeEvent.data);
          DetectorService.emitMessage(message);
        }}
        allowFileAccess
        javaScriptEnabled
        originWhitelist={["*"]}
        // hide display
        style={{
          position: "absolute",
          width: 1,
          height: 1,
          left: -10000,
        }}
        containerStyle={{ width: 0, height: 0, flex: 0 }}
        // ui optimizations
        bounces={false}
        overScrollMode="never"
        pointerEvents="none"
        scalesPageToFit={false}
        scrollEnabled={false}
        showsHorizontalScrollIndicator={false}
        showsVerticalScrollIndicator={false}
        // browser optimizations
        androidLayerType="software"
        cacheEnabled={false}
        domStorageEnabled={false}
        incognito
      />
    )
  );
}
