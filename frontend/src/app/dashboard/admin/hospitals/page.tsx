"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
  Building2, 
  CheckCircle, 
  XCircle, 
  ShieldCheck, 
  Clock, 
  Search,
  ExternalLink,
  MapPin,
  Phone,
  FileText,
  Loader2,
  Filter,
  Activity
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

export default function AdminHospitalsPage() {
  const [hospitals, setHospitals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const supabase = createClient();

  useEffect(() => {
    fetchHospitals();
  }, [filter]);

  async function fetchHospitals() {
    setLoading(true);
    try {
      // Use the Admin API instead of direct Supabase query to bypass RLS
      const res = await fetch("/api/admin/hospitals");
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Failed to fetch clinical network data");
      }
      
      const data = await res.json();
      
      // Filter data locally based on the selected tab
      let filtered = data || [];
      if (filter === "pending") {
        filtered = filtered.filter((h: any) => !h.is_verified);
      } else if (filter === "verified") {
        filtered = filtered.filter((h: any) => h.is_verified);
      }
      
      setHospitals(filtered);
    } catch (err: any) {
      toast.error(err.message || "Failed to fetch hospitals");
      console.error("ADMIN FETCH ERROR:", err);
    } finally {
      setLoading(false);
    }
  }

  async function toggleVerification(id: string, currentStatus: boolean, email?: string) {
    try {
      if (currentStatus === false) {
        const { error } = await supabase
          .from("hospitals")
          .update({ 
            is_verified: true,
            approval_status: "verified",
            approved_at: new Date().toISOString()
          })
          .eq("id", id);
        if (error) throw error;
        toast.success("Hospital verified successfully");
      } else {
        const { error: dbError } = await supabase.from("hospitals").delete().eq("id", id);
        if (dbError) throw dbError;
        if (email) {
          fetch('/api/admin/purge-hospital-auth', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email })
          });
        }
        toast.success("Hospital profile and login credentials purged.");
      }
      fetchHospitals();
      if (selectedHospital) setSelectedHospital(null);
    } catch (err: any) {
      toast.error(err.message || "Action failed");
    }
  }

  const filteredHospitals = hospitals.filter(h => 
    h.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    h.license_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    h.city?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const [selectedHospital, setSelectedHospital] = useState<any>(null);

  return (
    <div className="space-y-8">
      {/* Header Secion */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
            <Building2 className="h-8 w-8 text-primary" />
            Clinical Network Audit
          </h1>
          <p className="text-muted-foreground mt-1 font-medium">Verify and manage registered healthcare institutions.</p>
        </div>
        
        <div className="flex items-center gap-2 bg-muted/30 p-1 rounded-xl border border-border">
          <button 
            onClick={() => setFilter("pending")}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${filter === "pending" ? "bg-white shadow-sm text-primary" : "text-muted-foreground hover:text-foreground"}`}
          >
            Pending Approval ({hospitals.filter(h => !h.is_verified).length})
          </button>
          <button 
            onClick={() => setFilter("verified")}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${filter === "verified" ? "bg-white shadow-sm text-primary" : "text-muted-foreground hover:text-foreground"}`}
          >
            Verified Institutions
          </button>
          <button 
            onClick={() => setFilter("all")}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${filter === "all" ? "bg-white shadow-sm text-primary" : "text-muted-foreground hover:text-foreground"}`}
          >
            All
          </button>
        </div>
      </div>

      {/* Global Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input 
          type="text" 
          placeholder="Search by name, city or license number..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-card border-border rounded-2xl py-4 pl-12 pr-4 outline-none focus:ring-2 focus:ring-primary/20 transition-all font-medium"
        />
      </div>

      {/* Hospital Feed */}
      {loading ? (
        <div className="h-64 flex flex-col items-center justify-center gap-4 text-muted-foreground border-2 border-dashed border-border rounded-3xl">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm font-bold uppercase tracking-widest">Hydrating Clinical Data...</p>
        </div>
      ) : filteredHospitals.length === 0 ? (
        <div className="h-64 flex flex-col items-center justify-center gap-4 border-2 border-dashed border-border rounded-3xl bg-muted/10">
          <div className="h-16 w-16 rounded-3xl bg-muted flex items-center justify-center">
            <CheckCircle className="h-8 w-8 text-muted-foreground" />
          </div>
          <div className="text-center">
            <p className="font-bold">No hospitals found</p>
            <p className="text-sm text-muted-foreground mt-1">Clear filters or check back later for new registrations.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <AnimatePresence mode="popLayout">
            {filteredHospitals.map((hospital) => (
              <motion.div
                layout
                key={hospital.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="bg-card border border-border rounded-3xl overflow-hidden shadow-sm hover:shadow-xl hover:border-primary/20 transition-all group cursor-pointer"
                onClick={() => setSelectedHospital(hospital)}
              >
                <div className="p-6 space-y-6">
                  {/* Status & Name */}
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h2 className="text-xl font-bold tracking-tight">{hospital.name || hospital.hospital_name || "Unknown Hospital"}</h2>
                        {hospital.is_verified ? (
                          <ShieldCheck className="h-5 w-5 text-green-500" />
                        ) : (
                          <Clock className="h-5 w-5 text-amber-500 animate-pulse" />
                        )}
                      </div>
                      <p className="text-xs font-black uppercase text-primary tracking-widest">
                        {hospital.hospital_type} Institute
                      </p>
                    </div>
                    <div className={cn(
                      "px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest",
                      hospital.is_verified ? "bg-green-500/10 text-green-600" : "bg-amber-500/10 text-amber-600"
                    )}>
                      {hospital.is_verified ? "Verified" : "Pending Audit"}
                    </div>
                  </div>

                  {/* License Info */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-muted/30 p-3 rounded-2xl border border-border/50">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1 flex items-center gap-1">
                        <FileText className="h-3 w-3" /> License Number
                      </p>
                      <p className="text-sm font-mono font-bold">{hospital.license_number}</p>
                    </div>
                    <div className="bg-muted/30 p-3 rounded-2xl border border-border/50">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1 flex items-center gap-1">
                        <MapPin className="h-3 w-3" /> Location
                      </p>
                      <p className="text-sm font-bold truncate">{hospital.city}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground">
                    <CheckCircle className="h-3 w-3" /> Click to view full clinical details
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* AUDIT MODAL */}
      <AnimatePresence>
        {selectedHospital && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-md bg-slate-950/40">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="bg-white w-full max-w-2xl rounded-[2.5rem] shadow-2xl overflow-hidden border border-white/20"
            >
              <div className="p-8 space-y-8">
                {/* Modal Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-5">
                    <div className="h-16 w-16 rounded-[1.25rem] bg-primary/10 flex items-center justify-center">
                       <Building2 className="h-8 w-8 text-primary" />
                    </div>
                    <div>
                      <h2 className="text-3xl font-black tracking-tight">{selectedHospital.name || selectedHospital.hospital_name || "Unknown Hospital"}</h2>
                      <p className="text-xs font-black uppercase tracking-widest text-primary flex items-center gap-2">
                        Institutional Verification Audit
                      </p>
                    </div>
                  </div>
                  <button 
                    onClick={() => setSelectedHospital(null)}
                    className="h-10 w-10 rounded-full bg-muted flex items-center justify-center hover:bg-slate-200 transition-all"
                  >
                    <XCircle className="h-5 w-5 text-slate-400" />
                  </button>
                </div>

                {/* Audit Grid */}
                <div className="grid grid-cols-2 gap-6">
                  {/* Credentials */}
                  <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100 flex flex-col justify-between">
                    <div>
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest block mb-3">Legal Credentials</label>
                      <div className="flex items-center gap-2 text-slate-900 font-bold">
                        <ShieldCheck className="h-5 w-5 text-primary" />
                        {selectedHospital.license_number}
                      </div>
                    </div>
                    <p className="text-[10px] font-black uppercase text-slate-400 mt-4">
                      Administrator: <span className="text-slate-600">{selectedHospital.admin_name || "N/A"}</span>
                    </p>
                  </div>

                  {/* Location Info */}
                  <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100">
                    <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest block mb-3">Geospatial Mapping</label>
                    <div className="flex items-center gap-2 text-slate-900 font-bold mb-1">
                      <MapPin className="h-5 w-5 text-primary" />
                      {selectedHospital.city}
                    </div>
                    <p className="text-[10px] text-slate-500 font-medium leading-relaxed">
                      {selectedHospital.full_address || "Address details not provided"}
                    </p>
                  </div>

                  {/* Contact Info */}
                  <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100">
                    <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest block mb-3">Facility Contact</label>
                    <div className="flex items-center gap-2 text-slate-900 font-bold mb-1">
                      <Phone className="h-5 w-5 text-primary" />
                      {selectedHospital.phone || "N/A"}
                    </div>
                    <p className="text-[10px] text-slate-500 font-medium truncate">
                      {selectedHospital.contact_email}
                    </p>
                  </div>

                  {/* Registration Status */}
                  <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100">
                    <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest block mb-3">Registration Status</label>
                    <div className="flex items-center gap-2 font-black text-amber-500 mb-1 italic">
                      <Activity className="h-5 w-5" />
                      {selectedHospital.is_verified ? "Verified Node" : "Pending Oversight"}
                    </div>
                    <p className="text-[10px] text-slate-400 font-bold uppercase">Registered: {new Date(selectedHospital.created_at).toLocaleDateString()}</p>
                  </div>
                </div>

                {/* Footer Actions */}
                <div className="flex items-center gap-4">
                  <button 
                    onClick={() => toggleVerification(selectedHospital.id, selectedHospital.is_verified, selectedHospital.contact_email)}
                    className={cn(
                      "flex-1 py-5 rounded-[1.5rem] font-bold flex items-center justify-center gap-3 shadow-xl transition-all",
                      selectedHospital.is_verified 
                        ? "bg-slate-900 text-white hover:bg-slate-800" 
                        : "bg-primary text-white hover:brightness-110 shadow-primary/20"
                    )}
                  >
                    <CheckCircle className="h-5 w-5" />
                    {selectedHospital.is_verified ? "Revoke Node Authorization" : "Confirm & Authorize Node"}
                  </button>
                  <button 
                    onClick={() => setSelectedHospital(null)}
                    className="px-8 py-5 rounded-[1.5rem] bg-slate-100 font-bold text-slate-600 hover:bg-slate-200 transition-all"
                  >
                    Close Audit
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Utility for conditional classes
function cn(...classes: string[]) {
  return classes.filter(Boolean).join(" ");
}
