-- AgriTrust Initial Seed Data
USE agritrust_db;

-- 1. Seed Users (Farmer, Buyer, Admin)
INSERT INTO users (id, username, email, password_hash, role, full_name, phone, location, bio) VALUES
(1, 'farmer1', 'farmer@agritrust.com', 'scrypt:32768:8:1$SYPNyF9i3UV8OiaA$246c38f86cbda496d6a25d3c84cea2224a72ff5225b0ef72f28343bf2200bd7e55dc8916e2c272294464221194ff1ed9702faf6867d1b21b90154f6339e5fbba', 'FARMER', 'Ramesh Patel', '+91 98765 43210', 'Nashik, Maharashtra', 'Organic vegetable and grain farmer with over 15 years experience in sustainable agriculture.'),
(2, 'buyer1', 'buyer@agritrust.com', 'scrypt:32768:8:1$38DhYpdQBg7FP2ul$3069ceac6e8d86bdd6eb29b396d6d48fd79c28ff497e80e3a84fbe8fe30b98eef0eb5c15da8a8340505231b85015547305f7e48c5cc9cd5a1384860fd4211964', 'BUYER', 'FreshMart Wholesale Co.', '+91 91234 56789', 'Mumbai, Maharashtra', 'Procuring directly from regional growers to deliver farm-fresh harvest to urban communities.'),
(3, 'admin', 'admin@agritrust.com', 'scrypt:32768:8:1$pcLLmLxCa8sie5v1$0d989996f31183173394c3929d9dc61ae144612c5ba3e7e20f550159a5b02ee63fe7755e630cecb39f4fd5bf862320f3d206dd15315d7ddbe4aa1ac6890861eb', 'ADMIN', 'AgriTrust Platform Admin', '+91 99999 88888', 'Pune, Maharashtra', 'System administrator maintaining trust standards, marketplace integrity and agronomy intelligence.');

-- 2. Seed Farms
INSERT INTO farms (id, user_id, name, location, land_area, soil_type, irrigation_method) VALUES
(1, 1, 'Green Valley Organic Estate', 'Dindori Road, Nashik', 6.5, 'Black Soil (Regur)', 'Drip Irrigation'),
(2, 1, 'Godavari Riverside Agro Farm', 'Niphad, Nashik', 4.2, 'Alluvial Soil', 'Sprinkler & Canal');

-- 3. Seed Crops
INSERT INTO crops (id, user_id, farm_id, crop_name, planting_date, growth_stage, growth_percentage, expected_harvest_date, expected_yield, production_cost, expected_revenue, health_status) VALUES
(1, 1, 1, 'Tomato (Roma Hybrid)', '2026-08-15', 'Fruiting', 72, '2026-10-28', 4200.0, 18500.0, 63000.0, 'Healthy'),
(2, 1, 1, 'Cucumber (English Crispy)', '2026-09-01', 'Flowering', 55, '2026-11-10', 2800.0, 11200.0, 39200.0, 'Healthy'),
(3, 1, 2, 'Basmati Rice (Pusa 1121)', '2026-07-10', 'Maturation', 88, '2026-10-20', 6500.0, 32000.0, 143000.0, 'Healthy'),
(4, 1, 2, 'Grand Naine Banana', '2026-03-20', 'Vegetative', 40, '2026-12-15', 8500.0, 41000.0, 127500.0, 'Moderate Risk');

