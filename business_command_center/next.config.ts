import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  async redirects() {
    return [
      { source: '/admin/:path*', destination: '/', permanent: false },
      { source: '/company/:path*', destination: '/', permanent: false },
      { source: '/portal', destination: '/', permanent: false },
    ];
  },
};

export default nextConfig;
