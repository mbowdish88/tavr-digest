import type { Metadata } from "next";
import { getLatestDigest, getAllHistoricalArticles, getAllDigestDates } from "@/lib/data";
import ArchiveClient from "./ArchiveClient";

export const metadata: Metadata = {
  title: "Archive",
  description: "Browse all Valve Wire digest articles — searchable by topic, date, and source.",
};

export const dynamic = "force-dynamic";

export default function ArchivePage() {
  const data = getLatestDigest();
  const allArticles = getAllHistoricalArticles();
  const dates = getAllDigestDates();
  return <ArchiveClient data={data} allArticles={allArticles} dates={dates} />;
}
