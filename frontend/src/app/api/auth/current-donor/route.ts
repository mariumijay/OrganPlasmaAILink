import { createServerSupabase, getServiceSupabase } from "@/lib/supabase";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function GET() {
  const cookieStore = await cookies();
  const supabase = await createServerSupabase(cookieStore);
  const adminClient = getServiceSupabase();

  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      console.log("[AUTH] No active session found in request.");
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    console.log(`[QUERY] Fetching clinical profile for User ID: ${user.id}`);

    const { data: donor, error } = await adminClient
      .from("donors")
      .select("*")
      .eq("user_id", user.id)
      .maybeSingle();

    if (error) throw error;

    if (!donor) {
      console.warn(`[MISSING] No donor record found in DB for user ${user.id}`);
      return NextResponse.json({ 
        donor: null, 
        debug: { 
          userId: user.id, 
          email: user.email,
          metadata: user.user_metadata 
        } 
      });
    }

    return NextResponse.json({ donor });
  } catch (error: any) {
    console.error("GET_CURRENT_DONOR_FAILURE:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
