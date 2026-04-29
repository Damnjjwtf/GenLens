/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // Lint runs separately. Don't fail prod builds on stylistic warnings.
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
