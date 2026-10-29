import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  async redirects() {
    return [
      { source: '/company/assessments', destination: '/?tab=towers', permanent: false },
      { source: '/company/deliverables', destination: '/?tab=deliverables', permanent: false },
      { source: '/company/team', destination: '/?tab=clients', permanent: false },
      { source: '/company/compliance', destination: '/?tab=fair', permanent: false },
      { source: '/portal/upload', destination: '/', permanent: false },
      { source: '/portal/deliverables', destination: '/?tab=deliverables', permanent: false },
      { source: '/portal/help', destination: '/?tab=telemetry', permanent: false },
      { source: '/admin/organizations', destination: '/?tab=clients', permanent: false },
      { source: '/admin/users', destination: '/?tab=clients', permanent: false },
      { source: '/admin/policies', destination: '/?tab=fair', permanent: false },
      { source: '/admin/audit', destination: '/?tab=overview', permanent: false },
      { source: '/admin/evidence', destination: '/?tab=overview', permanent: false },
    ];
  },
};

export default nextConfig;
