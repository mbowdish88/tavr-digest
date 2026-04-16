import type { Metadata } from "next";
import {
  Big_Shoulders,
  Fraunces,
  Space_Grotesk,
  JetBrains_Mono,
} from "next/font/google";
import "./globals.css";
import Masthead from "@/components/Masthead";
import KickerBar from "@/components/KickerBar";
import Footer from "@/components/Footer";

const bigShoulders = Big_Shoulders({
  subsets: ["latin"],
  weight: ["500", "600", "700", "800", "900"],
  variable: "--font-big-shoulders",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-jetbrains-mono",
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
    <html
      lang="en"
      className={`${bigShoulders.variable} ${fraunces.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable}`}
    >
      <body className="min-h-screen flex flex-col">
        <Masthead />
        <KickerBar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
