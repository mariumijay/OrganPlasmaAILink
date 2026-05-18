"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ArrowLeft, PlusCircle, User, Droplet, MapPin, Activity, Zap } from "lucide-react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

export default function AddDonorPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [donorType, setDonorType] = useState<"blood" | "organ">("blood");
  
  const [formData, setFormData] = useState({
    full_name: "",
    age: "",
    blood_type: "A+",
    city: "",
    latitude: "",
    longitude: "",
    organs_available: [] as string[],
  });

  const availableOrgansList = ["Heart", "Lung", "Kidney", "Liver", "Pancreas", "Cornea"];

  const handleOrganToggle = (organ: string) => {
    setFormData(prev => ({
      ...prev,
      organs_available: prev.organs_available.includes(organ)
        ? prev.organs_available.filter(o => o !== organ)
        : [...prev.organs_available, organ]
    }));
  };

  const getLocation = () => {
    if (!navigator.geolocation) {
      toast.error("Geolocation is not supported by your browser");
      return;
    }

    toast.info("Fetching current location...");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setFormData(prev => ({
          ...prev,
          latitude: position.coords.latitude.toString(),
          longitude: position.coords.longitude.toString()
        }));
        toast.success("Coordinates updated from GPS");
      },
      (error) => {
        toast.error(`Location Error: ${error.message}`);
      }
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch("/api/hospital/upload-inventory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          donor_type: donorType,
        }),
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Upload failed");

      toast.success("Inventory successfully uploaded to the network!");
      router.push("/dashboard/hospital");
    } catch (error: any) {
      toast.error(`Failed to upload: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/hospital" className="p-3 bg-card border border-border rounded-full hover:bg-muted transition-colors">
            <ArrowLeft className="w-5 h-5 text-foreground" />
          </Link>
          <div>
            <h1 className="text-3xl font-black font-display tracking-tight text-foreground">Upload Inventory</h1>
            <p className="text-muted-foreground font-medium mt-1">Register available blood or organ donors to the network.</p>
          </div>
        </div>
      </div>

      <div className="glass-card rounded-[2.5rem] border border-border overflow-hidden bg-card/50 backdrop-blur-xl p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* Donor Type Selection */}
          <div className="flex gap-4 p-1 bg-muted rounded-2xl">
            <button
              type="button"
              onClick={() => setDonorType("blood")}
              className={`flex-1 py-3 rounded-xl font-bold text-sm uppercase tracking-widest transition-all ${donorType === "blood" ? "bg-primary text-white shadow-lg" : "text-muted-foreground hover:bg-background"}`}
            >
              🩸 Blood
            </button>
            <button
              type="button"
              onClick={() => setDonorType("organ")}
              className={`flex-1 py-3 rounded-xl font-bold text-sm uppercase tracking-widest transition-all ${donorType === "organ" ? "bg-primary text-white shadow-lg" : "text-muted-foreground hover:bg-background"}`}
            >
              🫀 Organ
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <User className="w-3 h-3" /> Donor/Reference Name
              </label>
              <input
                required
                type="text"
                placeholder="e.g. John Doe or Blood Bag #123"
                value={formData.full_name}
                onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                className="w-full px-5 py-4 bg-background border border-border rounded-2xl text-sm font-medium focus:ring-2 focus:ring-primary outline-none transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <Activity className="w-3 h-3" /> Age
              </label>
              <input
                required
                type="number"
                placeholder="Age in years"
                value={formData.age}
                onChange={(e) => setFormData({...formData, age: e.target.value})}
                className="w-full px-5 py-4 bg-background border border-border rounded-2xl text-sm font-medium focus:ring-2 focus:ring-primary outline-none transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <Droplet className="w-3 h-3" /> Blood Type
              </label>
              <select
                value={formData.blood_type}
                onChange={(e) => setFormData({...formData, blood_type: e.target.value})}
                className="w-full px-5 py-4 bg-background border border-border rounded-2xl text-sm font-medium focus:ring-2 focus:ring-primary outline-none transition-all"
              >
                {["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map(bt => (
                  <option key={bt} value={bt}>{bt}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <MapPin className="w-3 h-3" /> City
              </label>
              <input
                required
                type="text"
                placeholder="e.g. Lahore"
                value={formData.city}
                onChange={(e) => setFormData({...formData, city: e.target.value})}
                className="w-full px-5 py-4 bg-background border border-border rounded-2xl text-sm font-medium focus:ring-2 focus:ring-primary outline-none transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center justify-between">
                <span className="flex items-center gap-2"><MapPin className="w-3 h-3" /> Latitude</span>
                <button 
                  type="button" 
                  onClick={getLocation}
                  className="text-[10px] bg-primary/10 text-primary px-2 py-1 rounded-lg hover:bg-primary hover:text-white transition-all flex items-center gap-1"
                >
                  <Zap className="w-3 h-3" /> Auto-Detect GPS
                </button>
              </label>
              <input
                required
                type="number"
                step="any"
                placeholder="e.g. 31.5204"
                value={formData.latitude}
                onChange={(e) => setFormData({...formData, latitude: e.target.value})}
                className="w-full px-5 py-4 bg-background border border-border rounded-2xl text-sm font-medium focus:ring-2 focus:ring-primary outline-none transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <MapPin className="w-3 h-3" /> Longitude
              </label>
              <input
                required
                type="number"
                step="any"
                placeholder="e.g. 74.3587"
                value={formData.longitude}
                onChange={(e) => setFormData({...formData, longitude: e.target.value})}
                className="w-full px-5 py-4 bg-background border border-border rounded-2xl text-sm font-medium focus:ring-2 focus:ring-primary outline-none transition-all"
              />
            </div>
          </div>

          {/* Organ Selection (Only visible if type is organ) */}
          {donorType === "organ" && (
            <div className="space-y-4 pt-4 border-t border-border">
              <label className="text-xs font-black uppercase tracking-widest text-foreground flex items-center gap-2">
                Available Organs
              </label>
              <div className="flex flex-wrap gap-3">
                {availableOrgansList.map(organ => (
                  <button
                    key={organ}
                    type="button"
                    onClick={() => handleOrganToggle(organ)}
                    className={`px-4 py-2 rounded-xl text-sm font-bold border transition-all ${
                      formData.organs_available.includes(organ)
                        ? "bg-primary text-white border-primary"
                        : "bg-background border-border text-muted-foreground hover:border-primary/50"
                    }`}
                  >
                    {organ}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="pt-6">
            <button
              type="submit"
              disabled={loading || (donorType === "organ" && formData.organs_available.length === 0)}
              className="w-full flex items-center justify-center gap-2 py-4 bg-primary text-white rounded-2xl font-black uppercase tracking-widest hover:bg-primary/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Uploading..." : <><PlusCircle className="w-5 h-5" /> Upload to Network</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
