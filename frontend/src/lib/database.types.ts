// ============================================================
// Supabase Database Types for TypeScript
// Tells the Supabase client about our tables and RPC functions
// ============================================================

export type Database = {
  public: {
    Tables: {
      donors: {
        Row: {
          id: string;
          user_id: string | null;
          full_name: string;
          email: string | null;
          phone: string | null;
          age: number | null;
          gender: string | null;
          blood_type: string;
          cnic: string | null;
          donor_type: string | null;
          hypertension: boolean | null;
          heart_disease: boolean | null;
          diabetic_status: boolean | null;
          hepatitis_status: string | null;
          hiv_status: string | null;
          organs_available: any | null;
          is_living_donor: boolean | null;
          medical_report_url: string | null;
          city: string;
          latitude: number | null;
          longitude: number | null;
          is_available: boolean;
          status: string | null;
          approval_status: string | null;
          last_verified_by: string | null;
          created_at: string | null;
          updated_at: string | null;
          suspension_reason: string | null;
        };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
      };
      notifications: {
        Row: {
          id: string;
          user_id: string;
          title: string;
          message: string;
          type: string;
          is_read: boolean;
          created_at: string;
        };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
      };
      blood_donors: {
        Row: {
          id: string;
          user_id: string;
          full_name: string;
          email: string | null;
          phone: string | null;
          age: number | null;
          gender: string | null;
          blood_type: string;
          cnic: string | null;
          city: string;
          latitude: number | null;
          longitude: number | null;
          is_available: boolean;
          status: string | null;
          approval_status: string | null;
          created_at: string | null;
        };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
      };
      organ_donors: {
        Row: {
          id: string;
          user_id: string;
          full_name: string;
          email: string | null;
          phone: string | null;
          age: number | null;
          gender: string | null;
          blood_type: string;
          cnic: string | null;
          organs_available: any;
          hiv_status: string | null;
          hepatitis_status: string | null;
          diabetes: boolean | null;
          smoker: boolean | null;
          heart_disease: boolean | null;
          hypertension: boolean | null;
          is_living_donor: boolean | null;
          city: string;
          latitude: number | null;
          longitude: number | null;
          is_available: boolean;
          status: string | null;
          approval_status: string | null;
          created_at: string | null;
        };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
      };
      recipients: {
        Row: {
          id: string;
          hospital_id: string;
          patient_name: string | null;
          patient_blood_type: string;
          required_organs: any | null;
          urgency_level: string;
          status: string | null;
          created_at: string | null;
        };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
      };
      hospitals: {
        Row: {
          id: string;
          user_id: string | null;
          name: string;
          license_number: string | null;
          city: string;
          full_address: string | null;
          phone: string | null;
          contact_email: string | null;
          latitude: number | null;
          longitude: number | null;
          is_verified: boolean;
          approval_status: string | null;
          is_active: boolean | null;
          created_at: string | null;
        };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
      };
      match_results: {
        Row: {
          id: string;
          donor_id: string;
          recipient_id: string | null;
          match_score: number;
          compatibility: string | null;
          distance_km: number | null;
          status: string | null;
          urgency: string | null;
          blood_type: string | null;
          organ_type: string | null;
          donor_name: string | null;
          hospital_name: string | null;
          created_at: string | null;
        };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
      };
      organ_requests: {
        Row: {
          id: string;
          hospital_id: string;
          patient_blood_type: string;
          required_organs: any;
          status: string | null;
          urgency_level: string | null;
          created_at: string | null;
        };
        Insert: Record<string, unknown>;
        Update: Record<string, unknown>;
      };

    };
    Views: Record<string, never>;
    Functions: {
      find_blood_donors: {
        Args: {
          req_blood_type: string;
          req_city: string;
          req_urgency: string;
        };
        Returns: {
          donor_id: number;
          first_name: string;
          last_name: string;
          blood_type: string;
          city: string;
          hospital_name: string | null;
          match_score: number;
          compatibility: string;
          distance_km: number;
          status: string | null;
          blood_products_donating: string | null;
        }[];
      };
      find_organ_donors: {
        Args: {
          req_organ: string;
          req_city: string;
          req_urgency: string;
        };
        Returns: {
          donor_id: number;
          first_name: string;
          last_name: string;
          blood_type: string;
          city: string;
          hospital_name: string | null;
          match_score: number;
          compatibility: string;
          distance_km: number;
          status: string | null;
          organs_donating: string | null;
        }[];
      };
    };
    Enums: Record<string, never>;
  };
};
