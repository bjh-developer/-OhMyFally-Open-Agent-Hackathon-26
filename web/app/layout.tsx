import type { Metadata } from "next";
import { Inter, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], weight: ["300", "400", "600", "700"], display: "swap", variable: "--font-inter" });
const plexMono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400"], display: "swap", variable: "--font-plex-mono" });

export const metadata: Metadata = {
  title: "ProcureLens",
  description: "See which procurement awards need a second look.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-SG" className={`${inter.variable} ${plexMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
