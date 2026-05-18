import { getServiceSupabase } from "@/lib/supabase";
import { NextResponse } from "next/server";
import { sendEmail } from "@/lib/mailer";

export async function POST(request: Request) {
  const adminClient = getServiceSupabase();

  try {
    const { donor_id, hospital_id, category, organ_type, blood_type, match_score, ai_explanation, score_breakdown, distance_info, urgency } = await request.json();

    if (!donor_id) {
      return NextResponse.json({ error: "Donor ID is required" }, { status: 400 });
    }

    // 1. Fetch Donor Details 
    const { data: donor, error: donorErr } = await adminClient
      .from("donors")
      .select("full_name, user_id, city")
      .eq("id", donor_id)
      .maybeSingle();

    if (donorErr || !donor) throw new Error("Donor node not found.");

    // 2. Fetch Hospital Details
    let hospitalName = "OPAL-AI Verified Facility";
    if (hospital_id) {
        const { data: hosp } = await adminClient
            .from("hospitals")
            .select("name")
            .or(`user_id.eq.${hospital_id},id.eq.${hospital_id}`)
            .maybeSingle();
        if (hosp) hospitalName = hosp.name;
    }

    // 3. Get Donor Email
    let donorEmail = null;
    if (donor.user_id) {
      const { data: authUser } = await adminClient.auth.admin.getUserById(donor.user_id);
      donorEmail = authUser?.user?.email;
    }

    // 4. Send Emergency Email & Create In-App Notification
    if (donorEmail) {
      const donorName = donor.full_name || "Valued Donor";
      const subject = `🚨 URGENT: Life-Saving Request from ${hospitalName}`;
      
      await sendEmail({
        to: donorEmail,
        subject: subject,
        html: `
          <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 40px; background-color: #050505; color: #ffffff; border-radius: 24px; border: 1px solid #22c55e;">
            <div style="text-align: center; margin-bottom: 30px;">
                <span style="background: rgba(34, 197, 94, 0.1); color: #22c55e; padding: 8px 16px; border-radius: 99px; font-size: 10px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">
                    Critical Matching Alert
                </span>
                <div style="margin-top: 15px;">
                  <span style="background: ${urgency === 'Emergency' || urgency === 'Critical' ? '#ef4444' : '#f59e0b'}; color: #ffffff; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: bold; text-transform: uppercase;">
                      🚨 Threshold: ${urgency || 'Urgent'}
                  </span>
                </div>
            </div>
            
            <h1 style="color: #ffffff; font-size: 28px; font-weight: 900; text-align: center; margin-bottom: 20px;">
                Hello ${donorName}, <br/> WE NEED YOU!
            </h1>
            
            <p style="color: #9ca3af; text-align: center; font-size: 16px; line-height: 1.6;">
                A high-priority clinical match has been verified. <strong>${hospitalName}</strong> has requested your help for an urgent <strong>${organ_type}</strong> donation.
            </p>

            <div style="background: #111; padding: 30px; border-radius: 20px; text-align: center; margin: 30px 0; border: 1px dashed #333;">
              <p style="color: #4b5563; font-size: 12px; margin-bottom: 5px; text-transform: uppercase; font-weight: 900;">Required Product</p>
              <h2 style="font-size: 32px; font-weight: 900; color: #22c55e; margin: 0;">${organ_type}</h2>
              <p style="color: #22c55e; font-size: 14px; margin-top: 10px; font-weight: bold;">Blood Group: ${blood_type}</p>
              <p style="color: #4b5563; font-size: 12px; margin-top: 15px;">Target Location: ${hospitalName}, ${donor.city} (${distance_info || 'Local Area'})</p>
            </div>

            <p style="color: #ffffff; font-weight: bold; text-align: center;">
                Please check your OPAL-AI dashboard immediately or wait for a coordinator to call you.
            </p>

            <div style="text-align: center; margin-top: 40px;">
                <a href="${process.env.NEXT_PUBLIC_SITE_URL}/dashboard/donor" style="background: #22c55e; color: #000000; padding: 16px 32px; border-radius: 12px; text-decoration: none; font-weight: 900; font-size: 14px; text-transform: uppercase;">
                    Confirm Availability
                </a>
            </div>

            <p style="font-size: 11px; color: #4b5563; margin-top: 40px; text-align: center; border-top: 1px solid #1a1a1a; pt: 20px;">
                OPAL-AI Clinical Logistics Engine. This is an automated emergency notification.
            </p>
          </div>
        `
      }).catch(e => console.error("Mail Fail:", e));

      // 5. Create Database Notification for Amina's Portal
      if (donor.user_id) {
        await adminClient.from("notifications").insert({
          user_id: donor.user_id,
          title: `🚨 URGENT: Clinical Match Found`,
          message: `${hospitalName} needs your help for a ${organ_type} donation. Distance: ${distance_info || 'Local'}. Protocol initiated.`,
          type: 'emergency',
          is_read: false
        });
      }
    }

    // 6. --- [STRICT DIAGRAM STEP] --- 
    // Save to match_results Table & Update Donor Availability
    const { data: hospRecord } = await adminClient
      .from("hospitals")
      .select("id")
      .eq("user_id", hospital_id)
      .maybeSingle();

    const finalHospId = hospRecord?.id;

    // 6a. Insert into match_results
    await adminClient.from("match_results").insert({
        donor_id: donor_id,
        hospital_id: finalHospId,
        match_score: match_score || 0.0,
        match_type: category,
        ai_explanation: ai_explanation,
        score_breakdown: score_breakdown,
        status: 'pending',
        model_used: 'XGBRanker-v2'
    });

    // 6b. Toggle Donor Availability
    await adminClient.from("donors").update({
        is_available: false
    }).eq("id", donor_id);

    return NextResponse.json({ 
      success: true, 
      message: "Emergency notification dispatched. Donor status locked."
    });

  } catch (error: any) {
    console.error("Procure API Error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
