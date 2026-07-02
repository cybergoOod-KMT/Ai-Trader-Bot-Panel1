import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Tabdeal AI Trading Panel",
  description: "Phase 1 foundation for a real Tabdeal personal trading panel.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
