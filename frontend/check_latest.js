import { createClient } from '@supabase/supabase-js'
import * as dotenv from 'dotenv'
dotenv.config({ path: '.env.local' })

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY

const supabase = createClient(supabaseUrl, supabaseServiceKey)

async function checkLatest() {
  const { data: userData } = await supabase.auth.admin.listUsers()
  const users = userData?.users || []
  users.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  
  const latest = users[0]
  if (!latest) return
  
  console.log('LATEST USER:', latest.email, latest.id)
  
  const { data: donor } = await supabase.from('donors').select('*').eq('user_id', latest.id).maybeSingle()
  console.log('Donor Record:', donor)
}

checkLatest()
