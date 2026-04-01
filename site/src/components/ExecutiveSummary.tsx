interface ExecutiveSummaryProps {
  summary: string;
}

export default function ExecutiveSummary({ summary }: ExecutiveSummaryProps) {
  if (!summary) return null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-8">
      <h2 className="nav-font text-base font-bold uppercase tracking-wider text-[var(--color-burgundy)] mb-3">
        Executive Summary
      </h2>
      <p
        className="text-base leading-relaxed text-[var(--color-wine)] [&_a]:text-[var(--color-burgundy)] [&_a]:underline [&_a]:hover:opacity-80"
        dangerouslySetInnerHTML={{ __html: summary }}
      />
    </div>
  );
}
