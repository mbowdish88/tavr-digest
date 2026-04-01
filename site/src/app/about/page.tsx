import type { Metadata } from "next";
import Image from "next/image";

export const metadata: Metadata = {
  title: "About",
  description:
    "The Valve Wire is a platform for dissemination of both transcatheter and surgical therapies for structural heart disease.",
};

export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      {/* Header */}
      <div className="text-center mb-10">
        <Image
          src="/images/cover.jpg"
          alt="The Valve Wire"
          width={120}
          height={120}
          className="rounded-xl mx-auto mb-6 shadow-lg"
        />
        <h1 className="text-3xl font-bold text-[var(--color-wine)] mb-2">
          About The Valve Wire
        </h1>
        <p className="nav-font text-sm text-[var(--color-rose)] uppercase tracking-widest">
          Structural Heart Disease
        </p>
      </div>

      {/* Mission */}
      <section className="mb-10">
        <h2 className="nav-font text-xl font-medium text-[var(--color-burgundy)] mb-3">
          Our Mission
        </h2>
        <p className="leading-relaxed mb-4">
          The Valve Wire provides daily, balanced analysis of transcatheter valve
          technology — covering aortic (TAVR/TAVI), mitral (MitraClip, PASCAL, TMVR),
          and tricuspid (TriClip, TTVR) therapies. We aggregate research from academic,
          regulatory, financial, and social sources, then synthesize it into an
          accessible daily digest.
        </p>
        <p className="leading-relaxed">
          Our audience includes cardiac surgeons, interventional cardiologists,
          trainees, informed patients, industry stakeholders, and regulatory
          agencies. Whether you are in the cath lab, the OR, the boardroom, or
          the waiting room, The Valve Wire keeps you informed.
        </p>
      </section>

      {/* Editorial Stance */}
      <section className="mb-10">
        <h2 className="nav-font text-xl font-medium text-[var(--color-burgundy)] mb-3">
          Editorial Stance
        </h2>
        <div className="bg-[var(--color-cream)] border-l-4 border-[var(--color-rose)] rounded-r-lg p-5">
          <p className="leading-relaxed mb-3">
            Many structural heart technologies have gotten ahead of the science
            and clinical guidelines. We are committed to presenting{" "}
            <strong>balanced, circumspect analysis</strong>:
          </p>
          <ul className="space-y-2 text-sm">
            <li className="flex gap-2">
              <span className="text-[var(--color-rose)]">•</span>
              We always present competing arguments for and against favorable findings
            </li>
            <li className="flex gap-2">
              <span className="text-[var(--color-rose)]">•</span>
              We flag study limitations: non-randomized designs, industry sponsorship,
              short follow-up, small samples
            </li>
            <li className="flex gap-2">
              <span className="text-[var(--color-rose)]">•</span>
              When reporting favorable transcatheter outcomes, we note durability
              concerns, patient selection biases, and surgical alternatives
            </li>
            <li className="flex gap-2">
              <span className="text-[var(--color-rose)]">•</span>
              Our tone is expert skepticism — enthusiastic about real advances but
              always questioning
            </li>
          </ul>
        </div>
      </section>

      {/* AI Disclosure */}
      <section className="mb-10">
        <h2 className="nav-font text-xl font-medium text-[var(--color-burgundy)] mb-3">
          AI Disclosure
        </h2>
        <p className="leading-relaxed mb-4">
          The Valve Wire uses artificial intelligence to aggregate and synthesize
          content from peer-reviewed journals, regulatory databases, clinical
          trial registries, financial data, and news sources. The daily digest
          and weekly podcast are AI-generated using Claude (Anthropic) for text
          synthesis and editorial analysis.
        </p>
        <p className="leading-relaxed">
          While we strive for accuracy and balance, AI-synthesized content should
          not be considered medical advice. Always consult primary sources and
          clinical guidelines for patient care decisions.
        </p>
      </section>

      {/* Contact */}
      <section>
        <h2 className="nav-font text-xl font-medium text-[var(--color-burgundy)] mb-3">
          Contact
        </h2>
        <p className="leading-relaxed">
          Questions, corrections, or feedback? Reach us at{" "}
          <a
            href="mailto:nolan.beckett@pm.me"
            className="text-[var(--color-rose)] hover:underline"
          >
            nolan.beckett@pm.me
          </a>
        </p>
      </section>
    </div>
  );
}
