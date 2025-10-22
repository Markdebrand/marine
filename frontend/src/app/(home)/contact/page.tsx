import { Mail, MapPin, Phone } from "lucide-react";

export default function ContactPage() {
  return (
    <section className="container mx-auto px-6 sm:px-8 lg:px-12 py-12">
      <div className="grid gap-8 lg:gap-10 md:grid-cols-2">
  {/* Form */}
  <div className="glass-card red-glow p-6 sm:p-8">
          <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-slate-900">Contact Us</h1>
          <p className="mt-2 text-slate-600 text-sm">Fields marked with <span className="text-red-600">*</span> are required.</p>

          <form className="mt-6 grid gap-5">
            <div>
              <label className="block text-sm font-medium text-slate-700">Your Name <span className="text-red-600">*</span></label>
              <input required name="name" placeholder="Your Name" className="mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 ring-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Phone Number</label>
              <input name="phone" placeholder="+58" className="mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 ring-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Your Email <span className="text-red-600">*</span></label>
              <input required type="email" name="email" placeholder="you@company.com" className="mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 ring-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Your Company</label>
              <input name="company" placeholder="Company name" className="mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 ring-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Subject <span className="text-red-600">*</span></label>
              <input required name="subject" placeholder="How can we help?" className="mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 ring-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500" />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Your Question <span className="text-red-600">*</span></label>
              <textarea required name="message" placeholder="Tell us a bit more…" className="mt-2 w-full min-h-32 rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 ring-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500" />
            </div>

            <div>
              <button type="submit" className="inline-flex items-center rounded-xl bg-red-600 px-6 py-3 text-white text-base font-medium hover:bg-red-700 btn-red-glow">
                Submit
              </button>
            </div>
          </form>
        </div>

  {/* Contact information */}
        <div className="glass-card p-6 sm:p-8">
          <h2 className="text-xl sm:text-2xl font-semibold text-slate-900 text-center">HSO Marine</h2>
          <ul className="mt-6 space-y-5 text-slate-700">
            <li className="flex items-start gap-3">
              <MapPin className="mt-0.5 h-5 w-5 text-red-600" />
              <div>
                <div className="font-medium">Huron Smith Oil Co &amp; HSO Petroleum Services</div>
                <div className="text-sm text-slate-600">204 Hays St, Batesville, Mississippi, 38606</div>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <MapPin className="mt-0.5 h-5 w-5 text-red-600" />
              <div>
                <div className="font-medium">Huron Smith Oil Co &amp; HSO Petroleum Services</div>
                <div className="text-sm text-slate-600">110 East Broward Blvd., Suite 1700, Fort Lauderdale, Florida 33301</div>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <MapPin className="mt-0.5 h-5 w-5 text-red-600" />
              <div>
                <div className="font-medium">Huron Smith Oil S.A</div>
                <div className="text-sm text-slate-600">10th Floor, Banistmo Tower, Aquilino de la Guardia St., Marbella, Panama City</div>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <MapPin className="mt-0.5 h-5 w-5 text-red-600" />
              <div>
                <div className="font-medium">Huron Smith Oil S.A.S</div>
                <div className="text-sm text-slate-600">06th Floor Torre Proteccion, Carrera 43a # 1-650, 6th floor, office 652, Medellin, MEDELLIN 050021</div>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <Phone className="mt-0.5 h-5 w-5 text-red-600" />
              <div className="text-sm text-slate-700">+1 (662) 563-9786</div>
            </li>
            <li className="flex items-start gap-3">
              <Mail className="mt-0.5 h-5 w-5 text-red-600" />
              <div className="text-sm text-slate-700">support@hsomarine.com</div>
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}
