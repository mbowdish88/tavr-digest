import Image from "next/image";

interface HeroBannerProps {
  date: string;
  articleCount: number;
  leadSentence?: string;
}

export default function HeroBanner({ date, articleCount, leadSentence }: HeroBannerProps) {
  return (
    <div className="relative overflow-hidden" style={{ backgroundColor: "var(--color-navy)", minHeight: "280px" }}>
      {/* Background image with dark overlay */}
      <div className="absolute inset-0">
        <Image
          src="/images/banner-blue.jpg"
          alt=""
          fill
          className="object-cover"
          priority
        />
        <div className="absolute inset-0" style={{ backgroundColor: "rgba(27, 42, 74, 0.65)" }} />
      </div>

      {/* Content */}
      <div className="relative max-w-3xl mx-auto px-6 py-14 md:py-20 text-center">
        {/* Date */}
        <h2
          className="leading-tight mb-3"
          style={{
            fontFamily: "var(--font-playfair), 'Playfair Display', Georgia, serif",
            fontSize: "clamp(32px, 6vw, 48px)",
            color: "#F1EDE4",
          }}
        >
          {date}
        </h2>

        {/* Subtitle */}
        <p
          className="nav-font uppercase mb-4"
          style={{
            fontSize: "13px",
            letterSpacing: "0.15em",
            color: "#B8C4D4",
          }}
        >
          The Valve Wire &mdash; Daily Digest
        </p>

        {/* Article count */}
        <p
          className="nav-font mb-4"
          style={{ fontSize: "13px", color: "#B8C4D4" }}
        >
          {articleCount} articles &middot; Structural Heart Disease
        </p>

        {/* Lead sentence */}
        {leadSentence && (
          <p
            className="mx-auto leading-relaxed"
            style={{
              fontFamily: "Georgia, serif",
              fontSize: "18px",
              color: "rgba(241,237,228,0.9)",
              maxWidth: "672px",
              marginTop: "16px",
            }}
          >
            {leadSentence}
          </p>
        )}
      </div>
    </div>
  );
}
