"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Protected } from "@/components/auth/Protected";
import { apiFetch } from "@/lib/api";
import {
  MapPin,
  Anchor,
  Ship,
  Compass,
  ArrowLeft,
  Navigation,
  ShieldAlert,
  Waves,
  Ruler,
  Info,
  Radio,
  Wrench,
  Package,
  Hammer,
  Globe2
} from "lucide-react";

// Full Types based on the backend schema
interface PortData {
  port_number: number;
  port_name: string;
  region_number: number;
  region_name: string;
  country_code: string;
  country_name: string;
  alternate_name: string | null;
  global_id: string;
  latitude: string;
  longitude: string;
  publication_number: string | null;
  chart_number: string | null;
  nav_area: string | null;
  dnc: string | null;
  dod_water_body: string | null;
  unlocode: string | null;
  harbor_size: string | null;
  harbor_type: string | null;
  shelter: string | null;
  er_tide: string | null;
  er_swell: string | null;
  er_ice: string | null;
  er_other: string | null;
  overhead_limits: string | null;
  ch_depth: number | null;
  an_depth: number | null;
  cp_depth: number | null;
  ot_depth: number | null;
  tide: number | null;
  lng_terminal_depth: number | null;
  max_vessel_length: number | null;
  max_vessel_beam: number | null;
  max_vessel_draft: number | null;
  off_max_vessel_length: number | null;
  off_max_vessel_beam: number | null;
  off_max_vessel_draft: number | null;
  entrance_width: number | null;
  good_holding_ground: string | null;
  turning_area: string | null;
  first_port_of_entry: string | null;
  us_rep: string | null;
  pt_compulsory: string | null;
  pt_available: string | null;
  pt_local_assist: string | null;
  pt_advisable: string | null;
  tugs_salvage: string | null;
  tugs_assist: string | null;
  qt_pratique: string | null;
  qt_other: string | null;
  qt_sanitation: string | null;
  cm_telephone: string | null;
  cm_telegraph: string | null;
  cm_radio: string | null;
  cm_radio_tel: string | null;
  cm_air: string | null;
  cm_rail: string | null;
  lo_wharves: string | null;
  lo_anchor: string | null;
  lo_med_moor: string | null;
  lo_beach_moor: string | null;
  lo_ice_moor: string | null;
  lo_roro: string | null;
  lo_solid_bulk: string | null;
  lo_container: string | null;
  lo_break_bulk: string | null;
  lo_oil_term: string | null;
  lo_long_term: string | null;
  lo_other: string | null;
  lo_dang_cargo: string | null;
  lo_liquid_bulk: string | null;
  med_facilities: string | null;
  garbage_disposal: string | null;
  degauss: string | null;
  dirty_ballast: string | null;
  cr_fixed: string | null;
  cr_mobile: string | null;
  cr_floating: string | null;
  cranes_container: string | null;
  lifts_100: string | null;
  lifts_50: string | null;
  lifts_25: string | null;
  lifts_0: string | null;
  sr_longshore: string | null;
  sr_electrical: string | null;
  sr_steam: string | null;
  sr_navig_equip: string | null;
  sr_elect_repair: string | null;
  sr_ice_breaking: string | null;
  sr_diving: string | null;
  su_provisions: string | null;
  su_water: string | null;
  su_fuel: string | null;
  su_diesel: string | null;
  su_deck: string | null;
  su_engine: string | null;
  su_aviation_fuel: string | null;
  repair_code: string | null;
  drydock: string | null;
  railway: string | null;
  harbor_use: string | null;
  ukc_mgmt_system: string | null;
  port_security: string | null;
  eta_message: string | null;
  search_and_rescue: string | null;
  tss: string | null;
  vts: string | null;
  cht: string | null;
}

type LoadingState = "loading" | "error" | "success";

// Helper to map YES/NO/UNKNOWN values
const boolString = (val?: string | null) => {
  if (val === 'Y') return 'Yes';
  if (val === 'N') return 'No';
  if (val === 'U') return 'Unknown';
  return val || 'Unknown';
};

