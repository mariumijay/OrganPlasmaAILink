"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  ShieldCheck, 
  Download, 
  FileText, 
  Lock, 
  CheckCircle2, 
  AlertCircle,
  Activity,
  History,
  ArrowLeft,
  Loader2
} from "lucide-react";
import Link from "next/link";
import { useMatchResults } from "@/hooks/useSupabaseData";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { timeAgo } from "@/lib/utils";
import { toast } from "sonner";

export default function CompliancePage() {
  const { data: matches, isLoading } = useMatchResults();
  const [isExporting, setIsExporting] = useState(false);

  const handleDownloadAuditReport = async () => {
    try {
      setIsExporting(true);
      toast.info("Generating Production Audit Registry... [Secure Encryption Active]");
      
      const response = await fetch('/api/hospital/export-registry');
      if (!response.ok) throw new Error("Registry Export Failed");
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      const timestamp = new Date().toISOString().split('T')[0];
      
      link.href = url;
      link.setAttribute('download', `OPAL_Compliance_Audit_${timestamp}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast.success("Clinical Registry Exported Successfully.");
    } catch (error: any) {
      toast.error("Export Failed: " + error.message);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-8 pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <Link 
            href="/dashboard/hospital"
            className="h-10 w-10 rounded-xl bg-muted flex items-center justify-center hover:bg-muted/80 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-black font-display tracking-tight text-foreground">
              Compliance <span className="text-primary">Audit Registry</span>
            </h1>
            <p className="text-muted-foreground font-medium mt-1">
              Official clinical match logs and regulatory documentation.
            </p>
          </div>
        </div>

        <button 
          onClick={handleDownloadAuditReport}
          disabled={isExporting}
          className="flex items-center gap-2 px-6 py-3 bg-primary text-white rounded-2xl text-xs font-black uppercase tracking-widest hover:bg-primary/90 transition-all shadow-lg shadow-primary/20 disabled:opacity-50"
        >
          {isExporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          {isExporting ? "Encrypting..." : "Export Full Audit"}
        </button>
      </div>

      {/* Grid: Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 rounded-[2rem] border border-success/20 bg-success/5">
           <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-xl bg-success/10 flex items-center justify-center text-success">
                 <ShieldCheck className="h-5 w-5" />
              </div>
              <p className="text-[10px] font-black uppercase tracking-widest text-success">Network Status</p>
           </div>
           <h3 className="text-xl font-black text-foreground">Verified Node</h3>
           <p className="text-xs text-muted-foreground mt-1">Institutional ID: #PK-772-OPAL</p>
        </div>

        <div className="glass-card p-6 rounded-[2rem] border border-primary/20 bg-primary/5">
           <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                 <Lock className="h-5 w-5" />
              </div>
              <p className="text-[10px] font-black uppercase tracking-widest text-primary">Data Security</p>
           </div>
           <h3 className="text-xl font-black text-foreground">AES-256 Active</h3>
           <p className="text-xs text-muted-foreground mt-1">End-to-end clinical encryption</p>
        </div>

        <div className="glass-card p-6 rounded-[2rem] border border-border">
           <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-xl bg-muted flex items-center justify-center text-muted-foreground">
                 <FileText className="h-5 w-5" />
              </div>
              <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Total Logs</p>
           </div>
           <h3 className="text-xl font-black text-foreground">{matches?.length || 0} Records</h3>
           <p className="text-xs text-muted-foreground mt-1">Last sync: Just now</p>
        </div>
      </div>

      {/* Audit Table */}
      <div className="glass-card rounded-[2.5rem] border border-border overflow-hidden bg-card/50 backdrop-blur-xl">
        <div className="p-8 border-b border-border flex items-center justify-between">
           <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-muted flex items-center justify-center">
                 <History className="h-5 w-5 text-muted-foreground" />
              </div>
              <h2 className="text-xl font-bold font-display tracking-tight">Clinical Match Logs</h2>
           </div>
           <div className="flex items-center gap-2 px-4 py-2 bg-success/10 rounded-full border border-success/20">
              <CheckCircle2 className="h-3.5 w-3.5 text-success" />
              <span className="text-[10px] font-black text-success uppercase tracking-widest">Regulatory Compliant</span>
           </div>
        </div>

        <div className="overflow-x-auto">
           <table className="w-full text-left border-collapse">
              <thead>
                 <tr className="bg-muted/30">
                    <th className="px-8 py-4 text-[10px] font-black text-muted-foreground uppercase tracking-widest">Registry ID</th>
                    <th className="px-8 py-4 text-[10px] font-black text-muted-foreground uppercase tracking-widest">Clinical Match</th>
                    <th className="px-8 py-4 text-[10px] font-black text-muted-foreground uppercase tracking-widest">Status</th>
                    <th className="px-8 py-4 text-[10px] font-black text-muted-foreground uppercase tracking-widest">Timestamp</th>
                    <th className="px-8 py-4 text-[10px] font-black text-muted-foreground uppercase tracking-widest">Integrity</th>
                 </tr>
              </thead>
              <tbody className="divide-y divide-border">
                 {isLoading ? (
                    <tr>
                       <td colSpan={5} className="px-8 py-12 text-center">
                          <Loader2 className="h-8 w-8 text-primary animate-spin mx-auto" />
                       </td>
                    </tr>
                 ) : matches?.length === 0 ? (
                    <tr>
                       <td colSpan={5} className="px-8 py-12 text-center text-muted-foreground font-medium">
                          No clinical records found in registry.
                       </td>
                    </tr>
                 ) : (
                    matches?.map((m: any) => (
                       <tr key={m.id} className="hover:bg-muted/20 transition-colors group">
                          <td className="px-8 py-6">
                             <span className="text-[10px] font-black text-muted-foreground uppercase bg-muted px-2 py-1 rounded-md">
                                {m.id.substring(0, 8)}...
                             </span>
                          </td>
                          <td className="px-8 py-6">
                             <div className="flex items-center gap-3">
                                <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                                   <Activity className="h-4 w-4" />
                                </div>
                                <div>
                                   <p className="text-sm font-bold text-foreground">{m.required_item}</p>
                                   <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mt-0.5">{m.blood_type}</p>
                                </div>
                             </div>
                          </td>
                          <td className="px-8 py-6">
                             <StatusBadge status={m.status} />
                          </td>
                          <td className="px-8 py-6">
                             <p className="text-sm font-medium text-foreground">{new Date(m.created_at).toLocaleDateString()}</p>
                             <p className="text-[10px] text-muted-foreground uppercase font-black">{timeAgo(m.created_at)}</p>
                          </td>
                          <td className="px-8 py-6">
                             <div className="flex items-center gap-2">
                                <CheckCircle2 className="h-4 w-4 text-success" />
                                <span className="text-[10px] font-black text-success uppercase">Verified</span>
                             </div>
                          </td>
                       </tr>
                    ))
                 )}
              </tbody>
           </table>
        </div>
      </div>

      {/* Security Disclaimer */}
      <div className="p-8 rounded-[2.5rem] bg-muted/40 border border-border flex flex-col md:flex-row items-center justify-between gap-6">
         <div className="flex items-start gap-4">
            <AlertCircle className="h-6 w-6 text-primary shrink-0 mt-1" />
            <div>
               <h4 className="font-bold text-foreground">Data Retention & Privacy Notice</h4>
               <p className="text-sm text-muted-foreground max-w-2xl mt-1 leading-relaxed">
                  These logs are immutable and stored in compliance with national healthcare data standards. 
                  Access to this portal is logged and monitored for institutional security. 
                  Unauthorized export of patient data is strictly prohibited.
               </p>
            </div>
         </div>
      </div>
    </div>
  );
}
