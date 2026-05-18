import { NextRequest, NextResponse } from "next/server";
import { getServiceSupabase } from "@/lib/supabase";
import { donorFormSchema } from "@/lib/schemas/donor";
import { sendDonorWelcomeEmail } from "@/lib/mailer";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // 1. Validation
    const result = donorFormSchema.safeParse(body);
    if (!result.success) {
      return NextResponse.json({ 
        success: false, 
        error: "Validation failed", 
        details: result.error.flatten().fieldErrors 
      }, { status: 400 });
    }

    const data = result.data;
    const adminSupabase = getServiceSupabase();
    
    // 2. Security Check: Duplicate Email
    const { data: existingUsersData } = await adminSupabase.auth.admin.listUsers();
    if (existingUsersData?.users.some(u => u.email === data.email)) {
      return NextResponse.json({ success: false, error: "An account already exists with this email address." }, { status: 409 });
    }

    // 2.5 Security Check: Duplicate CNIC
    const { data: existingCnic } = await adminSupabase
      .from('donors')
      .select('cnic')
      .eq('cnic', data.cnic)
      .limit(1);

    if (existingCnic && existingCnic.length > 0) {
      return NextResponse.json({ 
        success: false, 
        error: "This CNIC is already registered. Please login or use a different CNIC." 
      }, { status: 409 });
    }

    // 3. Create Auth User
    const { data: authData, error: authError } = await adminSupabase.auth.admin.createUser({
      email: data.email,
      password: data.password,
      email_confirm: true,
      user_metadata: {
        first_name: data.firstName,
        last_name: data.lastName,
        role: 'donor'
      }
    });

    let userId = authData?.user?.id;

    if (authError) {
      if (authError.message.toLowerCase().includes("already exists")) {
        console.log("RECOVERY MODE: User exists, attempting ID resolution...");
        
        // Strategy A: Check profiles table first (often has the ID)
        const { data: profile } = await adminSupabase
          .from('profiles')
          .select('id')
          .ilike('full_name', `${data.firstName} ${data.lastName}`)
          .limit(1);
        
        if (profile && profile.length > 0) {
          userId = profile[0].id;
        } else {
          // Strategy B: List users (with high limit)
          const { data: userList } = await adminSupabase.auth.admin.listUsers({
            perPage: 1000
          });
          const existing = userList?.users?.find(u => u.email?.toLowerCase() === data.email.toLowerCase());
          if (existing) {
            userId = existing.id;
          }
        }
        
        if (userId) {
          // Reset password and confirm email for the existing user
          await adminSupabase.auth.admin.updateUserById(userId, {
            password: data.password,
            email_confirm: true
          });
          console.log("RECOVERY SUCCESS: Resolved ID and reset password for:", data.email);
        } else {
          console.error("RECOVERY FAILED: Could not resolve ID for existing email:", data.email);
          return NextResponse.json({ 
            success: false, 
            error: "This email is already registered, but your clinical profile is missing. Please contact the administrator to reset your account.",
            details: "AUTH_EXISTS_PROFILE_MISSING"
          }, { status: 409 });
        }
      } else {
        throw authError;
      }
    }

    if (!userId) throw new Error("Authentication storage failed.");

    // 4. Create/Fix Profile (Always use upsert)
    const { error: profileError } = await adminSupabase.from('profiles').upsert([{
      id: userId,
      role: 'donor',
      full_name: `${data.firstName} ${data.lastName}`
    }]);

    if (profileError) throw profileError;

    // 5. Parallelized Data Entry (Unified Clinical Registry)
    const fullName = `${data.firstName} ${data.lastName}`;
    const syncPromises = [];

    // Central Registry Sync (Use upsert to handle retries)
    syncPromises.push(adminSupabase.from('donors').upsert([{
        id: userId,
        user_id: userId,
        first_name: data.firstName,
        last_name: data.lastName,
        full_name: fullName,
        contact_number: data.contactNumber,
        age: data.age,
        gender: data.gender,
        blood_type: data.bloodType,
        cnic: data.cnic,
        donor_type: data.donationType === "Both" ? "both" : (data.donationType === "Organ Donation Only" ? "organ" : "blood"),
        city: data.city,
        latitude: data.latitude,
        longitude: data.longitude,
        is_available: true,
        is_blood_donor: data.donationType === "Blood Donation Only" || data.donationType === "Both",
        is_organ_donor: data.donationType === "Organ Donation Only" || data.donationType === "Both",
        donating_items: data.donatingItems || ["Whole Blood"],
        status: 'active',
        approval_status: 'pending',
        organs_available: data.organsWilling || [],
        diabetes: data.diabetes === "Yes",
        smoker: data.smoker === "Yes",
        condition_heart_disease: data.medicalConditions?.toLowerCase().includes('heart') || false,
        condition_hypertension: data.medicalConditions?.toLowerCase().includes('bp') || data.medicalConditions?.toLowerCase().includes('tension') || false
    }]));

    // Optional: Sync to donor_profiles for auxiliary medical flags
    syncPromises.push(adminSupabase.from('donor_profiles').upsert([{
      user_id: userId,
      full_name: fullName,
      city: data.city,
      blood_type: data.bloodType,
      donor_types: [data.donationType],
      is_available: true,
      is_verified_medical: false
    }]));

    // Wait for all syncs to complete in parallel
    const syncResults = await Promise.all(syncPromises);
    const firstError = syncResults.find(r => r.error)?.error;
    if (firstError) {
        console.error("CRITICAL: Clinical Registry Sync Failed:", firstError);
        throw firstError;
    }

    // 7. Communication logic
    try {
      await sendDonorWelcomeEmail(data.email, fullName, data.bloodType);
    } catch (e) {
      console.error("Delayed Notification Warning: Welcome email could not be sent.", e);
    }

    return NextResponse.json({ 
      success: true, 
      message: "Donor account established. Your application is now in the verification queue.",
      redirect: "/auth/pending-approval"
    }, { status: 201 });

  } catch (error: any) {
    console.error("CRITICAL REGISTRATION FAILURE:", error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
