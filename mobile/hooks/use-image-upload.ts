import { useState } from "react";

import { API_BASE_URL as IMAGE_UPLOAD_API } from "@/constants/api";

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
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000); // 10 seconds

    try {
      const formData = new FormData();

      formData.append("file", {
        uri,
        name: `${type}.jpg`,
        type: "image/jpeg",
      } as any);

      const uploadResponse = await fetch(
        new URL("/upload", IMAGE_UPLOAD_API).toString(),
        {
          method: "POST",
          body: formData,
          signal: controller.signal,
        },
      );

      return { success: uploadResponse.ok, data: await uploadResponse.json() };
    } catch (error) {
      return { success: false, data: { error } };
    } finally {
      clearTimeout(timeout);
      setLoading(false);
    }
  }

  return { loading, uploadImage };
}