// Helper mappings for NGA abbreviations
const harborSizeMap: Record<string, string> = { 'L': 'Large', 'M': 'Medium', 'S': 'Small', 'V': 'Very Small', 'X': 'Unknown' };
const harborTypeMap: Record<string, string> = { 'CB': 'Coastal (Breakwater)', 'CN': 'Coastal (Natural)', 'CT': 'Coastal (Tide Gates)', 'LC': 'Lake or Canal', 'RB': 'River (Basin)', 'RN': 'River (Natural)', 'RT': 'River (Tide Gates)', 'TH': 'Typhoon Harbor', 'OR': 'Open Roadstead', 'Unknown': 'Unknown' };
const shelterMap: Record<string, string> = { 'E': 'Excellent', 'G': 'Good', 'F': 'Fair', 'P': 'Poor', 'N': 'None', 'Unknown': 'Unknown' };
const repairMap: Record<string, string> = { 'A': 'Major', 'B': 'Moderate', 'C': 'Limited', 'N': 'None', 'Unknown': 'Unknown' };

export default function PortDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const unlocode = params?.unlocode as string;

  const [status, setStatus] = useState<LoadingState>("loading");
  const [port, setPort] = useState<PortData | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (!unlocode) return;

    const fetchPort = async () => {
      try {
        setStatus("loading");
        const data = await apiFetch<PortData>(`/ports/search?unlocode=${encodeURIComponent(unlocode)}`);
        setPort(data);
        setStatus("success");
      } catch (err: any) {
        console.error("Failed to fetch port:", err);
        setErrorMsg(err.message || "Port not found");
        setStatus("error");
      }
    };

    fetchPort();
  }, [unlocode]);

  if (status === "loading") {
    return (
      <Protected>
        <div className="flex min-h-[50vh] items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-red-600" />
            <p className="text-slate-500 font-medium">Loading port details...</p>
          </div>
        </div>
      </Protected>
    );
  }

  if (status === "error" || !port) {
    return (
      <Protected>
        <div className="flex flex-col items-center justify-center min-h-[50vh] gap-6 text-center">
          <div className="h-16 w-16 rounded-full bg-red-100 flex items-center justify-center text-red-600">
            <ShieldAlert className="h-8 w-8" />
          </div>
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">Port Not Found</h2>
            <p className="text-slate-500 mt-2 max-w-md">
              {errorMsg}. Could not locate a port with UN/LOCODE: <span className="font-medium text-slate-700">{unlocode}</span>
            </p>
          </div>
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 rounded-xl bg-slate-100 px-5 py-2.5 text-sm font-medium hover:bg-slate-200 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" /> Go Back
          </button>
        </div>
      </Protected>
    );
  }

  return (
    <Protected>
      <main className="py-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <button
          onClick={() => router.back()}
          className="group mb-6 flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-1" />
          Back
        </button>

        {/* Global Header */}
        <header className="glass-card p-6 md:p-8 relative overflow-hidden mb-6">
          <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-[rgba(59,130,246,0.1)] blur-[50px]" />
          <div className="absolute -left-12 -bottom-12 h-40 w-40 rounded-full bg-[rgba(239,68,68,0.05)] blur-[50px]" />
          
          <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 text-white shadow-lg shadow-blue-500/30">
                <Anchor className="h-7 w-7" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
                  {port.port_name}
                  {port.unlocode && (
                    <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-sm font-semibold text-slate-600 ring-1 ring-inset ring-slate-200">
                      {port.unlocode}
                    </span>
                  )}
                </h1>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-slate-600 font-medium">
                  <span className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 rounded-md border border-slate-100">
                    <MapPin className="h-4 w-4 text-blue-500" />
                    {port.country_name || "Unknown Country"}
                  </span>
                  {port.latitude && port.longitude && (
                    <span className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 rounded-md border border-slate-100">
                      <Navigation className="h-4 w-4 text-emerald-500" />
                      {formatCoord(port.latitude, port.longitude)}
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <a
                href={`/map?lat=${port.latitude}&lon=${port.longitude}&zoom=12`}
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-white text-sm font-medium shadow hover:bg-blue-700 transition-colors"
                target="_blank"
                rel="noreferrer"
              >
                <Compass className="h-4 w-4" /> View Map
              </a>
            </div>
          </div>
        </header>

        {/* Detailed Sections Grid */}
        <div className="grid gap-6 grid-cols-1 md:grid-cols-2">

          {/* Name and Location */}
          <SectionCard title="Name and Location" icon={<Globe2 className="h-5 w-5 text-indigo-500" />}>
            <ListRow label="World Port Index Number" value={port.port_number} />
            <ListRow label="Region Name" value={`${port.region_name} -- ${port.region_number}`} />
            <ListRow label="Main Port Name" value={port.port_name} />
            <ListRow label="Alternate Port Name" value={port.alternate_name} />
            <ListRow label="UN/LOCODE" value={port.unlocode} />
            <ListRow label="Country" value={port.country_name} />
            <ListRow label="World Water Body" value={port.dod_water_body} />
            <ListRow label="Sailing Directions or Publication" value={port.publication_number} />
            <ListRow label="Standard Nautical Chart" value={port.chart_number} />
            <ListRow label="Digital Nautical Chart" value={port.dnc} />
            <ListRow label="NAVAREA" value={port.nav_area} />
          </SectionCard>

          {/* Physical Environment */}
          <SectionCard title="Physical Environment" icon={<MapPin className="h-5 w-5 text-emerald-500" />}>
            <ListRow label="Harbor Size" value={harborSizeMap[port.harbor_size || ''] || port.harbor_size} />
            <ListRow label="Harbor Type" value={harborTypeMap[port.harbor_type || ''] || port.harbor_type} />
            <ListRow label="Harbor Use" value={port.harbor_use || "Unknown"} />
            <ListRow label="Shelter Afforded" value={shelterMap[port.shelter || ''] || port.shelter} />
            <ListRow label="Entrance Restriction - Tide" value={boolString(port.er_tide)} />
            <ListRow label="Entrance Restriction - Heavy Swell" value={boolString(port.er_swell)} />
            <ListRow label="Entrance Restriction - Ice" value={boolString(port.er_ice)} />
            <ListRow label="Entrance Restriction - Other" value={boolString(port.er_other)} />
            <ListRow label="Overhead Limits" value={boolString(port.overhead_limits)} />
            <ListRow label="Good Holding Ground" value={boolString(port.good_holding_ground)} />
            <ListRow label="Turning Area" value={boolString(port.turning_area)} />
          </SectionCard>

          {/* Depths */}
          <SectionCard title="Depths" icon={<Waves className="h-5 w-5 text-cyan-500" />}>
            <div className="grid grid-cols-2 gap-4 pt-2">
              <DetailBox label="Tidal Range" value={port.tide} suffix="m" />
              <DetailBox label="Entrance Width" value={port.entrance_width} suffix="m" />
              <DetailBox label="Channel Depth" value={port.ch_depth} suffix="m" />
              <DetailBox label="Anchorage Depth" value={port.an_depth} suffix="m" />
              <DetailBox label="Cargo Pier Depth" value={port.cp_depth} suffix="m" />
              <DetailBox label="Oil Terminal Depth" value={port.ot_depth} suffix="m" />
              <DetailBox label="LNG Terminal Depth" value={port.lng_terminal_depth} suffix="m" />
            </div>
          </SectionCard>

          {/* Maximum Vessel Size */}
          <SectionCard title="Maximum Vessel Size" icon={<Ruler className="h-5 w-5 text-rose-500" />}>
            <div className="grid grid-cols-2 gap-4 pt-2">
              <DetailBox label="Max Vessel Length" value={port.max_vessel_length} suffix="m" />
              <DetailBox label="Max Vessel Beam" value={port.max_vessel_beam} suffix="m" />
              <DetailBox label="Max Vessel Draft" value={port.max_vessel_draft} suffix="m" />
              <DetailBox label="Offshore Max Length" value={port.off_max_vessel_length} suffix="m" />
              <DetailBox label="Offshore Max Beam" value={port.off_max_vessel_beam} suffix="m" />
              <DetailBox label="Offshore Max Draft" value={port.off_max_vessel_draft} suffix="m" />
            </div>
          </SectionCard>

          {/* Approach */}
          <SectionCard title="Approach" icon={<Navigation className="h-5 w-5 text-teal-600" />}>
            <ListRow label="Port Security" value={boolString(port.port_security)} />
            <ListRow label="ETA Message" value={boolString(port.eta_message)} />
            <ListRow label="UKC Mgmt System" value={boolString(port.ukc_mgmt_system)} />
            <ListRow label="Quarantine - Pratique" value={boolString(port.qt_pratique)} />
            <ListRow label="Quarantine - Sanitation" value={boolString(port.qt_sanitation)} />
            <ListRow label="Quarantine - Other" value={boolString(port.qt_other)} />
            <ListRow label="Traffic Separation Scheme" value={boolString(port.tss)} />
            <ListRow label="Vessel Traffic Service" value={boolString(port.vts)} />
            <ListRow label="First Port of Entry" value={boolString(port.first_port_of_entry)} />
            <ListRow label="US Representative" value={boolString(port.us_rep)} />
          </SectionCard>

          {/* Pilots, Tugs, Communications */}
          <SectionCard title="Pilots, Tugs, Communications" icon={<Radio className="h-5 w-5 text-orange-500" />}>
            <ListRow label="Pilotage - Compulsory" value={boolString(port.pt_compulsory)} />
            <ListRow label="Pilotage - Available" value={boolString(port.pt_available)} />
            <ListRow label="Pilotage - Local Assistance" value={boolString(port.pt_local_assist)} />
            <ListRow label="Pilotage - Advisable" value={boolString(port.pt_advisable)} />
            <ListRow label="Tugs - Salvage" value={boolString(port.tugs_salvage)} />
            <ListRow label="Tugs - Assistance" value={boolString(port.tugs_assist)} />
            <ListRow label="Communications - Telephone" value={boolString(port.cm_telephone)} />
            <ListRow label="Communications - Telefax" value={boolString(port.cm_telegraph)} />
            <ListRow label="Communications - Radio" value={boolString(port.cm_radio)} />
            <ListRow label="Communications - Radiotelephone" value={boolString(port.cm_radio_tel)} />
            <ListRow label="Communications - Airport" value={boolString(port.cm_air)} />
            <ListRow label="Communications - Rail" value={boolString(port.cm_rail)} />
            <ListRow label="Search and Rescue" value={boolString(port.search_and_rescue)} />
          </SectionCard>

          {/* Facilities */}
          <SectionCard title="Facilities" icon={<Package className="h-5 w-5 text-sky-500" />}>
            <ListRow label="Facilities - Wharves" value={boolString(port.lo_wharves)} />
            <ListRow label="Facilities - Anchorage" value={boolString(port.lo_anchor)} />
            <ListRow label="Facilities - Dang Cargo Anch" value={boolString(port.lo_dang_cargo)} />
            <ListRow label="Facilities - Med Mooring" value={boolString(port.lo_med_moor)} />
            <ListRow label="Facilities - Beach Mooring" value={boolString(port.lo_beach_moor)} />
            <ListRow label="Facilities - Ice Mooring" value={boolString(port.lo_ice_moor)} />
            <ListRow label="Facilities - RoRo" value={boolString(port.lo_roro)} />
            <ListRow label="Facilities - Solid Bulk" value={boolString(port.lo_solid_bulk)} />
            <ListRow label="Facilities - Liquid Bulk" value={boolString(port.lo_liquid_bulk)} />
            <ListRow label="Facilities - Container" value={boolString(port.lo_container)} />
            <ListRow label="Facilities - Breakbulk" value={boolString(port.lo_break_bulk)} />
            <ListRow label="Facilities - Oil Terminal" value={boolString(port.lo_oil_term)} />
            <ListRow label="Facilities - Other" value={boolString(port.lo_other)} />
            <ListRow label="Medical Facilities" value={boolString(port.med_facilities)} />
            <ListRow label="Garbage Disposal" value={boolString(port.garbage_disposal)} />
            <ListRow label="Chemical Holding Tank Disposal" value={boolString(port.cht)} />
            <ListRow label="Degaussing" value={boolString(port.degauss)} />
            <ListRow label="Dirty Ballast Disposal" value={boolString(port.dirty_ballast)} />
          </SectionCard>

          {/* Services, Cranes & Repairs Container */}
          <div className="flex flex-col gap-6">
            <SectionCard title="Cranes & Lifts" icon={<Hammer className="h-5 w-5 text-yellow-600" />}>
              <ListRow label="Cranes - Fixed" value={boolString(port.cr_fixed)} />
              <ListRow label="Cranes - Mobile" value={boolString(port.cr_mobile)} />
              <ListRow label="Cranes - Floating" value={boolString(port.cr_floating)} />
              <ListRow label="Cranes - Container" value={boolString(port.cranes_container)} />
              <ListRow label="Lifts - 100+ Tons" value={boolString(port.lifts_100)} />
              <ListRow label="Lifts - 50-100 Tons" value={boolString(port.lifts_50)} />
              <ListRow label="Lifts - 25-49 Tons" value={boolString(port.lifts_25)} />
              <ListRow label="Lifts - 0-24 Tons" value={boolString(port.lifts_0)} />
            </SectionCard>

            <SectionCard title="Services and Supplies" icon={<Wrench className="h-5 w-5 text-gray-500" />}>
              <ListRow label="Services - Longshoremen" value={boolString(port.sr_longshore)} />
              <ListRow label="Services - Electricity" value={boolString(port.sr_electrical)} />
              <ListRow label="Services - Steam" value={boolString(port.sr_steam)} />
              <ListRow label="Services - Navigational Equipment" value={boolString(port.sr_navig_equip)} />
              <ListRow label="Services - Electrical Repair" value={boolString(port.sr_elect_repair)} />
              <ListRow label="Services - Ice Breaking" value={boolString(port.sr_ice_breaking)} />
              <ListRow label="Services - Diving" value={boolString(port.sr_diving)} />
              <div className="my-2 border-b border-slate-100" />
              <ListRow label="Supplies - Provisions" value={boolString(port.su_provisions)} />
              <ListRow label="Supplies - Potable Water" value={boolString(port.su_water)} />
              <ListRow label="Supplies - Fuel Oil" value={boolString(port.su_fuel)} />
              <ListRow label="Supplies - Diesel Oil" value={boolString(port.su_diesel)} />
              <ListRow label="Supplies - Aviation Fuel" value={boolString(port.su_aviation_fuel)} />
              <ListRow label="Supplies - Deck" value={boolString(port.su_deck)} />
              <ListRow label="Supplies - Engine" value={boolString(port.su_engine)} />
              <div className="my-2 border-b border-slate-100" />
              <ListRow label="Repairs" value={repairMap[port.repair_code || ''] || port.repair_code} />
              <ListRow label="Dry Dock" value={boolString(port.drydock)} />
              <ListRow label="Railway" value={boolString(port.railway)} />
            </SectionCard>
          </div>

        </div>
      </main>
    </Protected>
  );
}

// ----------------------
// Base UI Components
// ----------------------

function SectionCard({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="glass-card bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
      <h3 className="flex items-center gap-2 text-lg font-semibold text-slate-900 border-b border-slate-100 pb-4 mb-4">
        {icon} 
        {title}
      </h3>
      <div className="space-y-1 text-sm">
        {children}
      </div>
    </section>
  );
}

function ListRow({ label, value }: { label: string; value?: string | number | null }) {
  const isUnknown = !value || value === "Unknown" || value === "N/A" || value === "U";
  return (
    <div className="flex justify-between items-center py-2 border-b border-slate-50 last:border-0 hover:bg-slate-50 px-2 rounded -mx-2 transition-colors">
      <span className="text-slate-500 font-medium">{label}</span>
      <span className={`font-semibold ${isUnknown ? 'text-slate-400 font-normal' : 'text-slate-900 text-right'}`}>
        {!value ? (
          "Unknown"
        ) : typeof value === 'string' && value.startsWith('http') ? (
          <a href={value} className="text-blue-600 hover:underline inline-flex items-center gap-1" target="_blank" rel="noreferrer">
            Link <Compass className="w-3 h-3"/>
          </a>
        ) : (
          value
        )}
      </span>
    </div>
  );
}

function DetailBox({ label, value, suffix }: { label: string; value?: string | number | null; suffix?: string }) {
  const displayValue = value && value !== "N/A" && value !== "Unknown" ? value : null;
  
  return (
    <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3.5 transition-colors hover:bg-slate-100">
      <div className="text-xs font-semibold text-slate-500 tracking-wider mb-1 tooltip" title={label}>{label}</div>
      <div className="text-lg font-bold text-slate-900">
        {displayValue ? (
          <>
            {displayValue}
            {suffix && <span className="text-sm font-medium text-slate-400 ml-1">{suffix}</span>}
          </>
        ) : (
          <span className="text-sm font-normal text-slate-400">Not spec.</span>
        )}
      </div>
    </div>
  );
}

// Format Coordinate String
function formatCoord(lat?: string, lon?: string) {
  if (!lat || !lon) return "N/A";
  
  const llat = Number.parseFloat(lat);
  const llon = Number.parseFloat(lon);
  
  if (!isNaN(llat) && !isNaN(llon)) {
    const format = (val: number, isLat: boolean) => {
      const absVal = Math.abs(val);
      const d = Math.floor(absVal);
      const m = Math.floor((absVal - d) * 60);
      const dir = isLat ? (val >= 0 ? 'N' : 'S') : (val >= 0 ? 'E' : 'W');
      return `${d}°${m}' ${dir}`;
    };
    return `${format(llat, true)}, ${format(llon, false)}`;
  }
  
  return `${lat}, ${lon}`;
}
