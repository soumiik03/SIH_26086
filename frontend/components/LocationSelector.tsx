import type { Block, District, PanchayatListItem } from "@/types/api";
import { ChevronDown, MapPin } from "lucide-react";
import { LoadingState } from "./LoadingState";
import { ErrorState } from "./ErrorState";
import { EmptyState } from "./EmptyState";

interface Props {
  districts: District[];
  blocks: Block[];
  panchayats: PanchayatListItem[];
  districtId: string;
  blockId: string;
  panchayatId: string;
  loadingPanchayats: boolean;
  error?: string;
  onDistrictChange: (id: string) => void;
  onBlockChange: (id: string) => void;
  onPanchayatChange: (id: string) => void;
  onRetry: () => void;
}

function SelectField({ label, value, onChange, children, disabled }: { label: string; value: string; onChange: (value: string) => void; children: React.ReactNode; disabled?: boolean }) {
  return <label className="block text-sm font-semibold text-ink"><span className="mb-2 block text-xs uppercase tracking-[.16em] text-slate-500">{label}</span><span className="relative block"><select value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} className="w-full appearance-none border border-slate-200 bg-white px-3 py-3 pr-10 text-sm font-medium outline-none transition focus:border-moss focus:ring-2 focus:ring-moss/15 disabled:cursor-not-allowed disabled:bg-slate-100">{children}</select><ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" /></span></label>;
}

export function LocationSelector(props: Props) {
  const selectedDistrict = props.districts.find((district) => district.district_id === props.districtId);
  return <section className="border border-slate-200 bg-white p-5 shadow-[0_8px_30px_rgba(23,35,31,.04)] sm:p-6"><div className="mb-5 flex items-start gap-3"><div className="flex h-9 w-9 items-center justify-center bg-[#e4f0e8] text-moss"><MapPin className="h-4 w-4" /></div><div><h2 className="font-display text-lg font-semibold">Choose an observation area</h2><p className="mt-1 text-sm text-slate-500">Select a supported location to load verified forecast information.</p></div></div><div className="grid gap-4 md:grid-cols-3"><SelectField label="District" value={props.districtId} onChange={props.onDistrictChange} disabled={!props.districts.length}><option value="">Select district</option>{props.districts.map((district) => <option key={district.district_id} value={district.district_id}>{district.district_name}</option>)}</SelectField><SelectField label="Block" value={props.blockId} onChange={props.onBlockChange} disabled={!selectedDistrict}><option value="">Select block</option>{props.blocks.filter((block) => block.district_id === props.districtId).map((block) => <option key={block.block_id} value={block.block_id}>{block.block_name}</option>)}</SelectField><SelectField label="Panchayat" value={props.panchayatId} onChange={props.onPanchayatChange} disabled={!props.blockId || props.loadingPanchayats}><option value="">Select Panchayat</option>{props.panchayats.map((panchayat) => <option key={panchayat.panchayat_id} value={panchayat.panchayat_id}>{panchayat.panchayat_name}</option>)}</SelectField></div>{props.loadingPanchayats && <LoadingState label="Loading Panchayats..." />}{props.error && <div className="mt-4"><ErrorState message={props.error} onRetry={props.onRetry} /></div>}{props.blockId && !props.loadingPanchayats && !props.error && !props.panchayats.length && <div className="mt-4"><EmptyState message="No Panchayat data available for this block." /></div>}</section>;
}