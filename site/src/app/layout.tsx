import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "The Valve Wire — Structural Heart Disease",
    template: "%s | The Valve Wire",
  },
  description:
    "A platform for dissemination of both transcatheter and surgical therapies for structural heart disease. Balanced, evidence-based research, trials, regulation, and market analysis.",
  metadataBase: new URL("https://thevalvewire.com"),
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://thevalvewire.com",
    siteName: "The Valve Wire",
    title: "The Valve Wire — Structural Heart Disease",
    description:
      "A platform for dissemination of both transcatheter and surgical therapies for structural heart disease.",
    images: [{ url: "/images/cover.png", width: 1200, height: 1200 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "The Valve Wire",
    description:
      "A platform for dissemination of both transcatheter and surgical therapies for structural heart disease.",
    images: ["/images/cover.png"],
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
