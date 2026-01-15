"""
Modelos Pydantic para el módulo de Accounting de Odoo.
Representa facturas (account.move) y sus componentes.
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator


class Invoice(BaseModel):
    """Modelo para una factura de Odoo (account.move)."""
    
    id: int = Field(..., description="ID de la factura en Odoo")
    name: str = Field(..., description="Número de factura")
    partner_id: Optional[List] = Field(None, description="ID y nombre del partner [id, name]")
    partner_name: Optional[str] = Field(None, description="Nombre del cliente")
    invoice_date: Optional[str] = Field(None, description="Fecha de emisión")
    invoice_date_due: Optional[str] = Field(None, description="Fecha de vencimiento")
    amount_total: float = Field(0.0, description="Monto total")
    amount_residual: float = Field(0.0, description="Saldo pendiente")
    amount_untaxed: Optional[float] = Field(None, description="Monto sin impuestos")
    amount_tax: Optional[float] = Field(None, description="Monto de impuestos")
    currency_id: Optional[List] = Field(None, description="ID y símbolo de moneda [id, symbol]")
    currency_symbol: Optional[str] = Field(None, description="Símbolo de la moneda")
    state: str = Field("draft", description="Estado: draft, posted, cancel")
    payment_state: str = Field("not_paid", description="Estado de pago: not_paid, in_payment, paid, partial, reversed")
    move_type: str = Field("out_invoice", description="Tipo: out_invoice, out_refund, in_invoice, in_refund")
    access_token: Optional[str] = Field(None, description="Token de acceso para el portal")
    invoice_portal_url: Optional[str] = Field(None, description="URL del portal de Odoo")
    
    @field_validator('access_token', mode='before')
    @classmethod
    def convert_false_to_none(cls, v: Any) -> Optional[str]:
        """Convierte False de Odoo a None para campos opcionales."""
        if v is False:
            return None
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345,
                "name": "INV/2025/00001",
                "partner_id": [100, "Acme Corp"],
                "partner_name": "Acme Corp",
                "invoice_date": "2025-01-15",
                "invoice_date_due": "2025-02-15",
                "amount_total": 1500.00,
                "amount_residual": 1500.00,
                "amount_untaxed": 1250.00,
                "amount_tax": 250.00,
                "currency_id": [1, "$"],
                "currency_symbol": "$",
                "state": "posted",
                "payment_state": "not_paid",
                "move_type": "out_invoice",
                "access_token": "abc123...",
                "invoice_portal_url": "https://erp.hsotrade.com/my/invoices/12345?access_token=abc123"
            }
        }


class InvoiceLine(BaseModel):
    """Modelo para una línea de factura (account.move.line)."""
    
    id: int = Field(..., description="ID de la línea")
    product_id: Optional[List] = Field(None, description="ID y nombre del producto [id, name]")
    product_name: Optional[str] = Field(None, description="Nombre del producto")
    name: Optional[str] = Field(None, description="Descripción de la línea")
    quantity: float = Field(0.0, description="Cantidad")
    price_unit: float = Field(0.0, description="Precio unitario")
    price_subtotal: float = Field(0.0, description="Subtotal")
    price_total: float = Field(0.0, description="Total con impuestos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "product_id": [50, "Product A"],
                "product_name": "Product A",
                "name": "Product A - Description",
                "quantity": 10.0,
                "price_unit": 125.00,
                "price_subtotal": 1250.00,
                "price_total": 1500.00
            }
        }
