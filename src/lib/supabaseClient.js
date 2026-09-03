import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// Retrieve environment variables dynamically from environment or fallback safely
const SUPABASE_URL = 
  (typeof process !== 'undefined' && process.env && process.env.SUPABASE_URL) ||
  (typeof process !== 'undefined' && process.env && process.env.NEXT_PUBLIC_SUPABASE_URL) ||
  (typeof process !== 'undefined' && process.env && process.env.VITE_SUPABASE_URL) ||
  (typeof window !== 'undefined' && window.SUPABASE_URL) ||
  'https://sslzqfjvriasyivzvved.supabase.co';

const SUPABASE_KEY = 
  (typeof process !== 'undefined' && process.env && process.env.SUPABASE_KEY) ||
  (typeof process !== 'undefined' && process.env && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) ||
  (typeof process !== 'undefined' && process.env && process.env.VITE_SUPABASE_KEY) ||
  (typeof window !== 'undefined' && window.SUPABASE_KEY) ||
  'sb_publishable_xtG5wEmEQgaVL69ho-GY0Q_xLyUpocR';

export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
