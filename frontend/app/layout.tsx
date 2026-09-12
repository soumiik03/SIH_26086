import type { Metadata } from "next";
import { Manrope, Space_Grotesk } from "next/font/google";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope" });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-space-grotesk" });

export const metadata: Metadata = {
  title: "VARSHASENTINEL | Monsoon intelligence",
  description: "Verified monsoon forecast intelligence for supported Panchayats.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${manrope.variable} ${spaceGrotesk.variable}`}>{children}</body></html>;
}