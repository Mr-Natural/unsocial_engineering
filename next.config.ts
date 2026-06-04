import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable the dev-tools indicator overlay — works around the SegmentViewNode
  // RSC error, a known dev-only bug in Next.js 15.5.x.
  devIndicators: false,
};

export default nextConfig;
