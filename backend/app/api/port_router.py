import httpx
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from app.db import models as m
from app.core.auth.guards import require_admin
from app.core.auth.session_manager import get_current_user
from geoalchemy2.functions import ST_SetSRID, ST_Point
from app.schemas.port_schemas import PortListResponse, PortListEntry

router = APIRouter(prefix="/ports", tags=["Ports"])

NGA_API_URL = "https://msi.nga.mil/api/publications/world-port-index?output=json"

FIELD_MAP = {
    "portNumber": "port_number",
    "portName": "port_name",
    "regionNumber": "region_number",
    "regionName": "region_name",
    "countryCode": "country_code",
    "countryName": "country_name",
    "alternateName": "alternate_name",
    "unloCode": "unlocode",
    "globalId": "global_id",
    "latitude": "latitude",
    "longitude": "longitude",
    "ycoord": "ycoord",
    "xcoord": "xcoord",
    "publicationNumber": "publication_number",
    "chartNumber": "chart_number",
    "navArea": "nav_area",
    "dnc": "dnc",
    "s121WaterBody": "s121_water_body",
    "s57Enc": "s57_enc",
    "s101Enc": "s101_enc",
    "dodWaterBody": "dod_water_body",
    "harborSize": "harbor_size",
    "harborType": "harbor_type",
    "shelter": "shelter",
    "erTide": "er_tide",
    "erSwell": "er_swell",
    "erIce": "er_ice",
    "erOther": "er_other",
    "overheadLimits": "overhead_limits",
    "chDepth": "ch_depth",
    "anDepth": "an_depth",
    "cpDepth": "cp_depth",
    "otDepth": "ot_depth",
    "tide": "tide",
    "lngTerminalDepth": "lng_terminal_depth",
    "maxVesselLength": "max_vessel_length",
    "maxVesselBeam": "max_vessel_beam",
    "maxVesselDraft": "max_vessel_draft",
    "offMaxVesselLength": "off_max_vessel_length",
    "offMaxVesselBeam": "off_max_vessel_beam",
    "offMaxVesselDraft": "off_max_vessel_draft",
    "entranceWidth": "entrance_width",
    "goodHoldingGround": "good_holding_ground",
    "turningArea": "turning_area",
    "firstPortOfEntry": "first_port_of_entry",
    "usRep": "us_rep",
    "ptCompulsory": "pt_compulsory",
    "ptAvailable": "pt_available",
    "ptLocalAssist": "pt_local_assist",
    "ptAdvisable": "pt_advisable",
    "tugsSalvage": "tugs_salvage",
    "tugsAssist": "tugs_assist",
    "qtPratique": "qt_pratique",
    "qtOther": "qt_other",
    "qtSanitation": "qt_sanitation",
    "cmTelephone": "cm_telephone",
    "cmTelegraph": "cm_telegraph",
    "cmRadio": "cm_radio",
    "cmRadioTel": "cm_radio_tel",
    "cmAir": "cm_air",
    "cmRail": "cm_rail",
    "loWharves": "lo_wharves",
    "loAnchor": "lo_anchor",
    "loMedMoor": "lo_med_moor",
    "loBeachMoor": "lo_beach_moor",
    "loIceMoor": "lo_ice_moor",
    "loRoro": "lo_roro",
    "loSolidBulk": "lo_solid_bulk",
    "loContainer": "lo_container",
    "loBreakBulk": "lo_break_bulk",
    "loOilTerm": "lo_oil_term",
    "loLongTerm": "lo_long_term",
    "loOther": "lo_other",
    "loDangCargo": "lo_dang_cargo",
    "loLiquidBulk": "lo_liquid_bulk",
    "medFacilities": "med_facilities",
    "garbageDisposal": "garbage_disposal",
    "degauss": "degauss",
    "dirtyBallast": "dirty_ballast",
    "crFixed": "cr_fixed",
    "crMobile": "cr_mobile",
    "crFloating": "cr_floating",
    "cranesContainer": "cranes_container",
    "lifts100": "lifts_100",
    "lifts50": "lifts_50",
    "lifts25": "lifts_25",
    "lifts0": "lifts_0",
    "srLongshore": "sr_longshore",
    "srElectrical": "sr_electrical",
    "srSteam": "sr_steam",
    "srNavigEquip": "sr_navig_equip",
    "srElectRepair": "sr_elect_repair",
    "srIceBreaking": "sr_ice_breaking",
    "srDiving": "sr_diving",
    "suProvisions": "su_provisions",
    "suWater": "su_water",
    "suFuel": "su_fuel",
    "suDiesel": "su_diesel",
    "suDeck": "su_deck",
    "suEngine": "su_engine",
    "suAviationFuel": "su_aviation_fuel",
    "repairCode": "repair_code",
    "drydock": "drydock",
    "railway": "railway",
    "harborUse": "harbor_use",
    "ukcMgmtSystem": "ukc_mgmt_system",
    "portSecurity": "port_security",
    "etaMessage": "eta_message",
    "searchAndRescue": "search_and_rescue",
    "tss": "tss",
    "vts": "vts",
    "cht": "cht",
}

