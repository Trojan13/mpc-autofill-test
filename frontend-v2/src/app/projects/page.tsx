"use client";

import { useEffect, useState } from "react";

interface Project {
  id: string;
  name: string;
  created_at: string;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjects();
  }, []);

  async function fetchProjects() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/projects/`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const data = await res.json();
      setProjects(data);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("Please log in first.");
      return;
    }
    const name = prompt("Enter project name:");
    if (!name) return;

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/projects/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ name }),
        }
      );
      if (res.ok) fetchProjects();
    } catch (err) {
      console.error("Failed to create project:", err);
    }
  }

  async function handleExport(projectId: string) {
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/projects/${projectId}/export`,
        { headers: { Authorization: `Bearer ${token || ""}` } }
      );
      const data = await res.json();
      // Download as JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${data.project_name || "project"}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to export project:", err);
    }
  }

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Projects</h1>
        <button
          onClick={handleCreate}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          New Project
        </button>
      </div>

      <div className="space-y-4">
        {projects.map((project) => (
          <div
            key={project.id}
            className="p-4 border rounded-lg flex items-center justify-between"
          >
            <div>
              <h3 className="font-semibold">{project.name}</h3>
              <p className="text-sm text-gray-500">
                Created: {new Date(project.created_at).toLocaleDateString()}
              </p>
            </div>
            <div className="flex gap-2">
              <a
                href={`/projects/${project.id}`}
                className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
              >
                Edit
              </a>
              <button
                onClick={() => handleExport(project.id)}
                className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded hover:bg-green-200"
              >
                Export JSON
              </button>
            </div>
          </div>
        ))}

        {projects.length === 0 && (
          <p className="text-gray-500 text-center py-8">
            No projects yet. Create one to get started building your card order.
          </p>
        )}
      </div>
    </div>
  );
}
