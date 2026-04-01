import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-[#1B2A4A] text-[#A0AEC0] nav-font">
      <div className="max-w-7xl mx-auto px-4 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-2">
            <h3 className="text-white text-lg font-bold mb-2">The Valve Wire</h3>
            <p className="text-sm leading-relaxed max-w-md">
              A platform for dissemination of both transcatheter and surgical
              therapies for structural heart disease. Balanced, evidence-based
              research, trials, regulation, and market analysis — daily.
            </p>
            <p className="text-xs mt-4 text-gray-600">
              AI-synthesized content. Expert analysis, not medical advice.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-3">Navigate</h4>
            <ul className="space-y-1.5 text-sm">
              <li><Link href="/" className="hover:text-[#63B3ED] transition-colors">Today&apos;s Digest</Link></li>
              <li><Link href="/archive" className="hover:text-[#63B3ED] transition-colors">Archive</Link></li>
              <li><Link href="/podcast" className="hover:text-[#63B3ED] transition-colors">Podcast</Link></li>
              <li><Link href="/about" className="hover:text-[#63B3ED] transition-colors">About</Link></li>
            </ul>
          </div>

          {/* Topics */}
          <div>
            <h4 className="text-white font-semibold text-sm mb-3">Topics</h4>
            <ul className="space-y-1.5 text-sm">
              <li><Link href="/#aortic" className="hover:text-[#63B3ED] transition-colors">Aortic (TAVR)</Link></li>
              <li><Link href="/#mitral" className="hover:text-[#63B3ED] transition-colors">Mitral Valve</Link></li>
              <li><Link href="/#tricuspid" className="hover:text-[#63B3ED] transition-colors">Tricuspid Valve</Link></li>
              <li><Link href="/#surgical" className="hover:text-[#63B3ED] transition-colors">Surgical vs Transcatheter</Link></li>
              <li><Link href="/#trials" className="hover:text-[#63B3ED] transition-colors">Clinical Trials</Link></li>
              <li><Link href="/#regulatory" className="hover:text-[#63B3ED] transition-colors">Regulatory</Link></li>
              <li><Link href="/#financial" className="hover:text-[#63B3ED] transition-colors">Market & Finance</Link></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-300 mt-8 pt-6 flex flex-col md:flex-row justify-between items-center gap-2 text-xs">
          <p>&copy; {new Date().getFullYear()} The Valve Wire. All rights reserved.</p>
          <p>
            <a href="mailto:nolan.beckett@pm.me" className="hover:text-[#63B3ED] transition-colors">
              nolan.beckett@pm.me
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}
