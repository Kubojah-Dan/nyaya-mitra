/** @type {import('next').NextConfig} */
const securityHeaders = [
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
  {
    key: "X-Content-Type-Options",
    value: "nosniff",
  },
  {
    key: "X-Frame-Options",
    value: "DENY",
  },
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin",
  },
  {
    key: "Permissions-Policy",
    value: "camera=(self), microphone=(self), geolocation=()",
  },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self';",
      "img-src 'self' data: https:;",
      "font-src 'self' https://fonts.gstatic.com data:;",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;",
      "connect-src 'self' https://*.vercel.app https://*.onrender.com https://*.render.com http://localhost:8000 http://127.0.0.1:8000;",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval';",
      "frame-ancestors 'none';",
      "form-action 'self';",
    ].join(" "),
  },
];

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
      {
        source: "/_next/static/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
