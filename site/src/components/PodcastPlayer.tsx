"use client";

import type { PodcastEpisode } from "@/lib/data";

interface PodcastPlayerProps {
  episode: PodcastEpisode;
}

export default function PodcastPlayer({ episode }: PodcastPlayerProps) {
  return (
    <div className="bg-[#D8D8D8] rounded-lg p-5 text-[#1B2A4A]">
      <div className="flex items-start gap-4">
        <div className="w-16 h-16 rounded-lg overflow-hidden shrink-0">
          <img src="/images/cover.jpg" alt="Podcast" className="w-full h-full object-cover" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="nav-font text-xs text-[#2C5282] font-semibold uppercase tracking-wider mb-1">
            Latest Episode
          </p>
          <h3 className="font-bold text-sm leading-snug mb-1 truncate">{episode.title}</h3>
          <p className="text-xs text-[#4A5568]">
            {episode.date} · {episode.duration}
          </p>
        </div>
      </div>

      <audio controls className="w-full mt-4 h-8" preload="none">
        <source src={`/api/podcast/${episode.date}`} type="audio/mpeg" />
      </audio>

      <p className="text-xs text-[#4A5568] mt-3 leading-relaxed line-clamp-2">
        {episode.show_notes}
      </p>
    </div>
  );
}
