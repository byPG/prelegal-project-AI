import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Built as a static export and served directly by the FastAPI backend
  // (see backend/app/main.py) so the whole app ships as one process/port.
  output: "export",
};

export default nextConfig;
