import type { Metadata } from "next";
import { Suspense } from "react";
import { Inter, IBM_Plex_Mono } from "next/font/google";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { RunProvider } from "@/components/run-provider";
import { AppShell } from "@/components/app-shell";
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
      <body>
        <TooltipProvider delayDuration={150}>
          <Suspense fallback={null}>
            <RunProvider>
              <AppShell>{children}</AppShell>
            </RunProvider>
          </Suspense>
        </TooltipProvider>
        <Toaster />
      </body>
    </html>
  );
}
