import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MPC Autofill",
  description: "Image aggregation & print automation for tabletop gaming",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <nav className="border-b bg-white px-6 py-4">
          <div className="mx-auto flex max-w-7xl items-center justify-between">
            <a href="/" className="text-xl font-bold text-gray-900">
              MPC Autofill
            </a>
            <div className="flex gap-6">
              <a href="/search" className="text-gray-600 hover:text-gray-900">
                Search
              </a>
              <a href="/library" className="text-gray-600 hover:text-gray-900">
                My Library
              </a>
              <a href="/upload" className="text-gray-600 hover:text-gray-900">
                Upload
              </a>
              <a
                href="/projects"
                className="text-gray-600 hover:text-gray-900"
              >
                Projects
              </a>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
