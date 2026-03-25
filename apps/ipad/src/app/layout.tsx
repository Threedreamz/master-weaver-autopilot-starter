import type { Metadata, Viewport } from "next";
import { TouchNav } from "@/components/layout/TouchNav";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoPilot CT Scanner",
  description: "iPad touch-optimized CT scan control interface",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "CT Scanner",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de" className="dark">
      <body className="min-h-dvh bg-gray-950 text-gray-100 antialiased no-select">
        <main className="pb-[var(--nav-height)]">{children}</main>
        <TouchNav />
      </body>
    </html>
  );
}
