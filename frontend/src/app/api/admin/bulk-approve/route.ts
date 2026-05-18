import { getServiceSupabase } from "@/lib/supabase";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const adminClient = getServiceSupabase();

  try {
    // 1. Approve all pending donors in unified table
    const { error: donorError } = await adminClient
      .from("donors")
      .update({ 
        approval_status: 'verified',
        status: 'active' 
      })
      .eq("approval_status", "pending");

    if (donorError) throw donorError;

    // 2. Approve all pending hospitals
    const { error: hospError } = await adminClient
      .from("hospitals")
      .update({ 
        is_verified: true,
        approval_status: 'verified',
        is_active: true
      })
      .eq("approval_status", "pending");

    if (hospError) throw hospError;

    // 3. Sync legacy tables
    await adminClient.from("blood_donors").update({ approval_status: 'verified', status: 'active' }).eq("approval_status", "pending");
    await adminClient.from("organ_donors").update({ approval_status: 'verified', status: 'active' }).eq("approval_status", "pending");

    return NextResponse.json({ 
      success: true, 
      message: "Neural Synchronization Complete: All accounts verified." 
    });

  } catch (error: any) {
    console.error("Bulk Approve Error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
