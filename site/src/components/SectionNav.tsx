import Link from "next/link";

const SECTIONS = [
  { label: "Today", href: "/", active: true },
  { label: "Aortic", href: "/#aortic" },
  { label: "Mitral", href: "/#mitral" },
  { label: "Tricuspid", href: "/#tricuspid" },
  { label: "Surgical vs Transcatheter", href: "/#surgical" },
  { label: "Industry", href: "/#financial" },
  { label: "Trials", href: "/#trials" },
  { label: "Editorial", href: "/about" },
  { label: "Archive", href: "/archive" },
  { label: "Podcast", href: "/podcast" },
];

export default function SectionNav() {
  return (
    <div className="section-nav">
      <div className="container">
        <nav className="section-nav-inner">
          {SECTIONS.map((section) => (
            <Link
              key={section.href}
              href={section.href}
              className={section.active ? "active" : ""}
            >
              {section.label}
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
}
