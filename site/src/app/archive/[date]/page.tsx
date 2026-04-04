import type { Metadata } from "next";
import { getDigestByDate, getAllDigestDates, formatDate } from "@/lib/data";
import Link from "next/link";
import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ date: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { date } = await params;
  const digest = getDigestByDate(date);
  if (!digest) {
    return { title: "Not Found | The Valve Wire" };
  }
  return {
    title: `${formatDate(date)} | The Valve Wire`,
    description: `The Valve Wire daily digest for ${formatDate(date)}.`,
  };
}

export default async function ArchiveDayPage({ params }: PageProps) {
  const { date } = await params;
  const digest = getDigestByDate(date);

  if (!digest) {
    notFound();
  }

  const allDates = getAllDigestDates();
  const currentIndex = allDates.indexOf(date);
  const prevDate = currentIndex < allDates.length - 1 ? allDates[currentIndex + 1] : null;
  const nextDate = currentIndex > 0 ? allDates[currentIndex - 1] : null;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const html: string = (digest as any).digest_html as string || "";

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8 pb-6 border-b border-gray-200">
        <p className="nav-font text-xs font-semibold uppercase tracking-widest text-[var(--color-rose)] mb-2">
          Daily Digest
        </p>
        <h1 className="text-3xl font-bold text-[var(--color-wine)] mb-1">
          The Valve Wire
        </h1>
        <p className="text-gray-500 text-sm nav-font">{formatDate(date)}</p>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex gap-4">
            <Link href="/archive" className="nav-font text-xs text-[var(--color-rose)] hover:underline">
              ← Archive
            </Link>
            <Link href="/" className="nav-font text-xs text-[var(--color-rose)] hover:underline">
              Today&apos;s digest
            </Link>
          </div>
          <div className="flex gap-4">
            {prevDate && (
              <Link
                href={`/archive/${prevDate}`}
                className="nav-font text-xs text-gray-500 hover:text-[var(--color-rose)] transition-colors"
              >
                ← {new Date(prevDate + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })}
              </Link>
            )}
            {nextDate && (
              <Link
                href={`/archive/${nextDate}`}
                className="nav-font text-xs text-gray-500 hover:text-[var(--color-rose)] transition-colors"
              >
                {new Date(nextDate + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })} →
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Full newsletter HTML */}
      {html ? (
        <div
          className="weekly-content prose max-w-none"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      ) : (
        <div className="text-center py-16 text-gray-400 nav-font text-sm">
          <p>Newsletter HTML is not available for this date.</p>
          <Link href="/archive" className="mt-4 inline-block text-[var(--color-rose)] hover:underline">
            ← Back to archive
          </Link>
        </div>
      )}

      {/* Footer nav */}
      <div className="mt-12 pt-8 border-t border-gray-200 flex items-center justify-between nav-font text-xs text-gray-400">
        <div>
          {prevDate && (
            <Link
              href={`/archive/${prevDate}`}
              className="hover:text-[var(--color-rose)] transition-colors"
            >
              ← {new Date(prevDate + "T12:00:00").toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
            </Link>
          )}
        </div>
        <Link href="/archive" className="hover:text-[var(--color-rose)] transition-colors">
          Archive
        </Link>
        <div>
          {nextDate && (
            <Link
              href={`/archive/${nextDate}`}
              className="hover:text-[var(--color-rose)] transition-colors"
            >
              {new Date(nextDate + "T12:00:00").toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })} →
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