-- 4. Seed Products in Marketplace
INSERT INTO products (id, user_id, crop_id, title, category, quantity, initial_quantity, unit, price_per_unit, location, harvest_date, image_url, quality_grade, description, availability_status) VALUES
(1, 1, 1, 'Farm-Fresh Vine Tomatoes (Grade A)', 'Vegetables', 1200.0, 1500.0, 'kg', 22.0, 'Nashik, Maharashtra', '2026-10-08', 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=600&q=80', 'Grade A', 'Naturally ripened, pesticide-tested red tomatoes harvested fresh from the vine. Ideal for markets, culinary hubs, and processing.', 'Available'),
(2, 1, 2, 'Crisp Green English Cucumbers', 'Vegetables', 850.0, 1000.0, 'kg', 18.0, 'Nashik, Maharashtra', '2026-10-09', 'https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?auto=format&fit=crop&w=600&q=80', 'Grade A', 'Crunchy, thin-skinned English cucumbers cultivated under drip irrigation. High moisture and zero bitterness.', 'Available'),
(3, 1, 3, 'Aromatic Pusa Basmati Paddy Grain', 'Grains', 3500.0, 3500.0, 'kg', 38.0, 'Niphad, Maharashtra', '2026-10-05', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=600&q=80', 'Certified Organic', 'Long-grain aromatic basmati paddy harvested naturally. Low moisture content and uniform kernel length.', 'Available');

-- 5. Seed Future Harvests (for advance reservation)
INSERT INTO future_harvests (id, farmer_id, crop_name, expected_harvest_date, expected_quantity, reserved_quantity, target_price_per_kg, location, status, notes) VALUES
(1, 1, 'Red Bell Peppers (Capsicum)', '2026-11-05', 2000.0, 500.0, 42.0, 'Nashik, Maharashtra', 'Open for Reservation', 'High demand greenhouse crop. Advance booking locks price and guarantees immediate post-harvest dispatch.'),
(2, 1, 'Export Quality Grand Naine Banana', '2026-12-15', 5000.0, 1200.0, 24.0, 'Niphad, Maharashtra', 'Open for Reservation', 'Uniform hand clusters, treated with organic bio-fertilizers. Perfect for supermarket chains.');

-- 6. Seed Reservations
INSERT INTO reservations (id, user_id, future_harvest_id, farmer_id, crop_name, reserved_quantity, unit_price, total_estimated_amount, expected_harvest_date, status, contact_phone, delivery_address, notes) VALUES
(1, 2, 1, 1, 'Red Bell Peppers (Capsicum)', 500.0, 42.0, 21000.0, '2026-11-05', 'Confirmed', '+91 91234 56789', 'FreshMart Central Cold Hub, Vashi APMC, Navi Mumbai', 'Advance reservation locked for November delivery batch.');

-- 7. Seed Traceability Batches
INSERT INTO harvest_batches (id, batch_code, user_id, farm_id, crop_id, crop_name, harvest_date, quantity, unit, verification_status, is_independently_verified, verifier_name, verification_date, quality_grade, quality_score, journey_stage, storage_conditions, packaging_date, dispatch_date, notes) VALUES
(1, 'BATCH-2026-TM981', 1, 1, 1, 'Tomato (Roma Hybrid)', '2026-10-08', 1500.0, 'kg', 'Verified', 1, 'Nashik Agri Quality Inspection Agency', '2026-10-09', 'Grade A', 94, 'Packaging', 'Cold storage (12°C, 85% RH)', '2026-10-10', NULL, 'Pesticide residue test passed with zero banned synthetic chemical residues.');

-- 8. Seed Buyer Demands
INSERT INTO buyer_demands (id, buyer_id, crop_name, required_quantity, available_supply, unit, location, demand_level, target_price, required_date, description, status, is_sample_data) VALUES
(1, 2, 'Ripe Tomato (Processing Grade)', 5000.0, 1200.0, 'kg', 'Mumbai Wholesale Terminal', 'High', 21.0, '2026-10-30', 'Bulk requirement for urban grocery store network. Direct farmer delivery preferred.', 'Active', 0),
(2, 2, 'Milled Basmati Rice', 10000.0, 3500.0, 'kg', 'Pune Distribution Hub', 'Urgent', 40.0, '2026-11-15', 'Bulk procurement for export packaging. Moisture must be below 13%.', 'Active', 0);

-- 9. Seed Orders
INSERT INTO orders (id, order_number, buyer_id, product_id, quantity, unit_price, total_amount, status, payment_status, delivery_address, contact_phone, notes) VALUES
(1, 'ORD-2026-E49A11', 2, 1, 300.0, 22.0, 6600.0, 'Delivered', 'Paid (Demo)', 'FreshMart Store #14, Bandra West, Mumbai', '+91 91234 56789', 'Order completed with verified direct delivery.');

-- 10. Seed Reviews
INSERT INTO reviews (id, order_id, buyer_id, farmer_id, rating, comment) VALUES
(1, 1, 2, 1, 5, 'Exceptional produce freshness! The tomatoes arrived uniformly graded with zero transit damage. Direct farmer buying made pricing transparent.');

-- 11. Seed Notifications
INSERT INTO notifications (id, user_id, title, message, category, is_read) VALUES
(1, 1, 'Farming Alert: Pest Scouting Window', 'Weather conditions favorable for early leaf spot in high-humidity zones. Inspect lower leaves today.', 'alert', 0),
(2, 1, 'New Marketplace Order Received', 'Buyer FreshMart Wholesale Co. placed order ORD-2026-E49A11 for 300 kg Tomatoes.', 'order', 1);
