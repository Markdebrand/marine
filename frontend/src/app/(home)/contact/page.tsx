"use client";
import { useState } from "react";
import { Mail, MapPin, Phone } from "lucide-react";

type ContactValues = {
  name: string;
  phone: string;
  email: string;
  company: string;
  subject: string;
  message: string;
};

type ContactErrors = Partial<Record<keyof ContactValues, string>>;

function validate(values: ContactValues): ContactErrors {
  const errors: ContactErrors = {};
  // Name: required, 2+ chars, letters/spaces/hyphens/apostrophes allowed
  const name = values.name.trim();
  if (!name) errors.name = "El nombre es obligatorio";
  else if (name.length < 2) errors.name = "El nombre debe tener al menos 2 caracteres";
  else if (!/^[A-Za-zÀ-ÿ'\-\s]+$/.test(name)) errors.name = "Usa solo letras, espacios, guiones y apóstrofes";

  // Email: required + basic format
  const email = values.email.trim();
  if (!email) errors.email = "El correo es obligatorio";
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = "Correo inválido";

  // Phone: optional, but if present must be a plausible international format
  const phone = values.phone.trim();
  if (phone) {
    // Allow +, digits, spaces, parentheses, dots and dashes; length 7-20
    if (!/^\+?[0-9\s().-]{7,20}$/.test(phone)) errors.phone = "Teléfono inválido (usa formato internacional, ej. +1 555 123 4567)";
  }

  // Company: optional, 2+ chars if present
  const company = values.company.trim();
  if (company && company.length < 2) errors.company = "El nombre de la empresa debe tener al menos 2 caracteres";

  // Subject and message already have required in markup; keep browser validation for them
  return errors;
}

export default function ContactPage() {
  const [values, setValues] = useState<ContactValues>({
    name: "",
    phone: "",
    email: "",
    company: "",
    subject: "",
    message: "",
  });
  const [errors, setErrors] = useState<ContactErrors>({});
  const [submitted, setSubmitted] = useState(false);

  const onChange = (field: keyof ContactValues) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const next = { ...values, [field]: e.target.value } as ContactValues;
    setValues(next);
    // live-validate only edited field for quick feedback
    const fieldErrors = validate(next);
    setErrors((prev) => ({ ...prev, [field]: fieldErrors[field] }));
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const vErrors = validate(values);
    setErrors(vErrors);
    if (Object.keys(vErrors).length > 0) return;
    setSubmitted(true);
    // TODO: wire to backend submission if required
    // For now just log; keep UI responsive
    // console.log("Contact form submitted", values);
  };

  return (
    <section className="container mx-auto px-6 sm:px-8 lg:px-12 py-12">
      <div className="grid gap-8 lg:gap-10 md:grid-cols-2">
  {/* Form */}
  <div className="glass-card red-glow p-6 sm:p-8">
          <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-slate-900">Contact Us</h1>
          <p className="mt-2 text-slate-600 text-sm">Fields marked with <span className="text-red-600">*</span> are required.</p>

          <form className="mt-6 grid gap-5" onSubmit={onSubmit} noValidate>
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-slate-700">Your Name <span className="text-red-600">*</span></label>
              <input
                id="name"
                name="name"
                placeholder="Your Name"
                className={`mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${errors.name ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-red-500'}`}
                value={values.name}
                onChange={onChange('name')}
                autoComplete="name"
                aria-invalid={!!errors.name}
                aria-describedby={errors.name ? 'name-error' : undefined}
                required
              />
              {errors.name && <p id="name-error" className="mt-1 text-xs text-red-600">{errors.name}</p>}
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-slate-700">Phone Number</label>
              <input
                id="phone"
                name="phone"
                placeholder="+58"
                className={`mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${errors.phone ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-red-500'}`}
                value={values.phone}
                onChange={onChange('phone')}
                inputMode="tel"
                aria-invalid={!!errors.phone}
                aria-describedby={errors.phone ? 'phone-error' : undefined}
              />
              {errors.phone && <p id="phone-error" className="mt-1 text-xs text-red-600">{errors.phone}</p>}
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700">Your Email <span className="text-red-600">*</span></label>
              <input
                id="email"
                type="email"
                name="email"
                placeholder="you@company.com"
                className={`mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${errors.email ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-red-500'}`}
                value={values.email}
                onChange={onChange('email')}
                autoComplete="email"
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? 'email-error' : undefined}
                required
              />
              {errors.email && <p id="email-error" className="mt-1 text-xs text-red-600">{errors.email}</p>}
            </div>

            <div>
              <label htmlFor="company" className="block text-sm font-medium text-slate-700">Your Company</label>
              <input
                id="company"
                name="company"
                placeholder="Company name"
                className={`mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${errors.company ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-red-500'}`}
                value={values.company}
                onChange={onChange('company')}
                autoComplete="organization"
                aria-invalid={!!errors.company}
                aria-describedby={errors.company ? 'company-error' : undefined}
              />
              {errors.company && <p id="company-error" className="mt-1 text-xs text-red-600">{errors.company}</p>}
            </div>

            <div>
              <label htmlFor="subject" className="block text-sm font-medium text-slate-700">Subject <span className="text-red-600">*</span></label>
              <input
                id="subject"
                name="subject"
                placeholder="How can we help?"
                className="mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 ring-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500"
                value={values.subject}
                onChange={onChange('subject')}
                required
              />
            </div>

            <div>
              <label htmlFor="message" className="block text-sm font-medium text-slate-700">Your Question <span className="text-red-600">*</span></label>
              <textarea
                id="message"
                name="message"
                placeholder="Tell us a bit more…"
                className="mt-2 w-full min-h-32 rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 ring-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500"
                value={values.message}
                onChange={onChange('message')}
                required
              />
            </div>

            {submitted && (
              <div className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md px-3 py-2">
                ¡Gracias! Hemos recibido tu mensaje.
              </div>
            )}

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
