import Link from "next/link";

const SECTIONS = [
  { label: "Aortic", href: "/#aortic" },
  { label: "Mitral", href: "/#mitral" },
  { label: "Tricuspid", href: "/#tricuspid" },
  { label: "Surgical vs Transcatheter", href: "/#surgical" },
  { label: "Industry", href: "/#financial" },
  { label: "Trials", href: "/#trials" },
];

const ABOUT = [
  { label: "Editorial Stance", href: "/about" },
  { label: "Methodology", href: "/about#methodology" },
  { label: "Editor", href: "/about#editor" },
  { label: "Contact", href: "mailto:nolan.beckett@pm.me" },
];

const ARCHIVE = [
  { label: "By Date", href: "/archive" },
  { label: "By Topic", href: "/archive" },
  { label: "By Journal", href: "/archive" },
];

const LISTEN = [
  { label: "Podcast", href: "/podcast" },
  { label: "RSS Feed", href: "/podcast/feed.xml" },
  { label: "Apple Podcasts", href: "#" },
  { label: "Spotify", href: "#" },
];

function FooterCol({ label, links }: { label: string; links: { label: string; href: string }[] }) {
  return (
    <div className="footer-col">
      <div className="footer-col-label">{label}</div>
      <ul>
        {links.map((link) => (
          <li key={link.label}>
            <Link href={link.href}>{link.label}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function FooterRedesign() {
  const year = new Date().getFullYear();

  return (
    <footer className="footer-redesign">
      <div className="container">
        <div className="footer-grid">
          <div className="footer-brand">
            <div className="footer-wordmark">
              The Valve
              <span className="wire">— W I R E —</span>
            </div>
            <p>
              A surgeon&rsquo;s reading of structural heart disease, written from inside the
              AATS room and intended for everyone the field touches.
            </p>
          </div>
          <FooterCol label="Sections" links={SECTIONS} />
          <FooterCol label="About" links={ABOUT} />
          <FooterCol label="Archive" links={ARCHIVE} />
          <FooterCol label="Listen" links={LISTEN} />
        </div>
        <div className="footer-bottom">
          <div className="colophon">
            <strong>Founded April 2026 · Edited from Los Angeles.</strong>{" "}
            Independent. No industry funding since issue one. Set in Big Shoulders
            Display, Fraunces, and Space Grotesk.
          </div>
          <div className="right">
            © {year} The Valve Wire
          </div>
        </div>
      </div>
    </footer>
  );
}
