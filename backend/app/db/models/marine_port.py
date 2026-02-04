from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, func, Index
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship

from app.db.database import Base


class MarinePort(Base):
    __tablename__ = "marine_port"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unlocode = Column(String(16), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(128))
    ext_refs = Column(postgresql.JSONB, nullable=True)
    coords = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Identificación
    port_number = Column(Integer, nullable=True, index=True)
    port_name = Column(String(255), nullable=True)
    region_number = Column(Integer, nullable=True)
    region_name = Column(String(255), nullable=True)
    country_code = Column(String(2), nullable=True)
    country_name = Column(String(255), nullable=True)
    alternate_name = Column(String(255), nullable=True)
    global_id = Column(String(50), nullable=True)

    # Ubicación Geográfica
    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)
    ycoord = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    xcoord = Column(postgresql.DOUBLE_PRECISION, nullable=True)

    # Documentación de Navegación
    publication_number = Column(String(255), nullable=True)
    chart_number = Column(String(255), nullable=True)
    nav_area = Column(String(10), nullable=True)
    dnc = Column(String(255), nullable=True)
    s121_water_body = Column(String(255), nullable=True)
    s57_enc = Column(String(255), nullable=True)
    s101_enc = Column(String(255), nullable=True)
    dod_water_body = Column(String(255), nullable=True)

    # Características del Puerto
    harbor_size = Column(String(1), nullable=True) # V, S, M, L
    harbor_type = Column(String(10), nullable=True)
    shelter = Column(String(1), nullable=True) # E, G, F, P, N, U

    # Restricciones de Entrada
    er_tide = Column(String(1), nullable=True)
    er_swell = Column(String(1), nullable=True)
    er_ice = Column(String(1), nullable=True)
    er_other = Column(String(1), nullable=True)
    overhead_limits = Column(String(1), nullable=True)

    # Profundidades (en metros)
    ch_depth = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    an_depth = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    cp_depth = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    ot_depth = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    tide = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    lng_terminal_depth = Column(postgresql.DOUBLE_PRECISION, nullable=True)

    # Dimensiones Máximas
    max_vessel_length = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    max_vessel_beam = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    max_vessel_draft = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    off_max_vessel_length = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    off_max_vessel_beam = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    off_max_vessel_draft = Column(postgresql.DOUBLE_PRECISION, nullable=True)
    entrance_width = Column(postgresql.DOUBLE_PRECISION, nullable=True)

    # Condiciones de Navegación
    good_holding_ground = Column(String(1), nullable=True)
    turning_area = Column(String(1), nullable=True)
    first_port_of_entry = Column(String(1), nullable=True)
    us_rep = Column(String(1), nullable=True)

    # Servicios de Pilotaje
    pt_compulsory = Column(String(1), nullable=True)
    pt_available = Column(String(1), nullable=True)
    pt_local_assist = Column(String(1), nullable=True)
    pt_advisable = Column(String(1), nullable=True)

    # Servicios de Remolcadores
    tugs_salvage = Column(String(1), nullable=True)
    tugs_assist = Column(String(1), nullable=True)

    # Cuarentena
    qt_pratique = Column(String(1), nullable=True)
    qt_other = Column(String(1), nullable=True)
    qt_sanitation = Column(String(1), nullable=True)

    # Comunicaciones
    cm_telephone = Column(String(1), nullable=True)
    cm_telegraph = Column(String(1), nullable=True)
    cm_radio = Column(String(1), nullable=True)
    cm_radio_tel = Column(String(1), nullable=True)
    cm_air = Column(String(1), nullable=True)
    cm_rail = Column(String(1), nullable=True)

    # Instalaciones de Carga
    lo_wharves = Column(String(1), nullable=True)
    lo_anchor = Column(String(1), nullable=True)
    lo_med_moor = Column(String(1), nullable=True)
    lo_beach_moor = Column(String(1), nullable=True)
    lo_ice_moor = Column(String(1), nullable=True)
    lo_roro = Column(String(1), nullable=True)
    lo_solid_bulk = Column(String(1), nullable=True)
    lo_container = Column(String(1), nullable=True)
    lo_break_bulk = Column(String(1), nullable=True)
    lo_oil_term = Column(String(1), nullable=True)
    lo_long_term = Column(String(1), nullable=True)
    lo_other = Column(String(1), nullable=True)
    lo_dang_cargo = Column(String(1), nullable=True)
    lo_liquid_bulk = Column(String(1), nullable=True)

    # Instalaciones y Servicios
    med_facilities = Column(String(1), nullable=True)
    garbage_disposal = Column(String(1), nullable=True)
    degauss = Column(String(1), nullable=True)
    dirty_ballast = Column(String(1), nullable=True)

    # Grúas
    cr_fixed = Column(String(1), nullable=True)
    cr_mobile = Column(String(1), nullable=True)
    cr_floating = Column(String(1), nullable=True)
    cranes_container = Column(String(1), nullable=True)

    # Capacidad de Elevación
    lifts_100 = Column(String(1), nullable=True)
    lifts_50 = Column(String(1), nullable=True)
    lifts_25 = Column(String(1), nullable=True)
    lifts_0 = Column(String(1), nullable=True)

    # Servicios de Reparación
    sr_longshore = Column(String(1), nullable=True)
    sr_electrical = Column(String(1), nullable=True)
    sr_steam = Column(String(1), nullable=True)
    sr_navig_equip = Column(String(1), nullable=True)
    sr_elect_repair = Column(String(1), nullable=True)
    sr_ice_breaking = Column(String(1), nullable=True)
    sr_diving = Column(String(1), nullable=True)

    # Suministros
    su_provisions = Column(String(1), nullable=True)
    su_water = Column(String(1), nullable=True)
    su_fuel = Column(String(1), nullable=True)
    su_diesel = Column(String(1), nullable=True)
    su_deck = Column(String(1), nullable=True)
    su_engine = Column(String(1), nullable=True)
    su_aviation_fuel = Column(String(1), nullable=True)

    # Instalaciones de Reparación
    repair_code = Column(String(1), nullable=True) # A, B, C, N, U
    drydock = Column(String(1), nullable=True) # L, M, S
    railway = Column(String(1), nullable=True) # L, M, S

    # Otros Servicios
    harbor_use = Column(String(50), nullable=True)
    ukc_mgmt_system = Column(String(1), nullable=True)
    port_security = Column(String(1), nullable=True)
    eta_message = Column(String(1), nullable=True)
    search_and_rescue = Column(String(1), nullable=True)
    tss = Column(String(1), nullable=True)
    vts = Column(String(1), nullable=True)
    cht = Column(String(1), nullable=True)

    __table_args__ = (
        Index("ix_marine_port_unlocode_name", "unlocode", "name"),
        Index("ix_marine_port_port_number", "port_number"),
    )

    # relaciones opcionales
    # events = relationship("PortEvent", back_populates="port")
