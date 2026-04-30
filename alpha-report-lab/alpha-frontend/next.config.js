/** @type {import('next').NextConfig} */
const nextConfig = {
  // Strict Mode double-invokes effects in dev, which doubles every initial
  // fetch. Combined with OneAgent's fetch instrumentation latency on Windows,
  // this causes visible delays on the dashboard. Disable for a quieter dev loop.
  reactStrictMode: false,
  env: {
    PYTHON_SERVICE_URL: process.env.PYTHON_SERVICE_URL || "http://localhost:8000",
  },
};

module.exports = nextConfig;
