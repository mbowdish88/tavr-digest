import Image from "next/image";

interface HeroBannerProps {
  date: string;
  articleCount: number;
}

export default function HeroBanner({ date, articleCount }: HeroBannerProps) {
  return (
    <div className="relative bg-[#EDF2F7] overflow-hidden">
      {/* Thumbnail banner artwork — right side */}
      <div className="absolute right-0 top-0 bottom-0 w-1/2 pointer-events-none select-none opacity-100 hidden md:block">
        <Image
          src="/images/banner.jpg"
          alt=""
          fill
          className="object-contain object-right"
          priority
        />
      </div>

      {/* Content */}
      <div className="relative max-w-7xl mx-auto px-4 py-6 md:py-8">
        <div className="max-w-2xl">
          <p className="nav-font text-sm md:text-base font-semibold uppercase tracking-widest text-[#2C5282] mb-1">
            Daily Digest
          </p>
          <h2 className="text-lg md:text-xl font-semibold text-[var(--color-wine)] mb-1">
            {date}
          </h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            {articleCount} articles covering surgical and transcatheter valve therapies, trials, regulation, and market analysis.
          </p>

          {/* Section pills */}
          <div className="flex flex-wrap gap-1.5 sm:gap-2 mt-3 sm:mt-4 nav-font text-[10px] sm:text-xs font-semibold items-center">
            <a href="#aortic" className="px-3 py-1.5 rounded-full bg-[#C4787A] text-white shadow-sm hover:opacity-80 transition-opacity">Aortic</a>
            <a href="#mitral" className="px-3 py-1.5 rounded-full bg-[#8B5E6B] text-white shadow-sm hover:opacity-80 transition-opacity">Mitral</a>
            <a href="#tricuspid" className="px-3 py-1.5 rounded-full bg-[#4A7B8B] text-white shadow-sm hover:opacity-80 transition-opacity">Tricuspid</a>
            <a href="#surgical" className="px-3 py-1.5 rounded-full bg-[#5B6B7B] text-white shadow-sm hover:opacity-80 transition-opacity">Surgical vs Transcatheter</a>
            <a href="#trials" className="px-3 py-1.5 rounded-full bg-[#7B5B8B] text-white shadow-sm hover:opacity-80 transition-opacity">Trials</a>
            <a href="#regulatory" className="px-3 py-1.5 rounded-full bg-[#3B7B5B] text-white shadow-sm hover:opacity-80 transition-opacity">Regulatory</a>
            <a href="#financial" className="px-3 py-1.5 rounded-full bg-[#8B7B3B] text-white shadow-sm hover:opacity-80 transition-opacity">Financial</a>
          </div>
        </div>
      </div>

      {/* Gold accent line */}
      <div className="h-1 bg-gradient-to-r from-[var(--color-rose)] via-[var(--color-beige)] to-[var(--color-rose)]" />
    </div>
  );
}
