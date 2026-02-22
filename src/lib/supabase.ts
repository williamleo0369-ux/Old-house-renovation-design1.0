import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://zavymxqpzaavbmvyvqbk.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InphdnlteHFwemFhdmJtdnl2cWJrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk0MDc1MjQsImV4cCI6MjA4NDk4MzUyNH0.PbaAnGlo8i0ec00F35iZz5TRmfax8WlMTAX2ZjzmQ_s';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
