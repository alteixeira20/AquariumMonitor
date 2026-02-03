import "./globals.css";
import type { Metadata } from "next";
import { DM_Serif_Display, Manrope } from "next/font/google";
import { ToastProvider } from "../components/ui/ToastProvider";

const display = DM_Serif_Display({
  subsets: ["latin"],
  variable: "--font-display",
  weight: "400",
});

const body = Manrope({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "AquariumMonitor — Setup",
  description: "First-run setup for AquariumMonitor",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body>
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  );
}
