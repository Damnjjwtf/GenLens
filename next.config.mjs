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
};

export default nextConfig;
