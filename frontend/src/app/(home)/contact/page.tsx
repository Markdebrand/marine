"use client";
import { useState } from 'react';
import { Mail, MapPin, Phone } from "lucide-react";

type Values = {
  name: string;
  phone: string;
  email: string;
  company: string;
  subject: string;
  message: string;
};

type Errors = Partial<Record<keyof Values, string>>;

function validate(values: Values): Errors {
  const errs: Errors = {};
  const name = values.name.trim();
  if (!name) errs.name = 'El nombre es obligatorio';
  else if (name.length < 2) errs.name = 'El nombre debe tener al menos 2 caracteres';
  else if (!/^[\p{L}\s]+$/u.test(name)) errs.name = 'Usa solo letras y espacios (sin números ni símbolos)';

  const email = values.email.trim();
  if (!email) errs.email = 'El correo es obligatorio';
  else if (!/^[A-Za-z0-9.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email)) errs.email = 'Correo inválido. Usa formato nombre@dominio.com';

  const phone = values.phone.trim();
  if (phone && !/^\+?[0-9\s().-]{7,20}$/.test(phone)) errs.phone = 'Teléfono inválido (ej. +1 555 123 4567)';

  const company = values.company.trim();
  if (company && company.length < 2) errs.company = 'El nombre de la empresa debe tener al menos 2 caracteres';

  const subject = values.subject.trim();
  if (!subject) errs.subject = 'El asunto es obligatorio';
  else if (subject.length < 5) errs.subject = 'El asunto debe tener al menos 5 caracteres';

  const message = values.message.trim();
  if (!message) errs.message = 'El mensaje es obligatorio';
  else if (message.length < 10) errs.message = 'El mensaje debe tener al menos 10 caracteres';
  else if (message.length > 2000) errs.message = 'El mensaje es demasiado largo (máx. 2000 caracteres)';

  return errs;
}

