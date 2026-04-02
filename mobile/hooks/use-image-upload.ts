import { fetch } from "expo/fetch";

export const IMAGE_UPLOAD_API = "http://192.168.86.248:8000";

export function useImageUpload() {
  async function uploadImage(uri: string, type: "shelf" | "receipt") {
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

    if (!uploadResponse.ok) {
      throw new Error(
        `Upload failed: ${uploadResponse.status} ${uploadResponse.statusText}`,
      );
    }

    return uploadResponse.json();
  }

  return { uploadImage };
}
