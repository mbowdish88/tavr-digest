interface KeyPointsProps {
  points: string[];
}

export default function KeyPoints({ points }: KeyPointsProps) {
  if (!points.length) return null;

  return (
    <div className="bg-[var(--color-cream)] border-l-4 border-[var(--color-rose)] rounded-r-lg p-5 mb-8">
      <h2 className="nav-font text-base font-bold uppercase tracking-wider text-[var(--color-burgundy)] mb-3">
        Key Points
      </h2>
      <ul className="space-y-2">
        {points.map((point, i) => (
          <li key={i} className="flex gap-3 text-base leading-relaxed text-[var(--color-wine)]">
            <span className="text-[var(--color-rose)] font-bold mt-0.5">•</span>
            <span
              className="[&_a]:text-[var(--color-burgundy)] [&_a]:underline [&_a]:hover:opacity-80"
              dangerouslySetInnerHTML={{ __html: point }}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}
