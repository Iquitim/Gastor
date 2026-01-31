import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: 'export',
  images: {
    unoptimized: true
  },
  // Ensure trailing slashes for standard static hosting compatibility
  trailingSlash: true,
  webpack: (config) => {
    config.resolve.alias['@'] = path.join(process.cwd(), 'src');
    return config;
  },
};

export default nextConfig;
