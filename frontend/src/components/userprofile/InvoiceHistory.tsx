import React, { useEffect, useState } from 'react';
import { InvoiceService, Invoice } from '@/services/InvoiceService';
import { ExternalLink } from 'lucide-react';

export default function InvoiceHistory() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [filter, setFilter] = useState<'all' | 'paid' | 'pending'>('all');

    useEffect(() => {
        let mounted = true;
        const load = async () => {
            setLoading(true);
            try {
                const data = await InvoiceService.getMyInvoices(true);
                if (!mounted) return;
                setInvoices(data);
                setError(null);
            } catch (e: any) {
                if (!mounted) return;
                setError(e?.message || 'Failed to load invoices');
                setInvoices([]);
            } finally {
                if (mounted) setLoading(false);
            }
        };
        load();
        return () => { mounted = false; };
    }, []);

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return '—';
        try {
            const date = new Date(dateStr + 'T00:00:00Z');
            return date.toLocaleDateString(undefined, { timeZone: 'UTC' });
        } catch {
            return dateStr;
        }
    };

    const formatCurrency = (amount: number, symbol: string | null) => {
        const sym = symbol || '$';
        return `${sym}${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    const getPaymentStateBadge = (paymentState: string) => {
        const badges: Record<string, { label: string; color: string }> = {
            'paid': {
                label: 'Paid',
                color: 'bg-green-50 text-green-700 dark:bg-green-900/40 dark:text-green-200'
            },
            'not_paid': {
                label: 'Pending',
                color: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-200'
            },
            'partial': {
                label: 'Partial',
                color: 'bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200'
            },
            'in_payment': {
                label: 'In Payment',
                color: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-200'
            },
            'reversed': {
                label: 'Reversed',
                color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
            },
        };

        const badge = badges[paymentState] || badges['not_paid'];
        return (
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${badge.color}`}>
                {badge.label}
            </span>
        );
    };

    const isOverdue = (dueDate: string | null, paymentState: string) => {
        if (!dueDate || paymentState === 'paid') return false;
        try {
            return new Date(dueDate) < new Date();
        } catch {
            return false;
        }
    };

    const filteredInvoices = invoices.filter(invoice => {
        if (filter === 'all') return true;
        if (filter === 'paid') return invoice.payment_state === 'paid';
        if (filter === 'pending') return invoice.payment_state !== 'paid';
        return true;
    });

    return (
        <div className="mt-2 text-sm">
            <div className="flex items-center justify-between px-1 mb-2">
                <h3 className="text-base font-medium text-slate-800 dark:text-gray-200">
                    Invoice history
                </h3>
                <div className="flex items-center gap-2">
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value as 'all' | 'paid' | 'pending')}
                        className="text-xs px-2 py-1 rounded border cursor-pointer bg-white text-slate-700 border-slate-300 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                        <option value="all">All</option>
                        <option value="pending">Pending</option>
                        <option value="paid">Paid</option>
                    </select>
                    <div className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-700 dark:bg-gray-800 dark:text-gray-200 border dark:border-gray-700">
                        Total: <span className="font-semibold ml-1">{filteredInvoices.length}</span>
                    </div>
                </div>
            </div>

            <div className="rounded-sm border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
                <div className="relative p-2 overflow-x-auto">
                    {loading && <div className="h-24 flex items-center justify-center text-sm opacity-80">Loading...</div>}
                    {error && <div className="p-4 text-sm text-red-600">{error}</div>}
                    {!loading && !error && (
                        <table className="min-w-full text-xs sm:text-[13px] text-slate-700 dark:text-gray-300">
                            <thead className="text-[10px] sm:text-[11px] uppercase tracking-wide">
                                <tr className="bg-white text-slate-500 border-b border-slate-200 dark:bg-gray-900 dark:text-gray-400 dark:border-gray-800">
                                    <th className="px-3 py-2 text-left">Number</th>
                                    <th className="px-3 py-2 text-left">Date</th>
                                    <th className="px-3 py-2 text-left">Due Date</th>
                                    <th className="px-3 py-2 text-right">Total</th>
                                    <th className="px-3 py-2 text-right">Balance</th>
                                    <th className="px-3 py-2 text-center">Status</th>
                                    <th className="px-3 py-2 text-center">Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredInvoices.length === 0 && (
                                    <tr>
                                        <td colSpan={7} className="h-24 text-center text-sm text-slate-500 dark:text-gray-400">
                                            No invoices found
                                        </td>
                                    </tr>
                                )}
                                {filteredInvoices.map((invoice, idx) => {
                                    const overdue = isOverdue(invoice.invoice_date_due, invoice.payment_state);
                                    return (
                                        <tr
                                            key={invoice.id}
                                            className={`${idx % 2 === 0 ? 'bg-slate-50/40 dark:bg-gray-800/30' : ''} border-b border-slate-100 dark:border-gray-800 hover:bg-slate-50 dark:hover:bg-gray-800 transition-colors`}
                                        >
                                            <td className="px-3 py-2 align-middle whitespace-nowrap font-medium">
                                                {invoice.name}
                                                {overdue && (
                                                    <span className="ml-2 text-[10px] text-red-500 font-semibold">
                                                        OVERDUE
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-3 py-2 align-middle whitespace-nowrap">
                                                {formatDate(invoice.invoice_date)}
                                            </td>
                                            <td className="px-3 py-2 align-middle whitespace-nowrap">
                                                {formatDate(invoice.invoice_date_due)}
                                            </td>
                                            <td className="px-3 py-2 align-middle whitespace-nowrap text-right font-mono">
                                                {formatCurrency(invoice.amount_total, invoice.currency_symbol)}
                                            </td>
                                            <td className="px-3 py-2 align-middle whitespace-nowrap text-right font-mono">
                                                {formatCurrency(invoice.amount_residual, invoice.currency_symbol)}
                                            </td>
                                            <td className="px-3 py-2 align-middle text-center">
                                                {getPaymentStateBadge(invoice.payment_state)}
                                            </td>
                                            <td className="px-3 py-2 align-middle text-center">
                                                {invoice.invoice_portal_url ? (
                                                    <a
                                                        href={invoice.invoice_portal_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center gap-1 px-3 py-1 rounded text-xs font-medium transition-colors bg-indigo-50 text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-900/40 dark:text-indigo-200 dark:hover:bg-indigo-800/60"
                                                        title="View Invoice"
                                                    >
                                                        View
                                                        <ExternalLink size={12} />
                                                    </a>
                                                ) : (
                                                    <span className="text-xs opacity-50">—</span>
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}
