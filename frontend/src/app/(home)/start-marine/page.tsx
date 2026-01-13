"use client";
import { useState } from 'react';
import { Check, Phone, Mail } from "lucide-react";
import Image from "next/image";

type Values = {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    company: string;
};

type Errors = Partial<Record<keyof Values, string>>;

function validate(values: Values): Errors {
    const errs: Errors = {};

    const firstName = values.firstName.trim();
    if (!firstName) errs.firstName = 'First name is required';
    else if (firstName.length < 2) errs.firstName = 'First name must be at least 2 characters';

    const lastName = values.lastName.trim();
    if (!lastName) errs.lastName = 'Last name is required';
    else if (lastName.length < 2) errs.lastName = 'Last name must be at least 2 characters';

    const email = values.email.trim();
    if (!email) errs.email = 'Email is required';
    else if (!/^[A-Za-z0-9.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email)) errs.email = 'Invalid email format';

    const phone = values.phone.trim();
    if (!phone) errs.phone = 'Phone number is required';
    else if (!/^\+?[0-9\s().-]{7,20}$/.test(phone)) errs.phone = 'Invalid phone number';

    return errs;
}

export default function StartMarinePage() {
    const [values, setValues] = useState<Values>({ firstName: '', lastName: '', email: '', phone: '', company: '' });
    const [errors, setErrors] = useState<Errors>({});
    const [submitting, setSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);

    const onChange = (field: keyof Values) => (e: React.ChangeEvent<HTMLInputElement>) => {
        let raw = e.target.value;
        if (field === 'firstName' || field === 'lastName' || field === 'company') {
            raw = raw.replace(/[^\p{L}\s]/gu, '');
        }
        if (field === 'phone') {
            raw = raw.replace(/[^0-9+\s().-]/g, '');
        }
        if (field === 'email') {
            raw = raw.replace(/[^A-Za-z0-9@._-]/g, '');
        }
        const next = { ...values, [field]: raw } as Values;
        setValues(next);
        const fErrs = validate(next);
        setErrors((prev) => ({ ...prev, [field]: fErrs[field] }));
    };

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const errs = validate(values);
        setErrors(errs);
        if (Object.keys(errs).length > 0) return;
        setSubmitting(true);

        try {
            const response = await fetch('http://localhost:8000/registration/start-marine', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    first_name: values.firstName,
                    last_name: values.lastName,
                    email: values.email,
                    phone: values.phone,
                    company: values.company || null,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || 'Failed to submit registration');
            }

            setSubmitting(false);
            setSuccess(true);
        } catch (error) {
            setSubmitting(false);
            setErrors({ email: error instanceof Error ? error.message : 'Error submitting registration. Please try again.' });
        }
    };

    if (success) {
        return (
            <section className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-red-950 px-6 relative overflow-hidden">
                {/* Animated background elements */}
                <div className="absolute inset-0 overflow-hidden">
                    <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-red-500/5 rounded-full blur-3xl animate-pulse"></div>
                    <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-blue-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
                </div>

                <div className="max-w-2xl w-full text-center relative z-10">
                    <div className="glass-card p-12 backdrop-blur-xl bg-white/10 border border-white/20">
                        <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-green-400 to-green-600 mb-6 shadow-lg shadow-green-500/50 animate-bounce">
                            <Check className="w-12 h-12 text-white" strokeWidth={3} />
                        </div>
                        <h1 className="text-4xl font-bold text-white mb-4 bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                            Registration Successful!
                        </h1>
                        <p className="text-xl text-slate-300 mb-8 leading-relaxed">
                            Thank you for your interest in HSO Marine. Our team will contact you shortly to help you unlock your full maritime operations potential.
                        </p>
                        <a
                            href="/"
                            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-red-600 to-red-700 px-8 py-4 text-white text-lg font-semibold hover:from-red-700 hover:to-red-800 shadow-lg shadow-red-500/30 transition-all hover:scale-105"
                        >
                            Return to Home
                        </a>
                    </div>
                </div>
            </section>
        );
    }

    return (
        <section className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 py-16 px-6 relative overflow-hidden">
            {/* Animated background */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-red-500/10 rounded-full blur-3xl animate-pulse"></div>
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
            </div>

            <div className="container mx-auto max-w-7xl relative z-10">
                <div className="grid lg:grid-cols-2 gap-16 items-start">

                    {/* Left Column - Benefits */}
                    <div className="text-white space-y-8 lg:sticky lg:top-24">
                        <div className="space-y-4">
                            <h1 className="text-5xl sm:text-6xl font-bold leading-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                                Start tracking with HSO Marine today
                            </h1>
                            <div className="h-1 w-24 bg-gradient-to-r from-red-600 to-red-400 rounded-full"></div>
                        </div>

                        <div className="space-y-6">
                            <p className="text-2xl text-slate-200 font-medium">Unlock your full maritime operations potential now.</p>
                            <p className="text-lg text-slate-400">When you join HSO Marine, you get:</p>

                            <ul className="space-y-5">
                                <li className="flex items-start gap-4 group">
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center shadow-lg shadow-green-500/30 group-hover:scale-110 transition-transform">
                                        <Check className="w-5 h-5 text-white" strokeWidth={3} />
                                    </div>
                                    <span className="text-slate-200 text-lg leading-relaxed">Real-time vessel tracking and monitoring across global waters.</span>
                                </li>
                                <li className="flex items-start gap-4 group">
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center shadow-lg shadow-green-500/30 group-hover:scale-110 transition-transform">
                                        <Check className="w-5 h-5 text-white" strokeWidth={3} />
                                    </div>
                                    <span className="text-slate-200 text-lg leading-relaxed">Advanced fleet management tools and analytics dashboards.</span>
                                </li>
                                <li className="flex items-start gap-4 group">
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center shadow-lg shadow-green-500/30 group-hover:scale-110 transition-transform">
                                        <Check className="w-5 h-5 text-white" strokeWidth={3} />
                                    </div>
                                    <span className="text-slate-200 text-lg leading-relaxed">Comprehensive vessel data, routes, and port information.</span>
                                </li>
                                <li className="flex items-start gap-4 group">
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center shadow-lg shadow-green-500/30 group-hover:scale-110 transition-transform">
                                        <Check className="w-5 h-5 text-white" strokeWidth={3} />
                                    </div>
                                    <span className="text-slate-200 text-lg leading-relaxed">Instant alerts and notifications for your fleet operations.</span>
                                </li>
                            </ul>
                        </div>

                        {/* Contact Info */}
                        <div className="pt-6 space-y-4 border-t border-white/10">
                            <p className="text-slate-400 text-lg">Questions? Talk to an expert:</p>
                            <div className="flex flex-col gap-3">
                                <a href="tel:+16625639786" className="inline-flex items-center gap-3 text-xl text-red-400 hover:text-red-300 font-semibold transition-colors group">
                                    <Phone className="w-5 h-5 group-hover:scale-110 transition-transform" />
                                    +1 (662) 563-9786
                                </a>
                                <a href="mailto:info@hsomarine.com" className="inline-flex items-center gap-3 text-xl text-red-400 hover:text-red-300 font-semibold transition-colors group">
                                    <Mail className="w-5 h-5 group-hover:scale-110 transition-transform" />
                                    info@hsomarine.com
                                </a>
                            </div>
                        </div>

                        {/* Image */}
                        <div className="rounded-2xl overflow-hidden shadow-2xl shadow-black/50 border border-white/10 hover:scale-105 transition-transform duration-500">
                            <Image
                                src="/images/contact2webp.webp"
                                alt="Resumen"
                                fill
                                className="object-cover"
                            />
                        </div>
                    </div>

                    {/* Right Column - Form */}
                    <div className="lg:sticky lg:top-24">
                        <div className="p-8 lg:p-10 bg-white rounded-2xl border-2 border-slate-300 shadow-2xl">
                            <div className="mb-8">
                                <h2 className="text-3xl font-bold text-slate-950 mb-3">
                                    Ready to revolutionize your maritime operations?
                                </h2>
                                <p className="text-slate-800 text-lg leading-relaxed">
                                    Complete the form below to get started. Our team will be in touch to help you make the most of your powerful vessel tracking platform from day one.
                                </p>
                            </div>

                            <form onSubmit={onSubmit} className="space-y-6">
                                <div className="grid sm:grid-cols-2 gap-5">
                                    <div>
                                        <label htmlFor="firstName" className="block text-sm font-semibold text-slate-900 mb-2">
                                            First Name <span className="text-red-600">*</span>
                                        </label>
                                        <input
                                            id="firstName"
                                            type="text"
                                            value={values.firstName}
                                            onChange={onChange('firstName')}
                                            className={`w-full rounded-xl bg-white px-4 py-3.5 text-slate-900 ring-2 placeholder:text-slate-500 focus:outline-none focus:ring-2 transition-all ${errors.firstName ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-300 focus:ring-red-500'}`}
                                            placeholder="John"
                                        />
                                        {errors.firstName && <p className="text-xs text-red-600 mt-2 font-medium">{errors.firstName}</p>}
                                    </div>

                                    <div>
                                        <label htmlFor="lastName" className="block text-sm font-semibold text-slate-900 mb-2">
                                            Last Name <span className="text-red-600">*</span>
                                        </label>
                                        <input
                                            id="lastName"
                                            type="text"
                                            value={values.lastName}
                                            onChange={onChange('lastName')}
                                            className={`w-full rounded-xl bg-white px-4 py-3.5 text-slate-900 ring-2 placeholder:text-slate-500 focus:outline-none focus:ring-2 transition-all ${errors.lastName ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-300 focus:ring-red-500'}`}
                                            placeholder="Doe"
                                        />
                                        {errors.lastName && <p className="text-xs text-red-600 mt-2 font-medium">{errors.lastName}</p>}
                                    </div>
                                </div>

                                <div>
                                    <label htmlFor="email" className="block text-sm font-semibold text-slate-900 mb-2">
                                        Email <span className="text-red-600">*</span>
                                    </label>
                                    <input
                                        id="email"
                                        type="email"
                                        value={values.email}
                                        onChange={onChange('email')}
                                        className={`w-full rounded-xl bg-white px-4 py-3.5 text-slate-900 ring-2 placeholder:text-slate-500 focus:outline-none focus:ring-2 transition-all ${errors.email ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-300 focus:ring-red-500'}`}
                                        placeholder="john.doe@company.com"
                                    />
                                    {errors.email && <p className="text-xs text-red-600 mt-2 font-medium">{errors.email}</p>}
                                </div>

                                <div>
                                    <label htmlFor="phone" className="block text-sm font-semibold text-slate-900 mb-2">
                                        Phone Number <span className="text-red-600">*</span>
                                    </label>
                                    <input
                                        id="phone"
                                        type="tel"
                                        value={values.phone}
                                        onChange={onChange('phone')}
                                        className={`w-full rounded-xl bg-white px-4 py-3.5 text-slate-900 ring-2 placeholder:text-slate-500 focus:outline-none focus:ring-2 transition-all ${errors.phone ? 'ring-red-300 focus:ring-red-500' : 'ring-slate-300 focus:ring-red-500'}`}
                                        placeholder="+1 (555) 123-4567"
                                    />
                                    {errors.phone && <p className="text-xs text-red-600 mt-2 font-medium">{errors.phone}</p>}
                                </div>

                                <div>
                                    <label htmlFor="company" className="block text-sm font-semibold text-slate-900 mb-2">
                                        Company
                                    </label>
                                    <input
                                        id="company"
                                        type="text"
                                        value={values.company}
                                        onChange={onChange('company')}
                                        className="w-full rounded-xl bg-white px-4 py-3.5 text-slate-900 ring-2 ring-slate-300 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-red-500 transition-all"
                                        placeholder="Your Company Name"
                                    />
                                </div>

                                <button
                                    type="submit"
                                    disabled={submitting}
                                    className="w-full rounded-xl bg-gradient-to-r from-red-600 to-red-700 px-6 py-4 text-white text-lg font-bold hover:from-red-700 hover:to-red-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-red-500/30 hover:shadow-red-500/50 hover:scale-105 active:scale-95"
                                >
                                    {submitting ? (
                                        <span className="flex items-center justify-center gap-2">
                                            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                            </svg>
                                            Submitting...
                                        </span>
                                    ) : 'Get Started Now →'}
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
