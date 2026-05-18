-- ============================================================
-- DONORS UPDATE POLICY FIX
-- ============================================================

-- 1. Enable RLS on donors table (if not already enabled)
ALTER TABLE public.donors ENABLE ROW LEVEL SECURITY;

-- 2. Policy: Allow users to update ONLY their own donor record
DROP POLICY IF EXISTS "Users can update their own donor record" ON public.donors;

CREATE POLICY "Users can update their own donor record"
  ON public.donors
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- 3. Policy: Allow users to view their own donor record (standard)
DROP POLICY IF EXISTS "Users can view their own donor record" ON public.donors;

CREATE POLICY "Users can view their own donor record"
  ON public.donors
  FOR SELECT
  USING (auth.uid() = user_id);