export default function ContactPage() {
  const [values, setValues] = useState<Values>({ name: '', phone: '', email: '', company: '', subject: '', message: '' });
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const onChange = (field: keyof Values) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    let raw = e.target.value;
    // For the 'name' and 'company' fields, strip digits so users cannot enter numbers
    // Remove digits and a set of special characters from name and company
    if (field === 'name' || field === 'company') {
      // allow letters and spaces only
      raw = raw.replace(/[^\p{L}\s]/gu, '');
    }
    // For the 'phone' field, remove any letters or invalid characters; allow digits and common separators
    if (field === 'phone') {
      raw = raw.replace(/[^0-9+\s().-]/g, '');
    }
    // For email, remove spaces and forbidden special chars except @ and . and - _
    if (field === 'email') {
      raw = raw.replace(/[^A-Za-z0-9@._-]/g, '');
    }
    const next = { ...values, [field]: raw } as Values;
    setValues(next);
    // live validate only this field
    const fErrs = validate(next);
    setErrors((prev) => ({ ...prev, [field]: fErrs[field] }));
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(null);
    const errs = validate(values);
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;
    setSubmitting(true);

    try {
      // Call backend API
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/contact/simple-submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: values.name,
          email: values.email,
          phone: values.phone || null,
          company: values.company || null,
          subject: values.subject,
          message: values.message,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Failed to send message');
      }

      const data = await response.json();

      setSubmitting(false);
      setSubmitted(true);
      setSuccess('Tu mensaje ha sido enviado correctamente. Nos pondremos en contacto pronto.');
      // reset form
      setValues({ name: '', phone: '', email: '', company: '', subject: '', message: '' });
      setErrors({});
    } catch (error) {
      setSubmitting(false);
      setSuccess(null);
      setErrors({ message: error instanceof Error ? error.message : 'Error al enviar el mensaje. Por favor, intenta de nuevo.' });
    }
  };

  return (
    <section className="container mx-auto px-6 sm:px-8 lg:px-12 py-12">
      <div className="grid gap-8 lg:gap-10 md:grid-cols-2">
        {/* Form */}
        <div className="glass-card red-glow p-6 sm:p-8">
          <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-slate-900">Contact Us</h1>
          <p className="mt-2 text-slate-600 text-sm">Fields marked with <span className="text-red-600">*</span> are required.</p>

          <form className="mt-6 grid gap-5" onSubmit={onSubmit} noValidate onInvalid={(e) => e.preventDefault()}>
            <div>
              <label className="block text-sm font-medium text-slate-700">Your Name <span className="text-red-600">*</span></label>
              <input
                id="name"
                name="name"
                placeholder="Your Name"
                value={values.name}
                onChange={onChange('name')}
                onPaste={(e) => {
                  const paste = (e.clipboardData || (window as any).clipboardData).getData('text');
                  const cleaned = paste.replace(/[0-9]/g, '');
                  e.preventDefault();
                  const next = { ...values, name: (values.name + cleaned).slice(0, 200) } as Values;
                  setValues(next);
                  const fErrs = validate(next);
                  setErrors((prev) => ({ ...prev, name: fErrs.name }));
                }}
                className={`mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${errors.name ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-red-500'}`}
                aria-invalid={!!errors.name}
                aria-describedby={errors.name ? 'name-error' : undefined}
              />
              {errors.name && <p id="name-error" className="text-xs text-red-600 mt-1">{errors.name}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Phone Number</label>
              <input
                id="phone"
                name="phone"
                placeholder="+58"
                value={values.phone}
                onChange={onChange('phone')}
                onPaste={(e) => {
                  const paste = (e.clipboardData || (window as any).clipboardData).getData('text');
                  const cleaned = paste.replace(/[^0-9+\s().-]/g, '');
                  e.preventDefault();
                  const next = { ...values, phone: (values.phone + cleaned).slice(0, 30) } as Values;
                  setValues(next);
                  const fErrs = validate(next);
                  setErrors((prev) => ({ ...prev, phone: fErrs.phone }));
                }}
                className={`mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${errors.phone ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-red-500'}`}
                aria-invalid={!!errors.phone}
                aria-describedby={errors.phone ? 'phone-error' : undefined}
              />
              {errors.phone && <p id="phone-error" className="text-xs text-red-600 mt-1">{errors.phone}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Your Email <span className="text-red-600">*</span></label>
              <input
                id="email"
                type="email"
                name="email"
                placeholder="you@company.com"
                value={values.email}
                onChange={onChange('email')}
                onPaste={(e) => {
                  const paste = (e.clipboardData || (window as any).clipboardData).getData('text');
                  const cleaned = paste.replace(/[^A-Za-z0-9@._-]/g, '');
                  e.preventDefault();
                  const next = { ...values, email: (values.email + cleaned).slice(0, 254) } as Values;
                  setValues(next);
                  const fErrs = validate(next);
                  setErrors((prev) => ({ ...prev, email: fErrs.email }));
                }}
                className={`mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${errors.email ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-red-500'}`}
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? 'email-error' : undefined}
              />
              {errors.email && <p id="email-error" className="text-xs text-red-600 mt-1">{errors.email}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Your Company</label>
              <input
                id="company"
                name="company"
                placeholder="Company name"
                value={values.company}
                onChange={onChange('company')}
                onPaste={(e) => {
                  const paste = (e.clipboardData || (window as any).clipboardData).getData('text');
                  const cleaned = paste.replace(/[0-9]/g, '');
                  e.preventDefault();
                  const next = { ...values, company: (values.company + cleaned).slice(0, 200) } as Values;
                  setValues(next);
                  const fErrs = validate(next);
                  setErrors((prev) => ({ ...prev, company: fErrs.company }));
                }}
                className={`mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${errors.company ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200 focus:ring-red-500'}`}
                aria-invalid={!!errors.company}
                aria-describedby={errors.company ? 'company-error' : undefined}
              />
              {errors.company && <p id="company-error" className="text-xs text-red-600 mt-1">{errors.company}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Subject <span className="text-red-600">*</span></label>
              <input
                id="subject"
                name="subject"
                placeholder="How can we help?"
                value={values.subject}
                maxLength={200}
                onChange={onChange('subject')}
                aria-invalid={!!errors.subject}
                aria-describedby={errors.subject ? 'subject-error' : undefined}
                className={`mt-2 w-full rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${errors.subject ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200'}`}
              />
              {errors.subject && <p id="subject-error" className="text-xs text-red-600 mt-1">{errors.subject}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700">Your Question <span className="text-red-600">*</span></label>
              <textarea
                id="message"
                name="message"
                placeholder="Tell us a bit more…"
                value={values.message}
                maxLength={2000}
                onChange={onChange('message')}
                aria-invalid={!!errors.message}
                aria-describedby={errors.message ? 'message-error' : undefined}
                className={`mt-2 w-full min-h-32 rounded-xl bg-white/70 px-4 py-3 text-slate-900 ring-1 placeholder:text-slate-400 focus:outline-none focus:ring-2 ${errors.message ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-200'}`}
              />
              {errors.message && <p id="message-error" className="text-xs text-red-600 mt-1">{errors.message}</p>}
            </div>

            <div>
              <button type="submit" disabled={submitting} className="inline-flex items-center rounded-xl bg-red-600 px-6 py-3 text-white text-base font-medium hover:bg-red-700 btn-red-glow disabled:opacity-50">
                {submitting ? 'Sending…' : 'Submit'}
              </button>
              {success && (
                <p role="status" aria-live="polite" className="mt-3 text-sm text-green-600">{success}</p>
              )}
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
              <div className="text-sm text-slate-700">info@hsomarine.com</div>
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}
