import { NextRequest, NextResponse } from "next/server";
import { getServiceSupabase } from "@/lib/supabase";

export async function POST(request: NextRequest) {
  try {
    const { cnic } = await request.json();
    if (!cnic) return NextResponse.json({ error: "CNIC is required" }, { status: 400 });

    const adminSupabase = getServiceSupabase();
    
    // Check both donors and possibly hospitals (if they use CNIC for admins)
    const { data: existingDonor } = await adminSupabase
      .from('donors')
      .select('cnic')
      .eq('cnic', cnic)
      .maybeSingle();

    return NextResponse.json({ exists: !!existingDonor });
  } catch (error: any) {
    console.error("CNIC Check Error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
