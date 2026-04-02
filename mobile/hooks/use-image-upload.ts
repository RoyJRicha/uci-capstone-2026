import { fetch } from "expo/fetch";

import { useState } from "react";

export const IMAGE_UPLOAD_API = "http://192.168.86.248:8000";

export function useImageUpload() {
  const [loading, setLoading] = useState(false);

  async function uploadImage(uri: string, type: "shelf" | "receipt") {
    setLoading(true);

    const formData = new FormData();

    formData.append("file", {
      uri,
      name: `${type}.jpg`,
      type: "image/jpeg",
    } as unknown as Blob);

    const uploadResponse = await fetch(`${IMAGE_UPLOAD_API}/upload`, {
      method: "POST",
      body: formData,
    });

    setLoading(false);

    if (!uploadResponse.ok) {
      throw new Error(
        `Upload failed: ${uploadResponse.status} ${uploadResponse.statusText}`,
      );
    }

    return uploadResponse.json();
  }

  return { loading, uploadImage };
}
