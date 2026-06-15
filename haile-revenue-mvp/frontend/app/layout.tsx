import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Haile Revenue OS",
  description: "Autonomous AI Revenue System for Haile Resort",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
