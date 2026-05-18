import { createClient } from '@supabase/supabase-js'
import * as dotenv from 'dotenv'
dotenv.config({ path: '.env.local' })

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing env vars')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseServiceKey)

async function debugDonor(email: string) {
  console.log(`Checking donor for email: ${email}`)
  
  const { data: userData, error: userError } = await supabase.auth.admin.listUsers()
  const user = userData?.users.find(u => u.email === email)
  
  if (!user) {
    console.error('User not found in Auth')
    return
  }
  
  console.log(`User found: ${user.id}`)
  console.log('User Metadata:', user.user_metadata)
  
  const { data: profile } = await supabase.from('profiles').select('*').eq('id', user.id).single()
  console.log('Profile:', profile)
  
  const { data: donor } = await supabase.from('donors').select('*').eq('user_id', user.id).single()
  console.log('Donor Record:', donor)
  
  const { data: donorById } = await supabase.from('donors').select('*').eq('id', user.id).single()
  console.log('Donor Record (by id):', donorById)
}

const email = process.argv[2]
if (email) {
  debugDonor(email)
} else {
  console.log('Usage: node debug_donor.js <email>')
}