@router.get("/sync")
async def sync_ports(db: Session = Depends(get_db), current_user: m.User = Depends(require_admin)):
    """
    Sync ports from NGA World Port Index API.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(NGA_API_URL)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return {"error": f"Failed to fetch data from NGA: {str(e)}"}

    ports_data = data.get("ports", [])
    added_count = 0
    updated_count = 0

    for port_json in ports_data:
        port_num = port_json.get("portNumber")
        
        if not port_num:
            continue

        # Try to find ONLY by port_number (now our unique source of truth)
        db_port = db.query(m.MarinePort).filter(m.MarinePort.port_number == port_num).first()
        
        is_new = False
        if not db_port:
            db_port = m.MarinePort()
            db_port.port_number = port_num
            # Default unlocode to whatever is in JSON or a temp value
            unlocode = port_json.get("unloCode")
            db_port.unlocode = unlocode if unlocode else f"PORT_{port_num}"
            db_port.name = port_json.get("portName") or "Unknown"
            is_new = True
            db.add(db_port)
        
        # Update fields
        for json_key, db_key in FIELD_MAP.items():
            if json_key in port_json:
                setattr(db_port, db_key, port_json[json_key])
        
        # Sync duplicate fields for compatibility
        if "portName" in port_json:
            db_port.name = port_json["portName"]
        if "countryName" in port_json:
            db_port.country = port_json["countryName"]
        if "unloCode" in port_json and port_json["unloCode"]:
            db_port.unlocode = port_json["unloCode"]

        # Handle Coords (Geography)
        x = port_json.get("xcoord")
        y = port_json.get("ycoord")
        if x is not None and y is not None:
            try:
                # Use ST_SetSRID and ST_Point to create the geometry
                db_port.coords = ST_SetSRID(ST_Point(float(x), float(y)), 4326)
            except (ValueError, TypeError):
                pass

        if is_new:
            added_count += 1
        else:
            updated_count += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return {"error": f"Database commit failed: {str(e)}"}

    return {
        "message": "update successfull",
        "ports added": added_count,
        "ports updated": updated_count
    }


@router.get("/list", response_model=PortListResponse)
async def list_ports(db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    """
    Get a list of all ports with their basic info for map display.
    Returns xcoord (longitude) and ycoord (latitude) as decimal coordinates.
    """
    ports = db.query(
        m.MarinePort.port_number, 
        m.MarinePort.xcoord,  # longitude in decimal
        m.MarinePort.ycoord   # latitude in decimal
    ).all()
    
    # Map the results to the response format
    port_entries = [
        PortListEntry(port_number=p.port_number, lon=p.xcoord, lat=p.ycoord)
        for p in ports
    ]
    
    return PortListResponse(ports=port_entries)


@router.get("/search")
async def search_ports(
    unlocode: str = None,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user)
):
    """
    Search for a port by UN/LOCODE.
    """
    if not unlocode:
        raise HTTPException(status_code=400, detail="UN/LOCODE parameter is required")

    # Case-insensitive search
    # unlocode column matches the input
    port = db.query(m.MarinePort).filter(m.MarinePort.unlocode.ilike(unlocode)).first()
    
    if not port:
        raise HTTPException(status_code=404, detail=f"Port with UN/LOCODE {unlocode} not found")
        
    # Manual conversion to dict to safely exclude the binary 'coords' field
    # reusing logic from get_port_details
    port_data = {}
    for column in m.MarinePort.__table__.columns:
        if column.name != 'coords':
            port_data[column.name] = getattr(port, column.name)
            
    return port_data


@router.get("/details/{port_number}")
async def get_port_details(port_number: int, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    """
    Get all details for a specific port by its port_number.
    """
    port = db.query(m.MarinePort).filter(m.MarinePort.port_number == port_number).first()
    
    if not port:
        raise HTTPException(status_code=404, detail=f"Port with number {port_number} not found")
        
    # Manual conversion to dict to safely exclude the binary 'coords' field
    port_data = {}
    for column in m.MarinePort.__table__.columns:
        if column.name != 'coords':
            port_data[column.name] = getattr(port, column.name)
            
    return port_data
