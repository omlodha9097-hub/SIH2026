import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// The values below represent the environment variables from the .env file.
// In a purely static environment without a bundler, we initialize the client here directly.
const SUPABASE_URL = 'https://sslzqfjvriasyivzvved.supabase.co';
const SUPABASE_KEY = 'sb_publishable_xtG5wEmEQgaVL69ho-GY0Q_xLyUpocR';

export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// Mock user ID for the farmer to simulate an authenticated session
export const currentFarmerId = 'farmer-mock-1234';
