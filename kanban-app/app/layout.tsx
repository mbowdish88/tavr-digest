import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "Project Kanban",
  description: "Real-time project tracking dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Sidebar />
        <Header />
        <main className="ml-[180px] mt-[44px] h-[calc(100vh-44px)] overflow-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
