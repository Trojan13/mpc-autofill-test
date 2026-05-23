"use client";

import { useEffect, useState } from "react";

interface Source {
  id: string;
  name: string;
  source_type: string;
  last_synced_at: string | null;
}

export default function LibraryPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSources();
  }, []);

  async function fetchSources() {
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/sources/`,
        {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      const data = await res.json();
      setSources(data);
    } catch (err) {
      console.error("Failed to fetch sources:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleConnectDrive() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("Please log in first.");
      return;
    }
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/sources/google-drive/connect`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const data = await res.json();
      window.location.href = data.oauth_url;
    } catch (err) {
      console.error("Failed to start Drive connection:", err);
    }
  }

  async function handleCreateUploadSource() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("Please log in first.");
      return;
    }
    const name = prompt("Enter a name for your upload library:");
    if (!name) return;

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/sources/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            name,
            source_type: "upload",
            config: {},
          }),
        }
      );
      if (res.ok) {
        fetchSources();
      }
    } catch (err) {
      console.error("Failed to create source:", err);
    }
  }

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">My Library</h1>

      <div className="flex gap-4 mb-8">
        <button
          onClick={handleConnectDrive}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Connect Google Drive
        </button>
        <button
          onClick={handleCreateUploadSource}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          Create Upload Library
        </button>
      </div>

      <div className="space-y-4">
        {sources.map((source) => (
          <div
            key={source.id}
            className="p-4 border rounded-lg flex items-center justify-between"
          >
            <div>
              <h3 className="font-semibold">{source.name}</h3>
              <p className="text-sm text-gray-500">
                Type: {source.source_type === "google_drive" ? "Google Drive" : "Upload"}
              </p>
              {source.last_synced_at && (
                <p className="text-xs text-gray-400">
                  Last synced: {new Date(source.last_synced_at).toLocaleString()}
                </p>
              )}
            </div>
            {source.source_type === "google_drive" && (
              <button className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200">
                Sync
              </button>
            )}
          </div>
        ))}

        {sources.length === 0 && (
          <p className="text-gray-500 text-center py-8">
            No sources configured. Connect a Google Drive or create an upload
            library to get started.
          </p>
        )}
      </div>
    </div>
  );
}
