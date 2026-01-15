"""
Router para gestión de facturas de usuarios.
Proporciona endpoints para que los usuarios autenticados accedan a sus facturas desde Odoo ERP.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.core.auth.session_manager import get_current_user
from app.db.models import User

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("/my-invoices")
async def get_my_invoices(
    limit: int = Query(100, ge=1, le=500, description="Número máximo de facturas a retornar"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    include_paid: bool = Query(True, description="Incluir facturas pagadas"),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene las facturas del usuario autenticado.
    
    Las facturas se filtran por el email del usuario y se obtienen del ERP de Odoo.
    Cada factura incluye una URL al portal de Odoo donde el usuario puede ver
    detalles completos, descargar PDF y realizar pagos.
    
    Args:
        limit: Número máximo de facturas a retornar (default: 100)
        offset: Offset para paginación (default: 0)
        include_paid: Si True, incluye facturas ya pagadas (default: True)
        current_user: Usuario autenticado (inyectado automáticamente)
    
    Returns:
        Lista de facturas del usuario
    """
    try:
        # Lazy imports to avoid blocking on module load
        from app.integrations.odoo.odoo_service import list_customer_invoices_by_email, get_invoice_portal_url
        from app.integrations.odoo.odoo_accounting_models import Invoice
        
        # Obtener email del usuario
        user_email = current_user.email
        
        if not user_email:
            raise HTTPException(
                status_code=400,
                detail="El usuario no tiene un email configurado"
            )
        
        # Obtener facturas desde Odoo ERP
        invoices_data = list_customer_invoices_by_email(
            email=user_email,
            limit=limit,
            offset=offset,
            profile="erp",  # Usar perfil ERP
            include_paid=include_paid,
        )
        
        # Procesar y enriquecer datos
        invoices = []
        for inv_data in invoices_data:
            # Extraer nombre del partner
            partner_name = None
            if inv_data.get("partner_id") and isinstance(inv_data["partner_id"], list):
                partner_name = inv_data["partner_id"][1] if len(inv_data["partner_id"]) > 1 else None
            
            # Extraer símbolo de moneda
            currency_symbol = "$"  # Default
            if inv_data.get("currency_id") and isinstance(inv_data["currency_id"], list):
                currency_symbol = inv_data["currency_id"][1] if len(inv_data["currency_id"]) > 1 else "$"
            
            # Generar URL del portal
            portal_url = None
            if inv_data.get("id"):
                from app.config.settings import ODOO_ERP_URL
                access_token = inv_data.get("access_token")
                portal_url = get_invoice_portal_url(
                    invoice_id=inv_data["id"],
                    access_token=access_token,
                    odoo_base_url=ODOO_ERP_URL or "https://erp.hsotrade.com"
                )
            
            # Crear objeto Invoice
            invoice = Invoice(
                id=inv_data.get("id"),
                name=inv_data.get("name", ""),
                partner_id=inv_data.get("partner_id"),
                partner_name=partner_name,
                invoice_date=inv_data.get("invoice_date"),
                invoice_date_due=inv_data.get("invoice_date_due"),
                amount_total=inv_data.get("amount_total", 0.0),
                amount_residual=inv_data.get("amount_residual", 0.0),
                amount_untaxed=inv_data.get("amount_untaxed"),
                amount_tax=inv_data.get("amount_tax"),
                currency_id=inv_data.get("currency_id"),
                currency_symbol=currency_symbol,
                state=inv_data.get("state", "draft"),
                payment_state=inv_data.get("payment_state", "not_paid"),
                move_type=inv_data.get("move_type", "out_invoice"),
                access_token=inv_data.get("access_token"),
                invoice_portal_url=portal_url,
            )
            invoices.append(invoice)
        
        return invoices
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener facturas: {str(e)}"
        )


@router.get("/{invoice_id}/portal-url")
async def get_invoice_portal_url_endpoint(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Obtiene la URL del portal de Odoo para una factura específica.
    
    Verifica que la factura pertenezca al usuario autenticado antes de
    generar la URL.
    
    Args:
        invoice_id: ID de la factura en Odoo
        current_user: Usuario autenticado (inyectado automáticamente)
    
    Returns:
        Diccionario con la URL del portal
    """
    try:
        # Import here to avoid blocking on module load
        from app.integrations.odoo.odoo_service import list_customer_invoices_by_email, get_invoice_portal_url
        
        user_email = current_user.email
        
        if not user_email:
            raise HTTPException(
                status_code=400,
                detail="El usuario no tiene un email configurado"
            )
        
        # Verificar que la factura pertenezca al usuario
        invoices_data = list_customer_invoices_by_email(
            email=user_email,
            limit=1,
            offset=0,
            profile="erp",
            include_paid=True,  # Incluir todas para verificación
        )
        
        # Buscar la factura específica
        invoice_found = None
        for inv in invoices_data:
            if inv.get("id") == invoice_id:
                invoice_found = inv
                break
        
        if not invoice_found:
            raise HTTPException(
                status_code=404,
                detail="Factura no encontrada o no pertenece al usuario"
            )
        
        # Generar URL del portal
        from app.config.settings import ODOO_ERP_URL
        access_token = invoice_found.get("access_token")
        portal_url = get_invoice_portal_url(
            invoice_id=invoice_id,
            access_token=access_token,
            odoo_base_url=ODOO_ERP_URL or "https://erp.hsotrade.com"
        )
        
        return {"portal_url": portal_url}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar URL del portal: {str(e)}"
        )
