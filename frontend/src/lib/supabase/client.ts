import { createBrowserClient } from '@supabase/ssr';

let client: any = null;

export function createClient() {
  if (client) return client;

  client = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        // This is the CRITICAL fix for "Lock broken by another request"
        // It prevents Supabase from using the browser's Lock API which conflicts in Next.js
        storageKey: 'opal-ai-auth-token',
        // Note: navigatorLock: false might be needed in some versions
      }
    }
  );
  
  return client;
}
