from fastapi import APIRouter

# Agregador central de routers de la aplicación
# Mantiene los mismos prefijos que cada módulo declara (no se añade prefix global)

router = APIRouter()

# Auth
from app.auth.auth_router import router as auth_router  # /auth

from app.config.settings import (
	ENABLE_GOOGLE_OAUTH,
	ENABLE_CONTACT_FORMS,
	ENABLE_SUPPORT_FORM,
	ENABLE_RELEASES_API,
	ENABLE_RPC_API,
	ENABLE_ODOO_INTEGRATION,
)

if ENABLE_GOOGLE_OAUTH:
	try:
		from app.auth.providers.google import router as google_router  # /auth/google
	except Exception:  # pragma: no cover - optional
		google_router = None  # type: ignore

# System routes (healthz, root, google_authorized)
from app.api.system_router import router as system_router
try:
	from app.rpc.rpc_server import router as rpc_router
except Exception:
	rpc_router = None  # type: ignore
try:
	from app.api.contact_router import router as contact_router
except Exception:
	contact_router = None  # type: ignore
try:
	from app.api.simple_contact_router import router as simple_contact_router
except Exception:
	simple_contact_router = None  # type: ignore
try:
	from app.api.support_contact_router import router as support_contact_router
except Exception:
	support_contact_router = None  # type: ignore
try:
	from app.api.contact_form_router import router as contact_form_router  # /contact-us
except Exception:
	contact_form_router = None  # type: ignore
from app.api.activation_router import router as activation_router  # /auth/activation
try:
	from app.api.odoo_webhook_router import router as odoo_webhook_router  # /odoo (webhooks)
except Exception:
	odoo_webhook_router = None  # type: ignore
try:
	from app.integrations.odoo.odoo_router import router as odoo_integration_router  # /odoo (API proxy)
except Exception:
	odoo_integration_router = None  # type: ignore
try:
	from app.integrations.aisstream.router import router as aisstream_router
except Exception:
	aisstream_router = None  # pragma: no cover - optional in some envs
if 'aisstream_router' in globals() and aisstream_router:
	router.include_router(aisstream_router)

# Details (example public endpoint)
try:
	from app.api.details_router import router as details_router  # /details
except Exception:
	details_router = None  # type: ignore

# Incluir routers en el agregador
router.include_router(auth_router)
if ENABLE_GOOGLE_OAUTH and 'google_router' in globals() and google_router:
	router.include_router(google_router)
router.include_router(system_router)
if ENABLE_RPC_API and 'rpc_router' in globals() and rpc_router:
	router.include_router(rpc_router)
if ENABLE_CONTACT_FORMS and 'contact_router' in globals() and contact_router:
	router.include_router(contact_router)
if ENABLE_CONTACT_FORMS and 'simple_contact_router' in globals() and simple_contact_router:
	router.include_router(simple_contact_router)
if ENABLE_SUPPORT_FORM and 'support_contact_router' in globals() and support_contact_router:
	router.include_router(support_contact_router)
if ENABLE_CONTACT_FORMS and 'contact_form_router' in globals() and contact_form_router:
	router.include_router(contact_form_router)
router.include_router(activation_router)
if ENABLE_ODOO_INTEGRATION and 'odoo_webhook_router' in globals() and odoo_webhook_router:
	router.include_router(odoo_webhook_router)
if ENABLE_ODOO_INTEGRATION and 'odoo_integration_router' in globals() and odoo_integration_router:
	router.include_router(odoo_integration_router)

# Add details router unconditionally if available
if 'details_router' in globals() and details_router:
	router.include_router(details_router)

# Support form (SMTP)
try:
	from app.api.support_router import router as support_router
except Exception:
	support_router = None  # type: ignore
from app.config.settings import ENABLE_SUPPORT_FORM
if ENABLE_SUPPORT_FORM and 'support_router' in globals() and support_router:
	router.include_router(support_router)

# Release / Changelog
try:
	from app.api.release_router import router as release_router
except Exception:
	release_router = None  # type: ignore
if ENABLE_RELEASES_API and 'release_router' in globals() and release_router:
	router.include_router(release_router)

# User Preferences
try:
	from app.api.preferences_router import router as preferences_router
except Exception:
	preferences_router = None  # type: ignore
if 'preferences_router' in globals() and preferences_router:
	router.include_router(preferences_router)
