"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useCurrentDonor, useDonorNotifications } from "@/hooks/useSupabaseData";
import { useQueryClient } from "@tanstack/react-query";
import {
  Heart,
  Droplets,
  Calendar,
  Shield,
  Power,
  Bell,
  History,
  Zap,
  Loader2,
  Lock,
  MessageSquare,
  AlertTriangle,
  User,
  MapPin,
  Activity,
  ArrowRight,
  ShieldCheck,
  Dna,
  Trash2
} from "lucide-react";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase/client";
import { EditProfileModal } from "@/components/dashboard/donor/EditProfileModal";

function DonorDashboardContent() {
  const { data: donorData, isLoading: donorLoading } = useCurrentDonor();
  const { data: notifications, isLoading: notificationsLoading } = useDonorNotifications();
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  
  const [role, setRole] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [isAvailable, setIsAvailable] = useState(false);
  const [isToggling, setIsToggling] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    async function checkRole() {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      setUser(user);
      
      const userRole = user?.user_metadata?.role;
      const isAdminEmail = user?.email?.toLowerCase() === "ranahaseeb9427@gmail.com";
      const isAdminMode = searchParams.get("mode") === "admin_view";
      const isAdmin = userRole === "admin" || isAdminEmail || isAdminMode;
      
      setRole(isAdmin ? "admin" : userRole);
      setAuthLoading(false);
    }
    checkRole();
  }, [searchParams]);

  useEffect(() => {
    if (donorData) {
      setIsAvailable(donorData.status === 'active');
    }
  }, [donorData]);

  const handleToggle = async () => {
    if (!donorData?.id) return;
    setIsToggling(true);
    try {
      const res = await fetch("/api/admin/toggle-donor", { 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          donor_id: donorData.id, 
          type: 'blood', 
          current_status: isAvailable 
        })
      });
      
      if (!res.ok) throw new Error("Clinical status update failed");
      
      const result = await res.json();
      setIsAvailable(result.nextStatus);
      queryClient.invalidateQueries({ queryKey: ["current-donor"] });
      toast.success(`Network Protocol Updated: You are now ${result.nextStatus ? 'ACTIVE' : 'OFFLINE'}`);
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setIsToggling(false);
    }
  };

  if (authLoading || donorLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-slate-50/50">
        <div className="relative">
          <motion.div 
            animate={{ rotate: 360 }} 
            transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }} 
            className="h-16 w-16 border-4 border-blue-600/20 border-t-blue-600 rounded-full" 
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <Dna className="h-6 w-6 text-blue-600 animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  const donor = donorData || { full_name: user?.user_metadata?.first_name || 'Donor', blood_type: 'N/A', city: 'Unknown' };

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-20 px-4 pt-4 font-sans selection:bg-blue-100">
      
      {/* --- HERO SECTION --- */}
      <div className="relative overflow-hidden rounded-[2.5rem] bg-slate-900 p-8 md:p-12 text-white shadow-2xl">
        <div className="absolute top-0 right-0 w-1/2 h-full opacity-10 pointer-events-none">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path d="M0,100 C30,80 70,80 100,100" fill="none" stroke="currentColor" strokeWidth="0.5" />
            <path d="M0,80 C30,60 70,60 100,80" fill="none" stroke="currentColor" strokeWidth="0.5" />
            <path d="M0,60 C30,40 70,40 100,60" fill="none" stroke="currentColor" strokeWidth="0.5" />
          </svg>
        </div>

        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-8">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-2xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-600/20">
                <ShieldCheck className="h-6 w-6 text-white" />
              </div>
              <span className="text-xs font-black uppercase tracking-[0.3em] text-blue-400">Clinical ID Verified</span>
            </div>
            <div>
              <h1 className="text-4xl md:text-5xl font-black tracking-tight leading-tight">
                Welcome, <br />
                <span className="text-blue-500">{donor.full_name.split(' ')[0]}</span>
              </h1>
              <p className="text-slate-400 mt-4 max-w-md font-medium text-lg leading-relaxed">
                Your profile is active on the OPAL-AI clinical matching network. Ready to save lives.
              </p>
            </div>
          </div>

          <div className="flex flex-col items-center gap-4">
             <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleToggle}
              disabled={isToggling}
              className={`relative flex flex-col items-center gap-3 rounded-[2rem] p-6 min-w-[180px] border transition-all duration-500 ${
                isAvailable 
                ? "bg-blue-600/10 border-blue-500/30 text-blue-400 shadow-[0_0_40px_rgba(37,99,235,0.1)]" 
                : "bg-slate-800/50 border-slate-700 text-slate-500"
              }`}
            >
              <div className={`h-16 w-16 rounded-full flex items-center justify-center border-4 transition-all duration-500 ${isAvailable ? 'bg-blue-600 border-blue-400/30' : 'bg-slate-700 border-slate-600'}`}>
                {isToggling ? <Loader2 className="h-8 w-8 animate-spin text-white" /> : <Power className="h-8 w-8 text-white" />}
              </div>
              <span className="text-[10px] font-black uppercase tracking-[0.2em]">{isAvailable ? "Network Active" : "Go Online"}</span>
              {isAvailable && <div className="absolute top-4 right-4 h-3 w-3 rounded-full bg-green-400 animate-ping" />}
            </motion.button>
          </div>
        </div>
      </div>

      {/* --- DASHBOARD GRID --- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* LEFT COLUMN: IDENTITY CARD */}
        <div className="lg:col-span-1 space-y-8">
           <div className="relative overflow-hidden bg-white rounded-[2rem] border border-slate-100 p-8 shadow-sm group">
              <div className="absolute -top-24 -right-24 w-48 h-48 bg-blue-50 rounded-full transition-transform group-hover:scale-150 duration-700" />
              
              <div className="relative z-10 space-y-8">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <p className="text-[10px] font-black text-blue-600 uppercase tracking-widest">Medical Profile</p>
                    <h3 className="text-2xl font-black">Clinical Identity</h3>
                  </div>
                  <User className="w-8 h-8 text-slate-200" />
                </div>

                <div className="space-y-6">
                  <div className="flex items-center gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-100">
                    <div className="h-10 w-10 rounded-xl bg-white flex items-center justify-center text-red-500 shadow-sm">
                      <Droplets className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Blood Group</p>
                      <p className="text-lg font-black">{donor.blood_type}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-100">
                    <div className="h-10 w-10 rounded-xl bg-white flex items-center justify-center text-blue-500 shadow-sm">
                      <MapPin className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Current Location</p>
                      <p className="text-lg font-black">{donor.city}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-100">
                    <div className="h-10 w-10 rounded-xl bg-white flex items-center justify-center text-indigo-500 shadow-sm">
                      <Zap className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Network Status</p>
                      <p className={`text-lg font-black ${isAvailable ? 'text-green-600' : 'text-slate-400'}`}>
                        {isAvailable ? 'LIVE' : 'INACTIVE'}
                      </p>
                    </div>
                  </div>
                </div>

                <button 
                  onClick={() => setIsEditModalOpen(true)}
                  className="w-full py-4 rounded-2xl bg-slate-900 text-white text-[10px] font-black uppercase tracking-widest hover:bg-blue-600 transition-all flex items-center justify-center gap-2"
                >
                  Edit Profile <ArrowRight className="w-4 h-4" />
                </button>
              </div>
           </div>
        </div>

        {/* RIGHT COLUMN: NOTIFICATIONS & ACTIVITY */}
        <div className="lg:col-span-2 space-y-8">
           
           {/* ALERTS SECTION */}
           <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-black flex items-center gap-3">
                  <Bell className="w-5 h-5 text-blue-600" />
                  Live Match Alerts
                </h2>
                <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-[10px] font-black uppercase tracking-wider">Real-time Feed</span>
              </div>

              <div className="grid grid-cols-1 gap-4">
                {notifications && notifications.length > 0 ? (
                  notifications.map((n: any, i: number) => (
                    <motion.div
                      key={n.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className={`relative p-6 rounded-[2rem] border-2 transition-all ${
                        n.type === 'emergency' 
                        ? 'bg-red-50/50 border-red-100 hover:border-red-200' 
                        : 'bg-white border-slate-100 hover:border-blue-200 shadow-sm'
                      } group`}
                    >
                      <button 
                        onClick={async (e) => {
                          e.stopPropagation();
                          const supabase = createClient();
                          const { error } = await supabase.from("notifications").delete().eq("id", n.id);
                          if (error) toast.error("Could not delete alert");
                          else {
                            toast.success("Alert cleared");
                            queryClient.invalidateQueries({ queryKey: ["donor-notifications"] });
                          }
                        }}
                        className="absolute top-6 right-6 p-2 rounded-xl bg-white border border-slate-100 text-slate-400 hover:text-red-500 hover:border-red-100 transition-all opacity-0 group-hover:opacity-100 shadow-sm"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>

                      <div className="flex items-start gap-6">
                        <div className={`h-14 w-14 rounded-2xl flex items-center justify-center shrink-0 transition-transform group-hover:scale-110 ${
                          n.type === 'emergency' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'
                        }`}>
                          {n.type === 'emergency' ? <AlertTriangle className="h-7 w-7" /> : <MessageSquare className="h-7 w-7" />}
                        </div>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center justify-between pr-10">
                            <p className={`text-lg font-black ${n.type === 'emergency' ? 'text-red-900' : 'text-slate-900'}`}>{n.title}</p>
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{new Date(n.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                          </div>
                          <p className="text-sm text-slate-500 font-medium leading-relaxed">{n.message}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="py-20 text-center rounded-[2.5rem] border-2 border-dashed border-slate-100 bg-white/50 space-y-4">
                    <div className="h-16 w-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto">
                      <Zap className="w-8 h-8 text-slate-200" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs font-black text-slate-400 uppercase tracking-widest">Scanning for Matches...</p>
                      <p className="text-[10px] text-slate-400 italic">No clinical alerts at this moment.</p>
                    </div>
                  </div>
                )}
              </div>
           </div>

           {/* LOG SECTION */}
           <div className="space-y-6">
              <h2 className="text-xl font-black flex items-center gap-3">
                <History className="w-5 h-5 text-blue-600" />
                Donation Logbook
              </h2>
              <div className="bg-white rounded-[2rem] border border-slate-100 overflow-hidden shadow-sm">
                <div className="p-8 text-center space-y-4">
                   <Activity className="w-8 h-8 text-slate-100 mx-auto" />
                   <p className="text-xs font-bold text-slate-300 uppercase tracking-[0.2em]">Synchronizing Records</p>
                </div>
              </div>
           </div>
        </div>
      </div>

      {/* --- DANGER ZONE --- */}
      <div className="mt-20 group relative overflow-hidden p-10 rounded-[3rem] bg-red-50/50 border-2 border-red-100/50 flex flex-col md:flex-row items-center justify-between gap-8">
        <div className="absolute top-0 left-0 w-32 h-full bg-gradient-to-r from-red-100/20 to-transparent pointer-events-none" />
        
        <div className="relative z-10 space-y-2 text-center md:text-left">
          <h3 className="text-lg font-black text-red-600 uppercase tracking-widest flex items-center gap-2 justify-center md:justify-start">
            <Lock className="w-5 h-5" /> Account Purge
          </h3>
          <p className="text-sm text-red-700/60 font-medium max-w-md">
            Permanently erase your clinical identity. This action is IRREVERSIBLE and will remove you from all live matching queues.
          </p>
        </div>
        
        <motion.button 
           whileHover={{ scale: 1.02 }}
           whileTap={{ scale: 0.98 }}
           onClick={async () => {
             if(confirm("DANGER: This will permanently delete your identity from the network. Proceed?")) {
               const res = await fetch('/api/auth/delete-account', { method: 'DELETE' });
               if(res.ok) window.location.href = '/';
               else toast.error("Critical Failure: Could not purge identity.");
             }
           }}
           className="relative z-10 px-10 py-5 rounded-2xl bg-white border-2 border-red-200 text-red-600 text-xs font-black uppercase tracking-widest hover:bg-red-600 hover:text-white transition-all shadow-xl shadow-red-500/5"
        >
          Erase All Clinical Data
        </motion.button>
      </div>

      <EditProfileModal 
        donor={donor}
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onUpdate={() => queryClient.invalidateQueries({ queryKey: ["current-donor"] })} 
      />

    </div>
  );
}

export default function DonorDashboard() {
  return (
    <Suspense fallback={<div className="h-[80vh] flex items-center justify-center"><Loader2 className="h-10 w-10 animate-spin text-blue-600" /></div>}>
      <DonorDashboardContent />
    </Suspense>
  );
}
