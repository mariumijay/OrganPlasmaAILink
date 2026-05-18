import { createClient, getServiceSupabase } from "@/lib/supabase";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const supabase = await createClient();
    const adminClient = getServiceSupabase();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const updates = await req.json();

    // Standardize update to the unified 'donors' table using admin client to bypass RLS
    const { data, error } = await adminClient
      .from("donors")
      .update({
        ...updates,
        // Security: Ensure users can't verify themselves
        approval_status: 'pending' // Re-verification required if medical data changes
      })
      .eq("user_id", user.id)
      .select();

    if (error) throw error;

    return NextResponse.json({ success: true, data });
  } catch (err: any) {
    console.error("Profile Update Error:", err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
