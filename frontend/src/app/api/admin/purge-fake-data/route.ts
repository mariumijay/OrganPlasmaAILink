import { NextResponse } from "next/server";
import { getServiceSupabase } from "@/lib/supabase";
import { cookies } from "next/headers";
import { createServerSupabase } from "@/lib/supabase";

export async function POST() {
  const cookieStore = await cookies();
  const supabase = await createServerSupabase(cookieStore);
  const adminClient = getServiceSupabase();

  const { data: { user } } = await supabase.auth.getUser();
  const userEmail = user?.email?.toLowerCase();
  const isAdmin = user?.user_metadata?.role === "admin" || userEmail === "ranahaseeb9427@gmail.com";

  if (!isAdmin) {
    return NextResponse.json({ error: "Access Denied" }, { status: 403 });
  }

  try {
    // Purge pending donors and unverified hospitals
    const [donorRes, hospRes] = await Promise.all([
      adminClient.from("donors").delete().eq("approval_status", "pending"),
      adminClient.from("hospitals").delete().eq("is_verified", false)
    ]);

    if (donorRes.error) throw donorRes.error;
    if (hospRes.error) throw hospRes.error;

    return NextResponse.json({ 
      success: true, 
      message: "Neural Purge Complete: Thousands of phantom records have been removed from the registry." 
    });
  } catch (error: any) {
    console.error("PURGE FAILURE:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
