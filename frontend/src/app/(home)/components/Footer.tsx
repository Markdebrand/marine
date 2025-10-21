"use client";
import Image from "next/image";
import Link from "next/link";

function IconMail(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M2 6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6Zm2 0 8 5 8-5H4Zm16 12V8l-8 5-8-5v10h16Z" />
    </svg>
  );
}

function IconPhone(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M2 3.5A1.5 1.5 0 0 1 3.5 2h2A1.5 1.5 0 0 1 7 3.5V6a1.5 1.5 0 0 1-1 1.414c.27.74.63 1.459 1.08 2.152a17 17 0 0 0 3.354 3.354c.693.45 1.412.81 2.152 1.08A1.5 1.5 0 0 1 14 14h2.5A1.5 1.5 0 0 1 18 15.5v2A1.5 1.5 0 0 1 16.5 19h-1A13.5 13.5 0 0 1 2 5.5v-2Z" />
    </svg>
  );
}

function IconMapPin(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M12 2a7 7 0 0 0-7 7c0 5 7 13 7 13s7-8 7-13a7 7 0 0 0-7-7Zm0 9.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5Z" />
    </svg>
  );
}

function IconArrowUp(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M12 5l6 6-1.41 1.41L13 9.83V20h-2V9.83L7.41 12.4 6 11l6-6Z" />
    </svg>
  );
}

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-24 bg-[#0f172a] text-zinc-300">
      {/* Top content */}
  <div className="container mx-auto px-6 sm:px-8 lg:px-12 py-12 grid gap-10 md:grid-cols-2 lg:grid-cols-4">
        {/* Brand + developed by */}
        <div>
          <Link href="/" className="inline-flex items-center gap-2 rounded-md bg-white/5 px-3 py-2 ring-1 ring-white/10">
            <Image src="/HSO Marine Isotype.svg" alt="HSO Marine" width={28} height={28} className="h-7 w-7" />
            <span className="font-semibold text-white">HSO Marine</span>
          </Link>

          <div className="mt-4 flex items-center gap-3">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-white/5 ring-1 ring-white/10">🏦</span>
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-white/5 ring-1 ring-white/10">🌐</span>
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-white/5 ring-1 ring-white/10">🏠</span>
          </div>

          <div className="mt-6">
            <p className="text-sm text-zinc-400">Developed by</p>
            <div className="mt-2">
              <Image src="/DevelopedMDB.webp" alt="Developed by MDB markdebrand" width={160} height={40} className="h-auto w-[160px]" />
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div>
          <h3 className="text-sm font-semibold tracking-wide text-red-400">NAVIGATION</h3>
          <ul className="mt-4 space-y-3 text-sm">
            <li>
              <Link href="/" className="inline-flex items-center gap-2 hover:text-white">
                <span>🏠</span> Home
              </Link>
            </li>
            <li>
              <Link href="/services" className="inline-flex items-center gap-2 hover:text-white">
                <span>🧰</span> Services
              </Link>
            </li>
            <li>
              <Link href="/contact" className="inline-flex items-center gap-2 hover:text-white">
                <span>✉️</span> Contact Us
              </Link>
            </li>
            <li>
              <Link href="/about" className="inline-flex items-center gap-2 hover:text-white">
                <span>👥</span> About Us
              </Link>
            </li>
          </ul>
        </div>

        {/* Useful Links */}
        <div>
          <h3 className="text-sm font-semibold tracking-wide text-red-400">USEFUL LINKS</h3>
          <ul className="mt-4 space-y-3 text-sm">
            <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
            <li><a href="#" className="hover:text-white">Terms of Service</a></li>
            <li><a href="#" className="hover:text-white">Beta Program Terms</a></li>
            <li><a href="#" className="hover:text-white">Refund and Cancellation Policy</a></li>
            <li><a href="#" className="hover:text-white">Cookie Policy</a></li>
          </ul>
        </div>

        {/* Contact */}
        <div>
          <h3 className="text-sm font-semibold tracking-wide text-red-400">CONTACT</h3>
          <ul className="mt-4 space-y-4 text-sm">
            <li className="flex items-start gap-3">
              <IconMail className="mt-0.5 h-4 w-4 text-zinc-400" />
              <div>
                <a href="mailto:support@hsomarine.com" className="hover:text-white">support@hsomarine.com</a>
                <div className="text-xs text-zinc-500">24/7 Support</div>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <IconPhone className="mt-0.5 h-4 w-4 text-zinc-400" />
              <div>
                <a href="tel:+16625639786" className="hover:text-white">+1 (662) 563-9786</a>
                <div className="text-xs text-zinc-500">Trading Desk</div>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <IconMapPin className="mt-0.5 h-4 w-4 text-zinc-400" />
              <div>
                Miami, FL
                <div className="text-xs text-zinc-500">Business District</div>
              </div>
            </li>
          </ul>
        </div>
      </div>

      {/* Bottom bar */}
  <div className="border-t border-white/10">
  <div className="container mx-auto px-6 sm:px-8 lg:px-12 py-4 text-xs text-zinc-400 flex items-center justify-between">
          <div>Copyright {year} © HSO Marine. All rights reserved.</div>
          <button
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            className="inline-flex h-9 w-9 items-center justify-center rounded-md bg-white/5 ring-1 ring-white/10 text-zinc-300 hover:text-white"
            aria-label="Back to top"
          >
            <IconArrowUp className="h-4 w-4" />
          </button>
        </div>
      </div>
    </footer>
  );
}
