import type { Metadata } from "next";
import { Outfit, Playfair_Display, Space_Mono } from "next/font/google";
import "./globals.css";
import Provider from "@/components/provider";

const outfitSans = Outfit({
  variable: "--font-outfit-sans",
  subsets: ["latin"],
});

const playfairDisplay = Playfair_Display({
  variable: "--font-playfair-display",
  subsets: ["latin"],
});

const spaceMono = Space_Mono({
  variable: "--font-space-mono",
  subsets: ["latin"],
  weight: "400",
});

export const metadata: Metadata = {
  title: "Kalam3",
  description: "Handwriting generator",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${outfitSans.variable} ${playfairDisplay.variable} ${spaceMono} antialiased dark`}
      >
        <Provider>{children}</Provider>
      </body>
    </html>
  );
}
