const { createClient } = require('@supabase/supabase-js')

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY

const supabase = createClient(supabaseUrl, supabaseServiceKey)

async function checkRLS() {
  const { data, error } = await supabase.rpc('get_policies', { table_name: 'donors' })
  if (error) {
    // If RPC doesn't exist, try manual query to pg_policies
    const { data: policies, error: polError } = await supabase.from('pg_policies').select('*').eq('tablename', 'donors')
    console.log('POLICIES:', policies || polError)
  } else {
    console.log('POLICIES (RPC):', data)
  }
}

checkRLS()
