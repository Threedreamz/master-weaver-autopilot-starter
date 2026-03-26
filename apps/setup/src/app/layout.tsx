import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoPilot Setup",
  description: "Ersteinrichtung des AutoPilot CT-Scanners auf dem Raspberry Pi",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de" className="dark">
      <body className="min-h-dvh bg-gray-950 text-gray-100 antialiased no-select">
        <main className="mx-auto max-w-2xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
