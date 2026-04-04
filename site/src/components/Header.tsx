"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";

const NAV_ITEMS = [
  { label: "Today", href: "/" },
  { label: "Archive", href: "/archive" },
  { label: "Podcast", href: "/podcast" },
  { label: "About", href: "/about" },
];

const TOPICS = [
  { label: "Aortic (TAVR)", href: "/#aortic" },
  { label: "Mitral", href: "/#mitral" },
  { label: "Tricuspid", href: "/#tricuspid" },
  { label: "Surgical vs Transcatheter", href: "/#surgical" },
  { label: "Clinical Trials", href: "/#trials" },
  { label: "Regulatory", href: "/#regulatory" },
  { label: "Financial", href: "/#financial" },
];

export default function Header() {
  const [topicsOpen, setTopicsOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-[#1B2A4A] shadow-md">
      {/* Top utility bar — navy background */}
      <div className="bg-[#1B2A4A] border-b border-[#3D5873] px-4 py-1.5 text-xs nav-font text-[#EDE0C4]/70 flex justify-between items-center max-w-7xl mx-auto">
        <span>Structural Heart Disease — Research, Trials &amp; Analysis</span>
        <a
          href="mailto:nolan.beckett@pm.me?subject=Subscribe%20to%20The%20Valve%20Wire"
          className="text-[#EDE0C4] border border-[#EDE0C4]/40 px-3 py-0.5 rounded text-xs font-medium hover:bg-[#EDE0C4]/10 transition-colors"
        >
          Subscribe
        </a>
      </div>

      {/* Main nav */}
      <div className="max-w-7xl mx-auto px-4 py-5 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-4">
          <Image
            src="/images/profile-blue.jpg"
            alt="The Valve Wire"
            width={64}
            height={64}
            className="rounded-lg shadow-lg w-10 h-10 sm:w-14 sm:h-14 md:w-16 md:h-16 object-cover"
          />
          <div>
            <h1
              className="text-xl sm:text-3xl md:text-4xl font-medium text-white leading-tight"
              style={{ letterSpacing: "0.02em" }}
            >
              The Valve Wire
            </h1>
            <p className="text-[11px] text-[#EDE0C4]/80 uppercase tracking-[0.25em] font-semibold">
              Structural Heart Disease
            </p>
          </div>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6 nav-font text-sm">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-white hover:text-[var(--color-cream)] transition-colors font-medium"
            >
              {item.label}
            </Link>
          ))}

          {/* Topics dropdown */}
          <div className="relative">
            <button
              onClick={() => setTopicsOpen(!topicsOpen)}
              className="text-white hover:text-[var(--color-cream)] transition-colors font-medium flex items-center gap-1"
            >
              Topics
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {topicsOpen && (
              <div
                className="absolute top-full right-0 mt-2 bg-white rounded-lg shadow-xl py-2 w-48 z-50"
                onMouseLeave={() => setTopicsOpen(false)}
              >
                {TOPICS.map((topic) => (
                  <Link
                    key={topic.href}
                    href={topic.href}
                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-[var(--color-surface-alt)] transition-colors"
                    onClick={() => setTopicsOpen(false)}
                  >
                    {topic.label}
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Search */}
          <Link href="/archive" className="text-[#EDE0C4]/60 hover:text-[var(--color-cream)]">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </Link>
        </nav>

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-white"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {mobileOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-[var(--color-burgundy)] px-4 py-3 nav-font">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block py-2 text-white hover:text-[var(--color-cream)] font-medium"
              onClick={() => setMobileOpen(false)}
            >
              {item.label}
            </Link>
          ))}
          <div className="border-t border-[var(--color-burgundy)] mt-2 pt-2">
            <p className="text-xs text-[var(--color-cream)]/60 mb-1">Topics</p>
            {TOPICS.map((topic) => (
              <Link
                key={topic.href}
                href={topic.href}
                className="block py-1.5 text-sm text-white hover:text-[var(--color-cream)]"
                onClick={() => setMobileOpen(false)}
              >
                {topic.label}
              </Link>
            ))}
          </div>
        </div>
      )}
      {/* Steel blue accent line */}
      <div className="h-[2px] bg-[var(--color-accent)]" />
    </header>
  );
}
