import { NextRequest, NextResponse } from "next/server";
import { getServiceSupabase } from "@/lib/supabase";

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();
    if (!email) throw new Error("Email is required for purging.");

    const adminSupabase = getServiceSupabase();

    // 1. Get User ID by Email
    const { data: users, error: listError } = await adminSupabase.auth.admin.listUsers();
    if (listError) throw listError;

    const user = users.users.find((u: any) => u.email === email);
    
    if (user) {
      // 2. Delete from Auth
      const { error: deleteError } = await adminSupabase.auth.admin.deleteUser(user.id);
      if (deleteError) throw deleteError;
      console.log(`Successfully purged Auth account for: ${email}`);
    }

    return NextResponse.json({ success: true, message: "Auth credentials purged successfully." });
  } catch (error: any) {
    console.error("PURGE ERROR:", error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
