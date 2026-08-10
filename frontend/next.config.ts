import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Built as a static export and served directly by the FastAPI backend
  // (see backend/app/main.py) so the whole app ships as one process/port.
  output: "export",
  // Without this, `next build` emits e.g. `login.html` (a *file*) for the
  // /login route. Starlette's StaticFiles(html=True) mount only falls back
  // to index.html when the requested path resolves to an existing
  // *directory* — a bare `/login` request against a `login.html` file with
  // no extension 404s. trailingSlash emits `login/index.html` instead,
  // which StaticFiles resolves correctly. Only mattered once PREL-7 added
  // routes beyond `/`.
  trailingSlash: true,
};

export default nextConfig;
