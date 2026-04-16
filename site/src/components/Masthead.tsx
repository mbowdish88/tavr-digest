import Link from "next/link";
import Image from "next/image";

const NAV_ITEMS = [
  { label: "Search", href: "/archive" },
  { label: "Methodology", href: "/about#methodology" },
  { label: "About", href: "/about" },
];

export default function Masthead() {
  const today = new Date();
  const dateStr = today.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <header className="masthead">
      <div className="container">
        <div className="masthead-inner">
          <div className="mast-left">
            <Link href="/" className="mast-seal">
              <Image
                src="/images/cover.jpg"
                alt="The Valve Wire seal"
                width={92}
                height={92}
                priority
              />
            </Link>
            <div className="mast-wordmark-block">
              <Link href="/" className="mast-wordmark">
                The Valve
                <span className="wire">— W I R E —</span>
              </Link>
            </div>
            <div className="mast-tagline">
              A surgeon&rsquo;s reading of structural heart disease
            </div>
          </div>
          <div className="mast-right">
            <div className="mast-meta">
              {dateStr}
              <span className="meta-line">E. Nolan Beckett, MD · Editor</span>
            </div>
            <nav className="mast-nav">
              {NAV_ITEMS.map((item) => (
                <Link key={item.href} href={item.href}>
                  {item.label}
                </Link>
              ))}
              <Link href="#subscribe" className="subscribe-cta">
                Subscribe
              </Link>
            </nav>
          </div>
        </div>
      </div>
    </header>
  );
}
