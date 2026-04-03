import { fetch } from "expo/fetch";

import { useState } from "react";

const IMAGE_UPLOAD_API = "http://192.168.86.248:8000";

type UploadResponse = {
  success: boolean;
  data: any;
};

export function useImageUpload() {
  const [loading, setLoading] = useState(false);

  async function uploadImage(
    uri: string,
    type: "shelf" | "receipt",
  ): Promise<UploadResponse> {
    setLoading(true);

    try {
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

      return { success: uploadResponse.ok, data: await uploadResponse.json() };
    } catch (error) {
      return { success: false, data: { error } };
    } finally {
      setLoading(false);
    }
  }

  return { loading, uploadImage };
}
