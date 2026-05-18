-- ============================================================
-- NOTIFICATIONS RLS POLICY FIX
-- ============================================================

-- 1. Enable RLS on notifications table
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- 2. Drop existing policies to avoid conflicts
DROP POLICY IF EXISTS "Users can view their own notifications" ON public.notifications;
DROP POLICY IF EXISTS "System can insert notifications" ON public.notifications;

-- 3. Policy: Allow users to view ONLY their own notifications
CREATE POLICY "Users can view their own notifications"
  ON public.notifications
  FOR SELECT
  USING (auth.uid() = user_id);

-- 4. Policy: Allow the system (service role or authenticated hospitals) to insert notifications
--    Note: Since we use service_role in the API route, it bypasses RLS anyway, 
--    but adding an authenticated insert policy is good practice.
CREATE POLICY "Allow authenticated to insert notifications"
  ON public.notifications
  FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');
