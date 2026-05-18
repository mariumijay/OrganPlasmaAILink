"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { donorFormSchema, type DonorFormValues } from "@/lib/schemas/donor";
import { toast } from "sonner";
import {
  Heart, Mail, Lock, User, Phone, MapPin, Activity, ShieldAlert, CheckCircle, Droplet, ArrowRight, ArrowLeft, Loader2, Zap
} from "lucide-react";
import { PasswordInput } from "@/components/shared/PasswordInput";

function DonorSignupContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionSuccess, setSubmissionSuccess] = useState(false);
  const [isValidatingEmail, setIsValidatingEmail] = useState(false);
  const [isValidatingCnic, setIsValidatingCnic] = useState(false);

  const { register, handleSubmit, trigger, formState: { errors }, watch, setValue, reset } = useForm<DonorFormValues>({
    resolver: zodResolver(donorFormSchema) as any,
    defaultValues: {
      donationType: "Blood Donation Only",
      donatingItems: [],
      organsWilling: [],
      medicalConditions: "",
      contactNumber: "+92 ",
      consent: false
    }
  });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem("donor-draft");
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          reset(parsed);
        } catch (e) {}
      }
    }
  }, [reset]);

  useEffect(() => {
    const subscription = watch((value) => {
      if (typeof window !== 'undefined') {
        localStorage.setItem("donor-draft", JSON.stringify(value));
      }
    });
    return () => subscription.unsubscribe();
  }, [watch]);

  const watchDonationType = watch("donationType");
  const isOrganDonor = watchDonationType === "Organ Donation Only" || watchDonationType === "Both";
  const watchOrgansWilling = watch("organsWilling") || [];
  const watchDonatingItems = watch("donatingItems") || [];

  const handleOrganToggle = (organ: string) => {
    const current = watchOrgansWilling;
    if (current.includes(organ)) setValue("organsWilling", current.filter(i => i !== organ), { shouldValidate: true });
    else setValue("organsWilling", [...current, organ], { shouldValidate: true });
  };

  const handleLocationDetect = () => {
    if ("geolocation" in navigator) {
      const toastId = toast.loading("Detecting Precise GPS Location...");
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const { latitude, longitude } = pos.coords;
          setValue("latitude", latitude, { shouldValidate: true });
          setValue("longitude", longitude, { shouldValidate: true });
          try {
            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1`);
            const data = await res.json();
            const addr = data.address || {};
            let city = addr.neighbourhood || addr.suburb || addr.residential || addr.road || addr.village || addr.town || addr.city || addr.hamlet || addr.city_district;
            if (!city || city === addr.state) {
              if (data.display_name) city = data.display_name.split(',')[0];
            }
            if (!city) city = "Location Detected";
            setValue("city", city, { shouldValidate: true });
            toast.success(`Location Synced: ${city}`, { id: toastId, description: `Lat: ${latitude.toFixed(4)}, Lng: ${longitude.toFixed(4)}` });
          } catch (e) {
            toast.success("Coordinates captured!", { id: toastId });
          }
        },
        (err) => toast.error("GPS access failed: " + err.message, { id: toastId }),
        { enableHighAccuracy: true, timeout: 15000 }
      );
    } else {
      toast.error("Geolocation is not supported by your browser.");
    }
  };

  const processNextStep = async () => {
    let fieldsToValidate: (keyof DonorFormValues)[] = [];
    if (step === 1) fieldsToValidate = ["donationType", "email", "password", "donatingItems"];
    if (step === 2) fieldsToValidate = ["firstName", "lastName", "age", "gender", "city", "contactNumber", "cnic"];
    if (step === 3) {
      if (isOrganDonor) fieldsToValidate = ["bloodType", "hepStatus", "hivStatus", "diabetes", "smoker", "height", "weight", "donorStatus", "organsWilling"];
      else fieldsToValidate = ["bloodType", "hepStatus"];
    }
    
    const isStepValid = await trigger(fieldsToValidate as any);
    
    if (isStepValid && step === 1) {
      setIsValidatingEmail(true);
      try {
        const res = await fetch("/api/auth/check-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: watch("email") })
        });
        const { exists } = await res.json();
        if (exists) {
          toast.error("Email already registered. Please login.");
          return;
        }
      } catch (e) {} finally { setIsValidatingEmail(false); }
    }

    if (isStepValid && step === 2) {
      setIsValidatingCnic(true);
      try {
        const res = await fetch("/api/auth/check-cnic", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cnic: watch("cnic") })
        });
        const { exists } = await res.json();
        if (exists) {
          toast.error("This CNIC is already registered.");
          return;
        }
      } catch (e) {} finally { setIsValidatingCnic(false); }
    }

    if (isStepValid) setStep(prev => prev + 1);
  };

  const onSubmit = async (data: DonorFormValues) => {
    setIsSubmitting(true);
    try {
      const res = await fetch("/api/auth/register-donor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error || "Failed");
      localStorage.removeItem("donor-draft");
      setSubmissionSuccess(true);
      setTimeout(() => router.push("/auth/login?registered=true"), 2000);
    } catch (e: any) {
      toast.error(e.message);
    } finally { setIsSubmitting(false); }
  };

  if (submissionSuccess) {
    return (
      <div className="h-screen flex flex-col items-center justify-center space-y-4">
        <CheckCircle className="h-16 w-16 text-primary" />
        <h1 className="text-2xl font-bold">Registration Successful!</h1>
        <p className="text-muted-foreground">Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <div className="flex-1 flex flex-col items-center justify-center p-4">
        <div className="w-full max-w-xl space-y-8">
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-black tracking-tight">Become a Donor</h1>
            <p className="text-muted-foreground font-medium">Step {step} of 4</p>
          </div>

          <form 
            onSubmit={handleSubmit(onSubmit, (errors) => {
              console.log("Validation Errors:", errors);
              toast.error("Form incomplete. Please check all steps for errors.");
            })} 
            className="bg-card border border-border p-8 rounded-[2rem] shadow-sm space-y-6"
          >
            {/* ... rest of the form ... */}
            <AnimatePresence mode="wait">
              {step === 1 && (
                <motion.div key="1" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
                  <div className="grid grid-cols-1 gap-2">
                    {["Blood Donation Only", "Organ Donation Only", "Both"].map(type => (
                      <label key={type} className={`p-4 rounded-xl border-2 flex items-center gap-3 cursor-pointer transition-all ${watchDonationType === type ? 'border-primary bg-primary/5' : 'border-border'}`}>
                        <input type="radio" {...register("donationType")} value={type} className="hidden" />
                        <div className={`h-4 w-4 rounded-full border-2 ${watchDonationType === type ? 'border-primary border-t-primary bg-primary' : 'border-muted-foreground'}`} />
                        <span className="font-bold text-sm">{type}</span>
                      </label>
                    ))}
                  </div>

                  {(watchDonationType === "Blood Donation Only" || watchDonationType === "Both") && (
                    <div className="space-y-2 pt-2 animate-in fade-in slide-in-from-top-1">
                      <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground ml-1">Select Blood Products</label>
                      <div className="flex flex-wrap gap-2">
                        {["Whole Blood", "Plasma"].map(item => (
                          <button 
                            key={item} 
                            type="button" 
                            onClick={() => {
                              const current = watchDonatingItems;
                              const next = current.includes(item) ? current.filter(i => i !== item) : [...current, item];
                              setValue("donatingItems", next, { shouldValidate: true });
                            }} 
                            className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest border transition-all ${watchDonatingItems.includes(item) ? 'bg-primary text-white border-primary shadow-md' : 'bg-muted/50 border-border text-muted-foreground'}`}
                          >
                            {item}
                          </button>
                        ))}
                      </div>
                      {errors.donatingItems && <p className="text-[10px] text-destructive font-bold">{errors.donatingItems.message}</p>}
                    </div>
                  )}

                  <div className="space-y-2 pt-2 border-t border-border mt-4">
                    <label className="text-sm font-bold">Email</label>
                    <input {...register("email")} type="email" className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20" placeholder="your@email.com" />
                    {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-bold">Password</label>
                    <input 
                      {...register("password")} 
                      type="password" 
                      className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20" 
                      placeholder="••••••••"
                    />
                    {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
                  </div>
                </motion.div>
              )}

              {step === 2 && (
                <motion.div key="2" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-sm font-bold">First Name</label>
                      <input {...register("firstName")} className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20" />
                    </div>
                    <div className="space-y-1">
                      <label className="text-sm font-bold">Last Name</label>
                      <input {...register("lastName")} className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-sm font-bold">Age</label>
                      <input {...register("age", { valueAsNumber: true })} type="number" className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20" />
                    </div>
                    <div className="space-y-1">
                      <label className="text-sm font-bold">Gender</label>
                      <select {...register("gender")} className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 appearance-none">
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-bold">City</label>
                      <button type="button" onClick={handleLocationDetect} className="text-[10px] font-black uppercase text-primary tracking-widest flex items-center gap-1 hover:underline">
                        <Zap className="h-3 w-3" /> Auto Detect GPS
                      </button>
                    </div>
                    <input {...register("city")} className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20" />
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-bold">Contact Number</label>
                    <input {...register("contactNumber")} placeholder="+92 3XX XXXXXXX" className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20" />
                    {errors.contactNumber && <p className="text-xs text-destructive">{errors.contactNumber.message}</p>}
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-bold">CNIC (Verification)</label>
                    <input {...register("cnic")} placeholder="XXXXX-XXXXXXX-X" className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 font-mono" />
                    {errors.cnic && <p className="text-xs text-destructive">{errors.cnic.message}</p>}
                  </div>
                </motion.div>
              )}

              {step === 3 && (
                <motion.div key="3" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-sm font-bold">Blood Type</label>
                      <select {...register("bloodType")} className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 appearance-none">
                        {["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map(bt => <option key={bt} value={bt}>{bt}</option>)}
                      </select>
                    </div>
                    <div className="space-y-1">
                      <label className="text-sm font-bold">Hepatitis Status</label>
                      <select {...register("hepStatus")} className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 appearance-none">
                        <option value="Negative">Negative</option>
                        <option value="Positive">Positive</option>
                      </select>
                    </div>
                  </div>

                  {isOrganDonor && (
                    <div className="space-y-4 pt-4 border-t border-border animate-in fade-in slide-in-from-top-1">
                      <div className="grid grid-cols-3 gap-3">
                        <div className="space-y-1">
                          <label className="text-[10px] font-black uppercase text-muted-foreground ml-1">HIV Status</label>
                          <select {...register("hivStatus")} className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-xs outline-none">
                            <option value="">Select</option>
                            <option value="Negative">Negative</option>
                            <option value="Positive">Positive</option>
                          </select>
                          {errors.hivStatus && <p className="text-[10px] text-destructive">{errors.hivStatus.message}</p>}
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-black uppercase text-muted-foreground ml-1">Diabetes</label>
                          <select {...register("diabetes")} className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-xs outline-none">
                            <option value="">Select</option>
                            <option value="No">No</option>
                            <option value="Yes">Yes</option>
                          </select>
                          {errors.diabetes && <p className="text-[10px] text-destructive">{errors.diabetes.message}</p>}
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-black uppercase text-muted-foreground ml-1">Smoker</label>
                          <select {...register("smoker")} className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-xs outline-none">
                            <option value="">Select</option>
                            <option value="No">No</option>
                            <option value="Yes">Yes</option>
                          </select>
                          {errors.smoker && <p className="text-[10px] text-destructive">{errors.smoker.message}</p>}
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3">
                        <div className="space-y-1">
                          <label className="text-[10px] font-black uppercase text-muted-foreground ml-1">Height (cm)</label>
                          <input type="number" {...register("height", { valueAsNumber: true })} className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-xs outline-none" placeholder="170" />
                          {errors.height && <p className="text-[10px] text-destructive">{errors.height.message}</p>}
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-black uppercase text-muted-foreground ml-1">Weight (kg)</label>
                          <input type="number" {...register("weight", { valueAsNumber: true })} className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-xs outline-none" placeholder="70" />
                          {errors.weight && <p className="text-[10px] text-destructive">{errors.weight.message}</p>}
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-black uppercase text-muted-foreground ml-1">Status</label>
                          <select {...register("donorStatus")} className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-xs outline-none">
                            <option value="">Select</option>
                            <option value="Living">Living</option>
                            <option value="Posthumous">Posthumous</option>
                          </select>
                          {errors.donorStatus && <p className="text-[10px] text-destructive">{errors.donorStatus.message}</p>}
                        </div>
                      </div>

                      <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Organs for Donation</label>
                        <div className="flex flex-wrap gap-2">
                          {["Kidney", "Liver", "Heart", "Lung", "Pancreas", "Cornea"].map(organ => (
                            <button key={organ} type="button" onClick={() => handleOrganToggle(organ)} className={`px-4 py-2 rounded-lg text-xs font-bold border transition-all ${watchOrgansWilling.includes(organ) ? 'bg-primary text-white border-primary' : 'bg-muted/50 border-border'}`}>
                              {organ}
                            </button>
                          ))}
                        </div>
                        {errors.organsWilling && <p className="text-[10px] text-destructive font-bold">{errors.organsWilling.message}</p>}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {step === 4 && (
                <motion.div key="4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
                   <div className="text-center space-y-2">
                     <ShieldAlert className="h-10 w-10 text-primary mx-auto mb-2" />
                     <h3 className="text-xl font-black">{isOrganDonor ? "Legal & Emergency Contact" : "Final Confirmation"}</h3>
                     <p className="text-xs text-muted-foreground leading-relaxed">
                       {isOrganDonor ? "Required for clinical matching protocols." : "Please review and confirm your registration."}
                     </p>
                   </div>

                   {isOrganDonor && (
                     <div className="grid grid-cols-1 gap-4 animate-in fade-in slide-in-from-top-1">
                       <div className="space-y-1">
                         <label className="text-[10px] font-black uppercase text-muted-foreground tracking-widest ml-1">Next of Kin Name</label>
                         <input {...register("nextOfKinName")} placeholder="Emergency Contact Name" className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20" />
                         {errors.nextOfKinName && <p className="text-[10px] text-destructive font-bold">{errors.nextOfKinName.message}</p>}
                       </div>
                       <div className="space-y-1">
                         <label className="text-[10px] font-black uppercase text-muted-foreground tracking-widest ml-1">Next of Kin Contact</label>
                         <input {...register("nextOfKinContact")} placeholder="+92 3XX XXXXXXX" className="w-full bg-muted/50 border border-border rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20" />
                         {errors.nextOfKinContact && <p className="text-[10px] text-destructive font-bold">{errors.nextOfKinContact.message}</p>}
                       </div>
                     </div>
                   )}
                   
                   <label className="flex items-start gap-3 p-4 rounded-2xl border border-border bg-muted/30 cursor-pointer hover:bg-muted/50 transition-all">
                     <input 
                       type="checkbox" 
                       {...register("consent")} 
                       className="h-5 w-5 rounded-md accent-primary mt-0.5"
                     />
                     <span className="text-xs font-bold text-left text-foreground">I confirm that all provided information is accurate and I consent to the OPAL-AI clinical matching protocol.</span>
                   </label>
                   {errors.consent && <p className="text-xs text-destructive font-bold">{errors.consent.message}</p>}
                </motion.div>
              )}
            </AnimatePresence>

            <div className="flex gap-3 pt-4">
              {step > 1 && (
                <button type="button" onClick={() => setStep(step - 1)} className="px-6 py-3 rounded-xl border border-border font-bold text-sm hover:bg-muted transition-all">
                  Back
                </button>
              )}
              {step < 4 ? (
                <button type="button" disabled={isValidatingEmail || isValidatingCnic} onClick={processNextStep} className="flex-1 py-3 rounded-xl bg-primary text-white font-black uppercase tracking-widest text-sm hover:opacity-90 transition-all flex items-center justify-center gap-2">
                  {isValidatingEmail || isValidatingCnic ? <Loader2 className="h-4 w-4 animate-spin" /> : "Continue"}
                  <ArrowRight className="h-4 w-4" />
                </button>
              ) : (
                <button type="submit" disabled={isSubmitting} className="flex-1 py-3 rounded-xl bg-primary text-white font-black uppercase tracking-widest text-sm hover:opacity-90 transition-all flex items-center justify-center gap-2">
                  {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Complete Registration"}
                </button>
              )}
            </div>
          </form>
          
          <p className="text-center text-sm text-muted-foreground">
            Already have an account? <Link href="/auth/login" className="text-primary font-bold hover:underline">Sign In</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function DonorSignupPage() {
  return (
    <Suspense fallback={<div className="h-screen w-screen flex items-center justify-center"><Loader2 className="h-10 w-10 animate-spin text-primary" /></div>}>
      <DonorSignupContent />
    </Suspense>
  );
}
