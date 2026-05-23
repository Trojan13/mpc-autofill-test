"use client";

import { useState } from "react";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/images/search`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, page: 1, per_page: 50 }),
        }
      );
      const data = await res.json();
      setResults(data);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Search Images</h1>
      <form onSubmit={handleSearch} className="flex gap-4 mb-8">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for card images..."
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {results.map((image: any) => (
          <div
            key={image.id}
            className="border rounded-lg overflow-hidden hover:shadow-md transition"
          >
            {image.thumbnail_url && (
              <img
                src={image.thumbnail_url}
                alt={image.name}
                className="w-full h-48 object-cover"
              />
            )}
            <div className="p-2">
              <p className="text-sm font-medium truncate">{image.name}</p>
              <p className="text-xs text-gray-500">{image.card_type}</p>
            </div>
          </div>
        ))}
      </div>

      {results.length === 0 && !loading && query && (
        <p className="text-center text-gray-500 mt-8">
          No images found for &quot;{query}&quot;
        </p>
      )}
    </div>
  );
}
