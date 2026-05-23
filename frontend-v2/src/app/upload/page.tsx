"use client";

import { useCallback, useState } from "react";

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files).filter((f) =>
      f.type.startsWith("image/")
    );
    setFiles((prev) => [...prev, ...droppedFiles]);
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        const selected = Array.from(e.target.files).filter((f) =>
          f.type.startsWith("image/")
        );
        setFiles((prev) => [...prev, ...selected]);
      }
    },
    []
  );

  async function handleUpload() {
    if (files.length === 0) return;
    setUploading(true);
    setMessage("");

    const token = localStorage.getItem("access_token");
    if (!token) {
      setMessage("Please log in to upload images.");
      setUploading(false);
      return;
    }

    let successCount = 0;
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("name", file.name.replace(/\.[^/.]+$/, ""));
      formData.append("card_type", "card");
      formData.append("tags", "");
      // Source ID would come from user's upload source
      formData.append("source_id", "");

      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/images/upload`,
          {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
          }
        );
        if (res.ok) successCount++;
      } catch (err) {
        console.error("Upload failed for", file.name, err);
      }
    }

    setMessage(`Uploaded ${successCount} of ${files.length} images.`);
    setFiles([]);
    setUploading(false);
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Upload Images</h1>

      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-500 transition"
      >
        <p className="text-gray-600 mb-4">
          Drag and drop image files here, or click to select
        </p>
        <input
          type="file"
          multiple
          accept="image/png,image/jpeg"
          onChange={handleFileInput}
          className="hidden"
          id="file-input"
        />
        <label
          htmlFor="file-input"
          className="px-4 py-2 bg-gray-100 rounded cursor-pointer hover:bg-gray-200"
        >
          Select Files
        </label>
      </div>

      {files.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">
            Selected Files ({files.length})
          </h2>
          <ul className="space-y-1 mb-4">
            {files.map((f, i) => (
              <li key={i} className="text-sm text-gray-700">
                {f.name} ({(f.size / 1024).toFixed(1)} KB)
              </li>
            ))}
          </ul>
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {uploading ? "Uploading..." : "Upload All"}
          </button>
        </div>
      )}

      {message && <p className="mt-4 text-green-700 font-medium">{message}</p>}
    </div>
  );
}
