-- ============================================================
-- OPAL-AI DATABASE MIGRATION SCRIPT (v2 — Schema-Verified)
-- Run this entire script in your Supabase SQL Editor
-- ============================================================

-- 1. ADD MISSING COLUMNS to match_results
--    (existing cols: id, donor_id, recipient_id, match_score,
--     compatibility, distance_km, status, urgency, blood_type,
--     organ_type, donor_name, hospital_name, created_at)
ALTER TABLE public.match_results
  ADD COLUMN IF NOT EXISTS model_used    TEXT DEFAULT 'XGBRanker-v2',
  ADD COLUMN IF NOT EXISTS ai_explanation TEXT,
  ADD COLUMN IF NOT EXISTS score_breakdown JSONB,
  ADD COLUMN IF NOT EXISTS match_type    TEXT DEFAULT 'organ';

-- 2. CREATE data_access_logs TABLE (Privacy Audit Trail)
--    Uses TEXT for IDs to avoid FK issues with UUID casting
CREATE TABLE IF NOT EXISTS public.data_access_logs (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  hospital_id  TEXT,
  donor_id     TEXT,
  action_type  TEXT NOT NULL DEFAULT 'reveal_contact',
  accessed_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.data_access_logs ENABLE ROW LEVEL SECURITY;

-- Policy: allow authenticated users to insert their own logs
CREATE POLICY "Allow hospital to log access"
  ON public.data_access_logs
  FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

-- Policy: hospital can read its own logs
CREATE POLICY "Allow hospital to read its logs"
  ON public.data_access_logs
  FOR SELECT
  USING (auth.role() = 'authenticated');

-- 3. ENSURE match_results has status column
ALTER TABLE public.match_results
  ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'potential';

-- 4. PERFORMANCE INDEXES
CREATE INDEX IF NOT EXISTS idx_match_results_donor   ON public.match_results(donor_id);
CREATE INDEX IF NOT EXISTS idx_match_results_status  ON public.match_results(status);
CREATE INDEX IF NOT EXISTS idx_access_logs_hospital  ON public.data_access_logs(hospital_id);
CREATE INDEX IF NOT EXISTS idx_donors_available      ON public.donors(is_available, approval_status);

-- 5. VERIFY — this will show all columns after migration
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('match_results', 'data_access_logs')
ORDER BY table_name, ordinal_position;
