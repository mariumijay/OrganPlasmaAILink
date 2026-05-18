import { createServerSupabase, getServiceSupabase } from "@/lib/supabase";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const cookieStore = await cookies();
  const supabase = await createServerSupabase(cookieStore);
  const adminClient = getServiceSupabase();

  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

    const { hospital_id } = await request.json();

    if (!hospital_id) {
      return NextResponse.json({ error: "Application ID is required" }, { status: 400 });
    }

    // 1. Try to find in hospitals
    let { data: hospital } = await adminClient
      .from("hospitals")
      .select("id, user_id, contact_email, name")
      .eq("id", hospital_id)
      .single();

    if (hospital) {
      // It's a hospital
      await adminClient.from("hospitals").delete().eq("id", hospital_id);
      if (hospital.user_id) {
        await adminClient.auth.admin.deleteUser(hospital.user_id);
      }
    } else {
      // 2. Try to find in donors
      const { data: donor } = await adminClient
        .from("donors")
        .select("id, user_id, full_name")
        .eq("id", hospital_id)
        .single();
      
      if (donor) {
        await adminClient.from("donors").delete().eq("id", hospital_id);
        if (donor.user_id) {
          await adminClient.auth.admin.deleteUser(donor.user_id);
        }
      } else {
        throw new Error("Application not found in clinical registry.");
      }
    }

    return NextResponse.json({ success: true });
  } catch (error: any) {
    console.error("REJECTION_FAILURE:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
