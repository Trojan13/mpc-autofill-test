export default function HomePage() {
  return (
    <div className="text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">MPC Autofill</h1>
      <p className="text-lg text-gray-600 mb-8">
        Image aggregation &amp; print automation for your tabletop gaming
        community.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
        <a
          href="/search"
          className="block p-6 bg-white rounded-lg border hover:shadow-md transition"
        >
          <h2 className="text-xl font-semibold mb-2">Search Images</h2>
          <p className="text-gray-600">
            Browse community drives and find card images for your project.
          </p>
        </a>
        <a
          href="/upload"
          className="block p-6 bg-white rounded-lg border hover:shadow-md transition"
        >
          <h2 className="text-xl font-semibold mb-2">Upload Images</h2>
          <p className="text-gray-600">
            Upload your own card images or connect your Google Drive.
          </p>
        </a>
        <a
          href="/projects"
          className="block p-6 bg-white rounded-lg border hover:shadow-md transition"
        >
          <h2 className="text-xl font-semibold mb-2">Build Projects</h2>
          <p className="text-gray-600">
            Assemble card fronts and backs, then export for MPC autofill.
          </p>
        </a>
      </div>
    </div>
  );
}
