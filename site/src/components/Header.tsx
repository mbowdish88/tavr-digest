"use client";
import Link from "next/link";
import Image from "next/image";
import { useState } from "react";

const NAV = [
  { label: "Today", href: "/" },
  { label: "Archive", href: "/archive" },
  { label: "Weekly", href: "/weekly" },
  { label: "Podcast", href: "/podcast" },
  { label: "About", href: "/about" },
];

export default function Header() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <header className="sticky top-0 z-50" style={{ backgroundColor: "var(--color-navy)" }}>
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          {/* Logo + wordmark */}
          <Link href="/" className="flex items-center gap-3">
            <Image
              src="/images/profile-blue.jpg"
              alt=""
              width={32}
              height={32}
              className="rounded-full object-cover w-8 h-8"
            />
            <span
              className="text-[22px] uppercase tracking-[0.08em] leading-none"
              style={{
                fontFamily: "var(--font-playfair), 'Playfair Display', Georgia, serif",
                color: "#F1EDE4",
              }}
            >
              The Valve Wire
            </span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-6">
            {NAV.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                className="nav-font text-[13px] transition-colors hover:text-white"
                style={{ color: "#B8C4D4", textDecoration: "none" }}
              >
                {n.label}
              </Link>
            ))}
            <a
              href="mailto:nolan.beckett@pm.me?subject=Subscribe"
              className="nav-font text-[13px] transition-colors hover:text-white"
              style={{ color: "#B8C4D4", textDecoration: "none" }}
            >
              Subscribe
            </a>
          </nav>

          {/* Mobile hamburger */}
          <button className="md:hidden" style={{ color: "#F1EDE4" }} onClick={() => setOpen(!open)}>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {open
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />}
            </svg>
          </button>
        </div>

        {/* Mobile overlay */}
        {open && (
          <div className="md:hidden px-4 py-4" style={{ backgroundColor: "var(--color-navy)", borderTop: "1px solid rgba(255,255,255,0.1)" }}>
            {NAV.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                onClick={() => setOpen(false)}
                className="block nav-font text-base py-3 transition-colors hover:text-white"
                style={{ color: "#B8C4D4", borderBottom: "1px solid rgba(255,255,255,0.08)", textDecoration: "none" }}
              >
                {n.label}
              </Link>
            ))}
            <a
              href="mailto:nolan.beckett@pm.me?subject=Subscribe"
              className="block nav-font text-base py-3 transition-colors hover:text-white"
              style={{ color: "#B8C4D4", textDecoration: "none" }}
            >
              Subscribe
            </a>
          </div>
        )}
      </header>
      {/* Accent stripe below header */}
      <div className="h-0.5 w-full" style={{ backgroundColor: "var(--color-accent)" }} />
    </>
  );
}
