import { Router } from 'express';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://zavymxqpzaavbmvyvqbk.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InphdnlteHFwemFhdmJtdnl2cWJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTQwNzUyNCwiZXhwIjoyMDg0OTgzNTI0fQ.XG2DAZitxPvAyv0atk4ourc8HOH3_ZpYgd_JePcmS-M';
const supabase = createClient(supabaseUrl, supabaseKey);

const router = Router();

router.post('/', async (req, res) => {
  const { imageUrl, constraints } = req.body;

  if (!imageUrl || !constraints) {
    return res.status(400).json({ error: 'imageUrl and constraints are required' });
  }

  // 在这里，我们将调用 AI 图像生成服务
  // 目前，我们只返回一个模拟的响应
  const generatedImageUrl = 'https://placehold.co/1024x768';
  const products = [
    { id: 1, name: '沙发', price: 1200, imageUrl: 'https://placehold.co/200x200' },
    { id: 2, name: '灯具', price: 300, imageUrl: 'https://placehold.co/200x200' },
  ];

  const { data, error } = await supabase
    .from('renovations')
    .insert([
      { original_image_url: imageUrl, constraints, generated_image_url: generatedImageUrl },
    ])
    .select();

  if (error) {
    return res.status(500).json({ error: error.message });
  }

  res.json({ id: data[0].id, generatedImageUrl, products });
});

export default router;
