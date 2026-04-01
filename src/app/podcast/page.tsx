import type { Metadata } from "next";
import { getLatestDigest } from "@/lib/data";
import Image from "next/image";

export const metadata: Metadata = {
  title: "Podcast",
  description:
    "The Valve Wire Weekly podcast — weekly analysis of structural heart disease.",
};

export const dynamic = "force-dynamic";

export default function PodcastPage() {
  const data = getLatestDigest();
  const episodes = data.podcast.all_episodes || [data.podcast.latest_episode];

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      {/* Hero */}
      <div className="flex flex-col md:flex-row items-center gap-8 mb-12">
        <Image
          src="/images/cover.jpg"
          alt="The Valve Wire Weekly Podcast"
          width={200}
          height={200}
          className="rounded-2xl shadow-xl"
        />
        <div>
          <p className="nav-font text-xs font-semibold uppercase tracking-widest text-[var(--color-rose)] mb-2">
            Podcast
          </p>
          <h1 className="text-3xl font-bold text-[var(--color-wine)] mb-3">
            The Valve Wire Weekly
          </h1>
          <p className="text-gray-600 leading-relaxed mb-4">
            A weekly podcast covering structural heart disease —
            surgical and transcatheter valve therapies, clinical trials,
            and industry analysis. Balanced, evidence-based analysis with expert
            skepticism.
          </p>
          <div className="nav-font flex flex-wrap gap-3">
            <a
              href="/podcast/feed.xml"
              className="inline-flex items-center gap-2 bg-[var(--color-rose)] text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-[var(--color-burgundy)] transition-colors"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6.18 15.64a2.18 2.18 0 010 4.36 2.18 2.18 0 010-4.36M4 4.44A15.56 15.56 0 0119.56 20h-2.83A12.73 12.73 0 004 7.27V4.44m0 5.66a9.9 9.9 0 019.9 9.9h-2.83A7.07 7.07 0 004 12.93v-2.83z" />
              </svg>
              RSS Feed
            </a>
          </div>
        </div>
      </div>

      {/* Episodes */}
      <div>
        <h2 className="nav-font text-xl font-medium text-[var(--color-burgundy)] mb-6">
          All Episodes ({episodes.length})
        </h2>

        <div className="space-y-4">
          {episodes.map((episode, i) => (
            <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-100 p-6">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-bold text-[var(--color-wine)] text-lg">{episode.title}</h3>
                  <p className="nav-font text-xs text-gray-400 mt-1">
                    {episode.date} · {episode.duration}
                  </p>
                </div>
              </div>

              <p className="text-sm text-gray-600 leading-relaxed mb-4">{episode.show_notes}</p>

              {episode.mp3_url && (
                <audio controls className="w-full" preload="none">
                  <source src={episode.mp3_url} type="audio/mpeg" />
                </audio>
              )}
            </div>
          ))}
        </div>

        {episodes.length === 0 && (
          <p className="text-center text-gray-400 py-12">No episodes yet.</p>
        )}
      </div>
    </div>
  );
}
