import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://zavymxqpzaavbmvyvqbk.supabase.co';
// WARNING: This is a service role key and should be treated like a password.
// It is used here for a one-time setup script.
const supabaseServiceKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InphdnlteHFwemFhdmJtdnl2cWJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTQwNzUyNCwiZXhwIjoyMDg0OTgzNTI0fQ.XG2DAZitxPvAyv0atk4ourc8HOH3_ZpYgd_JePcmS-M';

const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function setupStorage() {
  const bucketName = 'renovations';

  // Check if the bucket already exists
  const { data: buckets, error: listError } = await supabase.storage.listBuckets();
  if (listError) {
    console.error('Error listing buckets:', listError.message);
    return;
  }

  const bucketExists = buckets.some(bucket => bucket.name === bucketName);

  if (bucketExists) {
    console.log(`Bucket "${bucketName}" already exists.`);
  } else {
    console.log(`Bucket "${bucketName}" not found. Creating it...`);
    const { error: createError } = await supabase.storage.createBucket(bucketName, {
      public: true, // Make the bucket public
    });

    if (createError) {
      console.error(`Error creating bucket:`, createError.message);
      return;
    }
    console.log(`Bucket "${bucketName}" created successfully.`);
  }

  // Define the policy
  const policyName = `Public access for ${bucketName}`;
  const policyDefinition = {
      name: policyName,
      bucket_id: bucketName,
      roles: ['anon', 'authenticated'],
      statements: [
          {
              actions: ['select', 'insert'],
              effect: 'allow'
          }
      ]
  };

  // This is a simplified representation. Actual policy creation via API is more complex
  // and typically done via SQL or the Supabase dashboard.
  // For now, we rely on the `public: true` flag and will proceed.
  console.log('Bucket is public. For finer-grained control, set up policies in the Supabase dashboard.');
}

setupStorage();
