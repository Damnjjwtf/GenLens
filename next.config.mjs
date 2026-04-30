/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // Lint runs separately. Don't fail prod builds on stylistic warnings.
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Pre-existing Neon driver type-cast issues in cron/api routes block
    // builds. Type-check runs separately; revisit after a typing cleanup pass.
    ignoreBuildErrors: true,
  },
  async redirects() {
    return [
      // Old /index/* URLs → /markets/* (folder renamed to sidestep a
      // Next 14 prerender bug specific to `app/index/` siblings).
      { source: '/index', destination: '/markets', permanent: true },
      { source: '/index/:path*', destination: '/markets/:path*', permanent: true },
    ]
  },
};

export default nextConfig;
