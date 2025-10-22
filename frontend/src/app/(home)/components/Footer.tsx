"use client";
import Image from "next/image";
import Link from "next/link";
import { Mail, Phone, MapPin, ArrowUp, Linkedin, Globe, Home, Layers, Users } from 'lucide-react';

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-24 bg-[#0f172a] text-zinc-300">
      {/* Top content */}
  <div className="container mx-auto px-6 sm:px-8 lg:px-12 py-12 grid gap-10 md:grid-cols-2 lg:grid-cols-4">
        {/* Brand + developed by */}
        <div>
          <Link href="/" className="inline-flex items-center gap-2 rounded-md bg-white/5 px-3 py-2 ring-1 ring-white/10">
            <Image src="/HSOMarineIsotype.svg" alt="HSO Marine" width={28} height={28} className="h-7 w-7" />
            <span className="font-semibold text-white">HSO Marine</span>
          </Link>

          <div className="mt-4 flex items-center gap-3">
            <a href="#" className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-white/5 ring-1 ring-white/10" aria-label="LinkedIn">
              <Linkedin className="h-5 w-5 text-zinc-300" />
            </a>
            <a href="#" className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-white/5 ring-1 ring-white/10" aria-label="Website">
              <Globe className="h-5 w-5 text-zinc-300" />
            </a>
            <a href="/" className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-white/5 ring-1 ring-white/10" aria-label="Home">
              <Home className="h-5 w-5 text-zinc-300" />
            </a>
          </div>

          <div className="mt-6">
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
                <Home className="h-5 w-5 text-zinc-400" /> Home
              </Link>
            </li>
            <li>
              <Link href="/services" className="inline-flex items-center gap-2 hover:text-white">
                <Layers className="h-5 w-5 text-zinc-400" /> Services
              </Link>
            </li>
            <li>
              <Link href="/contact" className="inline-flex items-center gap-2 hover:text-white">
                <Mail className="h-5 w-5 text-zinc-400" /> Contact Us
              </Link>
            </li>
            <li>
              <Link href="/about" className="inline-flex items-center gap-2 hover:text-white">
                <Users className="h-5 w-5 text-zinc-400" /> About Us
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
              <Mail className="mt-0.5 h-4 w-4 text-zinc-400" />
              <div>
                <a href="mailto:support@hsomarine.com" className="hover:text-white">support@hsomarine.com</a>
                <div className="text-xs text-zinc-500">24/7 Support</div>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <Phone className="mt-0.5 h-4 w-4 text-zinc-400" />
              <div>
                <a href="tel:+16625639786" className="hover:text-white">+1 (662) 563-9786</a>
                <div className="text-xs text-zinc-500">Trading Desk</div>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <MapPin className="mt-0.5 h-4 w-4 text-zinc-400" />
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
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
      </div>
    </footer>
  );
}
