import { apiFetch } from "@/lib/api";

export interface Invoice {
    id: number;
    name: string;
    partner_name: string | null;
    invoice_date: string | null;
    invoice_date_due: string | null;
    amount_total: number;
    amount_residual: number;
    amount_untaxed: number | null;
    amount_tax: number | null;
    currency_symbol: string | null;
    state: 'draft' | 'posted' | 'cancel';
    payment_state: 'not_paid' | 'in_payment' | 'paid' | 'partial' | 'reversed';
    invoice_portal_url: string | null;
}

export const InvoiceService = {
    /**
     * Obtiene las facturas del usuario autenticado
     */
    getMyInvoices: async (includePaid: boolean = false): Promise<Invoice[]> => {
        const params = new URLSearchParams();
        if (includePaid) {
            params.append('include_paid', 'true');
        }

        const url = `/invoices/my-invoices${params.toString() ? `?${params.toString()}` : ''}`;
        return await apiFetch<Invoice[]>(url);
    },

    /**
     * Obtiene la URL del portal de Odoo para una factura específica
     */
    getPortalUrl: async (invoiceId: number): Promise<string> => {
        const response = await apiFetch<{ portal_url: string }>(`/invoices/${invoiceId}/portal-url`);
        return response.portal_url;
    }
};
