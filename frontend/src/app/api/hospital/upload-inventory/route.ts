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

    const body = await request.json();
    
    // Split name for schema compatibility
    const nameParts = body.full_name.split(" ");
    const firstName = nameParts[0];
    const lastName = nameParts.slice(1).join(" ") || "Registry";

    const payload = {
      ...body,
      first_name: firstName,
      last_name: lastName,
      user_id: user.id, // Track which hospital added this record
      status: 'active',
      approval_status: 'verified',
      is_available: true,
      is_blood_donor: body.donor_type === 'blood',
      is_organ_donor: body.donor_type === 'organ'
    };

    const { data, error } = await adminClient
      .from("donors")
      .insert([payload])
      .select()
      .single();

    if (error) throw error;

    return NextResponse.json({ success: true, donor: data });
  } catch (error: any) {
    console.error("INVENTORY_UPLOAD_FAILURE:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
