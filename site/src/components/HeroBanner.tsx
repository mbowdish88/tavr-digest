import Image from "next/image";

interface HeroBannerProps {
  date: string;
  articleCount: number;
}

export default function HeroBanner({ date, articleCount }: HeroBannerProps) {
  return (
    <div className="relative bg-[#1B2A4A] overflow-hidden">
      {/* Blue Figures banner artwork — right side */}
      <div className="absolute right-0 top-0 bottom-0 w-1/2 pointer-events-none select-none opacity-100 hidden md:block">
        <Image
          src="/images/banner-blue.jpg"
          alt=""
          fill
          className="object-contain object-right"
          priority
        />
      </div>

      {/* Content */}
      <div className="relative max-w-7xl mx-auto px-4 py-6 md:py-8">
        <div className="max-w-2xl">
          <p className="nav-font text-sm md:text-base font-semibold uppercase tracking-widest text-[#EDE0C4]/80 mb-1">
            Daily Digest
          </p>
          <h2 className="text-lg md:text-xl font-semibold text-white mb-1">
            {date}
          </h2>
          <p className="text-[#EDE0C4]/70 text-sm leading-relaxed">
            {articleCount} articles covering surgical and transcatheter valve therapies, trials, regulation, and market analysis.
          </p>

          {/* Section pills — blue palette */}
          <div className="flex flex-wrap gap-1.5 sm:gap-2 mt-3 sm:mt-4 nav-font text-[10px] sm:text-xs font-semibold items-center">
            <a href="#aortic" className="px-3 py-1.5 rounded-full bg-[#5B7FA6] text-white shadow-sm hover:bg-[#3D5873] transition-colors">Aortic</a>
            <a href="#mitral" className="px-3 py-1.5 rounded-full bg-[#4A6B8A] text-white shadow-sm hover:bg-[#3D5873] transition-colors">Mitral</a>
            <a href="#tricuspid" className="px-3 py-1.5 rounded-full bg-[#3D5873] text-white shadow-sm hover:bg-[#2C4460] transition-colors">Tricuspid</a>
            <a href="#surgical" className="px-3 py-1.5 rounded-full bg-[#5B6B7B] text-white shadow-sm hover:bg-[#4A5A6A] transition-colors">Surgical vs Transcatheter</a>
            <a href="#trials" className="px-3 py-1.5 rounded-full bg-[#4A7B8B] text-white shadow-sm hover:bg-[#3A6A7A] transition-colors">Trials</a>
            <a href="#regulatory" className="px-3 py-1.5 rounded-full bg-[#3B7B5B] text-white shadow-sm hover:bg-[#2A6A4A] transition-colors">Regulatory</a>
            <a href="#financial" className="px-3 py-1.5 rounded-full bg-[#7B6B3B] text-white shadow-sm hover:bg-[#6A5A2A] transition-colors">Financial</a>
          </div>
        </div>
      </div>

      {/* Steel blue accent line */}
      <div className="h-1 bg-gradient-to-r from-[#3D5873] via-[#5B7FA6] to-[#3D5873]" />
    </div>
  );
}
