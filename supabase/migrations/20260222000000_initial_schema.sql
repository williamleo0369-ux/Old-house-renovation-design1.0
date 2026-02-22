-- 创建商品表
CREATE TABLE products (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    image_url TEXT,
    category TEXT
);

-- 启用行级安全
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- 策略：允许公共读取，但只有服务角色能写入
CREATE POLICY "Public read access for products" ON products FOR SELECT USING (true);
CREATE POLICY "Allow service role to manage products" ON products FOR ALL USING (auth.role() = 'service_role');

GRANT SELECT ON products TO anon;
GRANT ALL ON products TO service_role;

-- 创建改造方案表
CREATE TABLE renovations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_image_url TEXT NOT NULL,
    constraints JSONB,
    generated_image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 启用行级安全
ALTER TABLE renovations ENABLE ROW LEVEL SECURITY;

-- 策略：只有服务角色可以访问
CREATE POLICY "Allow service role to manage renovations" ON renovations FOR ALL USING (auth.role() = 'service_role');

GRANT ALL ON renovations TO service_role;

-- 创建方案-商品关联表
CREATE TABLE renovation_products (
    renovation_id UUID REFERENCES renovations(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    PRIMARY KEY (renovation_id, product_id)
);

-- 启用行级安全
ALTER TABLE renovation_products ENABLE ROW LEVEL SECURITY;

-- 策略：只有服务角色可以访问
CREATE POLICY "Allow service role to manage relations" ON renovation_products FOR ALL USING (auth.role() = 'service_role');

GRANT ALL ON renovation_products TO service_role;
