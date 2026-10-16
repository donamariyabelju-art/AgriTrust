"""
AgriTrust AI Farming Assistant Service
Comprehensive agronomy and marketplace knowledge assistant with clear transparency.
"""

import re

# Stemming helper for basic English inflections (plurals, verbs) without external libraries
def _stem(word):
    w = word.lower().strip()
    if len(w) <= 3:
        return w
    if w.endswith('ies') and len(w) > 4:
        return w[:-3] + 'y'
    if w.endswith('ing') and len(w) > 4:
        return w[:-3]
    if w.endswith('ed') and len(w) > 3:
        return w[:-2]
    if w.endswith('es') and len(w) > 3:
        return w[:-2]
    if w.endswith('s') and not w.endswith('ss') and len(w) > 3:
        return w[:-1]
    return w

CHAT_KNOWLEDGE_BASE = [
    {
        'topic': 'Irrigation Management',
        'keywords': ['water', 'watering', 'irrigation', 'drip', 'sprinkler', 'furrow', 'flood', 'moisture', 'drought', 'evaporation'],
        'anchors': ['irrigation', 'drip', 'watering', 'water requirement', 'drip irrigation'],
        'priority': 10,
        'response': """**Efficient Irrigation Best Practices:**
- **Drip Irrigation:** Saves 40–60% water compared to flood irrigation, reduces weed growth, and keeps plant canopies dry to prevent fungal outbreaks.
- **Critical Watering Stages:**
  - *Tomato & Vegetables:* Flowering and fruit enlargement (irregular watering causes blossom end rot and fruit splitting).
  - *Rice:* Tillering and panicle development (maintain 2-3 cm standing water).
  - *Banana:* Shooting and bunch maturation (requires 15–20 liters/plant/day in peak heat).
  - *Cucumber:* Continuous moderate moisture during active fruiting.
- **Timing:** Irrigate in the early morning or late afternoon to minimize evaporation losses."""
    },
    {
        'topic': 'Fertilizer & Plant Nutrition',
        'keywords': ['fertilizer', 'fertilizers', 'fertilizing', 'npk', 'urea', 'dap', 'potash', 'manure', 'compost', 'vermicompost', 'nutrient', 'nutrients', 'feed', 'foliar', 'zinc', 'boron', 'nitrogen', 'phosphorus', 'potassium'],
        'anchors': ['fertilizer', 'npk', 'urea', 'manure', 'dap', 'potash', 'nutrient'],
        'priority': 10,
        'response': """**Nutrient Management Strategy (NPK & Micronutrients):**
- **Basal Dose:** Apply 100% Phosphorus (P) and 30-50% Nitrogen (N) & Potassium (K) during final land preparation or sowing.
- **Top Dressing / Fertigation:** Split remaining Nitrogen and Potassium in 2-3 doses during vegetative surge and flowering to avoid leaching.
- **Micronutrients:** Foliar spray of Zinc Sulphate (0.5%) and Borax (0.2%) during flower budding prevents blossom drop and improves fruit set.
- **Bio-fertilizers:** Seed/root treatment with Azotobacter/Rhizobium and Phosphate Solubilizing Bacteria (PSB) enhances natural nutrient uptake and cuts synthetic fertilizer needs by 20%."""
    },
    {
        'topic': 'Disease Symptoms & Control',
        'keywords': ['disease', 'diseases', 'blight', 'wilt', 'mildew', 'fungus', 'fungal', 'rot', 'spot', 'spots', 'leaf spot', 'yellowing', 'curl', 'leaf curl', 'virus', 'canker', 'damping off', 'bacterial'],
        'anchors': ['disease', 'blight', 'mildew', 'wilt', 'fungus', 'rot', 'leaf spot', 'powdery mildew'],
        'priority': 10,
        'response': """**Crop Disease Identification & Treatment:**
- **Early / Late Blight:** Concentric dark target-like spots on lower leaves. Treat promptly with Mancozeb (2.5 g/L) or Copper Oxychloride (3 g/L).
- **Powdery Mildew:** White floury dusting on upper leaves. Spray Wettable Sulfur (2 g/L) or water-soluble Neem formulations.
- **Bacterial Wilt:** Sudden foliage drooping without initial yellowing. Uproot affected plants and drench surrounding soil with Copper Oxychloride.
- **Leaf Curl Virus:** Transmitted by whiteflies. Control whitefly vectors using sticky traps and neem sprays.
- *Tip:* You can also use our **Crop Health Scanner** to upload a leaf photograph for computer vision diagnosis!"""
    },
    {
        'topic': 'Integrated Pest Management (IPM)',
        'keywords': ['pest', 'pests', 'insect', 'insects', 'worm', 'worms', 'caterpillar', 'caterpillars', 'borer', 'borers', 'aphid', 'aphids', 'whitefly', 'whiteflies', 'thrip', 'thrips', 'mite', 'mites', 'neem', 'trap', 'traps', 'pesticide', 'pesticides', 'spray', 'spraying'],
        'anchors': ['pest', 'insect', 'whitefly', 'aphid', 'borer', 'neem oil', 'pesticide', 'worm'],
        'priority': 10,
        'response': """**Integrated Pest Management (IPM):**
1. **Physical & Cultural:** Install yellow sticky traps (15–20 traps/acre) for whiteflies and aphids, and blue sticky traps for thrips. Use pheromone traps for fruit/stem borers.
2. **Bio-pesticides:** Spray Neem Seed Kernel Extract (NSKE 5%) or 10,000 ppm cold-pressed Neem Oil (3 ml/liter) at the first sighting of sucking pests.
3. **Biological Control:** Release Trichogramma egg parasitoids against bollworms and fruit borers.
4. **Targeted Remediation:** Use systemic insecticides (e.g. Imidacloprid or Chlorantraniliprole) only as a last resort when pest population crosses economic threshold levels (ETL)."""
    },
    {
        'topic': 'Soil Preparation',
        'keywords': ['soil', 'prepare', 'preparation', 'land', 'plow', 'plowing', 'tillage', 'ph', 'hardpan', 'bed', 'loam', 'clay', 'black soil', 'alluvial', 'red soil'],
        'anchors': ['soil', 'soil preparation', 'plow', 'tillage', 'land prep'],
        'priority': 8,
        'response': """**Soil Preparation Guidelines:**
1. **Soil Testing:** Test pH (ideal is 6.0 - 7.5 for most vegetables) and available N-P-K plus organic carbon.
2. **Deep Tillage:** Perform 1-2 deep plowings to break hardpan layers and expose soil-borne grubs and fungal pathogens to sunlight.
3. **Organic Matter:** Incorporate 5–8 tons of well-decomposed Farm Yard Manure (FYM) or 2.5 tons of vermicompost per acre 2-3 weeks before sowing or transplanting.
4. **Bed Formation:** Make raised beds (15–20 cm high, 90–120 cm wide) to prevent waterlogging and facilitate furrow or drip irrigation.
5. **Soil Type Notes:** Black soils require good drainage; sandy/loamy soils benefit from higher organic mulch to retain moisture."""
    },
    {
        'topic': 'Harvest Reservations',
        'keywords': ['reserve', 'reservation', 'reservations', 'contract', 'contracts', 'advance', 'future harvest', 'future harvests', 'pre-book', 'booking', 'advance booking'],
        'anchors': ['reservation', 'reservations', 'future harvest', 'advance booking', 'reserve', 'harvest reservation'],
        'priority': 10,
        'response': """**How Harvest Reservations Work on AgriTrust:**
- Farmers can list upcoming harvests 3–6 weeks before picking date in the **Harvest Reservations** section.
- Commercial buyers and cooperatives lock in advance bookings at an agreed price per kg.
- This secures guaranteed market demand before crops are cut, virtually eliminating distress sales and post-harvest spoilage."""
    },
    {
        'topic': 'Harvesting Timing & Techniques',
        'keywords': ['harvest', 'harvests', 'harvesting', 'mature', 'maturity', 'picking', 'yield', 'yields', 'post-harvest', 'spoilage', 'storage', 'crate', 'crates'],
        'anchors': ['picking', 'maturity', 'harvest timing', 'post-harvest'],
        'priority': 6,
        'response': """**Harvesting Recommendations & Techniques:**
- **Tomatoes:** Harvest at 'breaker' or 'pink' stage if sending to distant markets; harvest at full-red ripe for direct local delivery.
- **Cucumber:** Pick when fruits are firm, crisp, and deep green before skin yellowing starts (usually every 2-3 days).
- **Rice:** Harvest when 85–90% of panicle grains turn golden straw color and grain moisture is approximately 20-22%.
- **Banana:** Cut bunches when top fingers are three-quarters rounded and angles are less sharp.
- **Handling:** Harvest in the cool morning hours, avoid dropping fruits, and transfer immediately to shaded, ventilated cooling sheds."""
    },
    {
        'topic': 'Price Intelligence & Fair Pricing',
        'keywords': ['price', 'prices', 'pricing', 'fair price', 'mandi', 'rate', 'rates', 'cost', 'costs', 'market rate', 'benchmark', 'apmc'],
        'anchors': ['fair price', 'mandi', 'rate', 'mandi rate', 'benchmark price'],
        'priority': 8,
        'response': """**Fair Price Intelligence on AgriTrust:**
- Our **Fair Price Advisor** displays benchmark wholesale reference bands, historical averages, and active buyer procurement bids.
- Farmers retain 100% autonomy to set their farm-gate asking price based on cultivation costs, organic status, and quality grade.
- Cutting out intermediary commissions typically gives farmers 15%–30% higher net margins while offering competitive prices to bulk buyers."""
    },
    {
        'topic': 'Direct Marketplace Guidelines',
        'keywords': ['market', 'marketplace', 'sell', 'selling', 'list', 'listing', 'product', 'products', 'buyer', 'buyers', 'direct sale', 'procurement', 'order', 'orders'],
        'anchors': ['marketplace', 'list produce', 'sell produce', 'direct marketplace'],
        'priority': 8,
        'response': """**How to Sell Directly on AgriTrust Marketplace:**
1. Navigate to **Direct Marketplace** and click **+ List Fresh Produce**.
2. Fill in produce details: crop variety, harvest date, available quantity, grade, and farm location.
3. Upload produce photos and optional quality certificates (pesticide test, organic certificate).
4. Verified buyers can view your listing and place purchase orders directly. You receive real-time notifications for incoming orders!"""
    },
    {
        'topic': 'Traceability & Trust',
        'keywords': ['traceability', 'batch', 'batches', 'batch id', 'qr', 'qr code', 'verify', 'verification', 'uhvc', 'hvc', 'trust', 'passport', 'audit'],
        'anchors': ['traceability', 'batch', 'uhvc', 'qr code', 'verification', 'trace batch'],
        'priority': 8,
        'response': """**Farm-to-Table Traceability & Quality Verification:**
- Every registered harvest lot receives a unique **UHVC Code** (Unique Harvest Verification Code).
- AgriTrust tracks the product journey: Farm Origin → Harvested → Quality Check → Packaging → In Transit → Delivered.
- Verified batches generate a public digital traceability certificate with an auditable QR code that buyers can scan to verify origin, pesticide checks, and harvest freshness."""
    },
    {
        'topic': 'Tomato Cultivation Guide',
        'keywords': ['tomato', 'tomatoes', 'roma', 'lycopersicon', 'blossom rot', 'tomato plant', 'tomato farming'],
        'anchors': ['grow tomato', 'tomato guide', 'tomato farming', 'tomato cultivation'],
        'priority': 7,
        'response': """**Tomato Cultivation Best Practices:**
- **Soil & Climate:** Well-drained loamy to black soils with pH 6.0–7.0. Optimal day temperature 21–28°C.
- **Spacing:** Raised beds with 60 cm plant-to-plant and 90 cm row-to-row spacing.
- **Irrigation & Nutrition:** Drip irrigation ensures uniform moisture and prevents fruit splitting. High Potassium requirement during fruiting. Spray calcium chloride (0.5%) to prevent Blossom End Rot.
- **Pest & Disease:** Yellow sticky traps for whiteflies; copper spray for early blight. Stake plants with bamboo or trellis wire for maximum yield."""
    },
    {
        'topic': 'Rice / Paddy Cultivation Guide',
        'keywords': ['rice', 'paddy', 'basmati', 'pusa', 'grain', 'grains', 'rice farming', 'grow rice'],
        'anchors': ['grow rice', 'rice farming', 'basmati farming', 'paddy cultivation'],
        'priority': 7,
        'response': """**Rice (Basmati & Paddy) Cultivation Handbook:**
- **Soil & Climate:** Heavy clay or alluvial soils with high water retention capacity.
- **Transplanting:** Transplant 21–25 day old seedlings (2–3 seedlings per hill) with 20 cm x 15 cm spacing.
- **Water Management:** Maintain 2–3 cm standing water during tillering and panicle initiation. Drain field 10–12 days before harvest.
- **Nutrient Application:** Apply Urea in 3 splits (basal, tillering, panicle emergence). Add Zinc Sulphate (25 kg/ha) at planting."""
    },
    {
        'topic': 'Cucumber Cultivation Guide',
        'keywords': ['cucumber', 'cucumbers', 'cucurbit', 'crispy cucumber', 'grow cucumber'],
        'anchors': ['grow cucumber', 'cucumber guide', 'cucumber farming'],
        'priority': 7,
        'response': """**Cucumber Cultivation Handbook:**
- **Soil & Climate:** Warm climate (25–35°C) and fertile sandy loam soil with good drainage.
- **Trellising:** Use net trellises or vertical staking to keep fruits clean, straight, and prevent ground rot.
- **Watering:** Drip irrigation at regular intervals; moisture stress leads to fruit bitterness.
- **Disease Protection:** Watch for powdery and downy mildew. Treat with sulfur spray or neem oil at first signs."""
    },
    {
        'topic': 'Banana Cultivation Guide',
        'keywords': ['banana', 'bananas', 'grand naine', 'sucker', 'suckers', 'bunch', 'banana farming'],
        'anchors': ['grow banana', 'banana plantation', 'banana farming'],
        'priority': 7,
        'response': """**Banana (Grand Naine) Cultivation Guidelines:**
- **Soil & Spacing:** Deep alluvial or rich loamy soil. Plant tissue-culture plantlets with 1.8 m x 1.8 m spacing.
- **Water & Nutrition:** Heavy feeder: requires 15–20 L water/day/plant and high potassium fertigation during shooting.
- **Bunch Care:** Cover bunches with blue polyethylene sleeves to protect fingers from thrips and sunburn."""
    },
    {
        'topic': 'Bell Pepper / Capsicum Guide',
        'keywords': ['bell pepper', 'bell peppers', 'capsicum', 'peppers', 'greenhouse pepper', 'capsicum farming'],
        'anchors': ['bell pepper', 'capsicum', 'grow bell pepper'],
        'priority': 7,
        'response': """**Bell Pepper (Capsicum) Cultivation Guidelines:**
- **Environment:** Greenhouse or shade-net cultivation is ideal for temperature control (20–25°C).
- **Soil:** Rich loamy soil with pH 6.0–6.8 and high organic content.
- **Pruning & Trellising:** Prune to 2 or 4 main stems and support with nylon twine.
- **Harvest:** Pick green when firm and glossy, or allow full red/yellow coloring for premium market prices."""
    },
    {
        'topic': 'Crop Recommendation & Planning',
        'keywords': ['recommend', 'recommendation', 'recommendations', 'what to grow', 'suitable crop', 'crop selection', 'which crop', 'season', 'kharif', 'rabi', 'zaid', 'grow'],
        'anchors': ['what to grow', 'crop recommendation', 'which crop', 'what should i grow', 'what crop should i grow'],
        'priority': 9,
        'response': """**Crop Planning & Suitability Engine:**
- On AgriTrust, navigate to **What to Grow** (Crop Recommendation).
- Enter your land area, soil classification (Black, Alluvial, Loamy, Clay, Sandy), season (Kharif, Rabi, Zaid), and irrigation status.
- Our algorithmic engine ranks the best-performing crops, calculates estimated yield, input expenses, and projected net profit per acre!"""
    },
    {
        'topic': 'Crop Health Scanner',
        'keywords': ['scan', 'scanner', 'camera', 'photo', 'leaf scan', 'disease detection', 'opencv', 'diagnose', 'diagnosis', 'leaf image'],
        'anchors': ['scan', 'scanner', 'leaf scan', 'crop health scanner'],
        'priority': 9,
        'response': """**How to Use the Crop Health Scanner:**
1. Open **Crop Health** in the main navigation.
2. Take or upload a clear, focused photo of an affected leaf in good lighting.
3. AgriTrust's image processing engine inspects lesion patterns, color shifts, and necrotic spots.
4. You receive an instant diagnostic assessment with severity score and recommended organic/conventional remediation steps!"""
    },
    {
        'topic': 'Weather & Farm Advisory',
        'keywords': ['weather', 'rain', 'temperature', 'humidity', 'forecast', 'wind', 'monsoon', 'advisory', 'climate'],
        'anchors': ['weather', 'forecast', 'rain', 'weather advisory'],
        'priority': 9,
        'response': """**Weather & Field Advisory on AgriTrust:**
- Visit **Weather & Advisory** in your dashboard.
- Get live temperature, humidity, rainfall probability, and wind metrics for your farm district.
- Includes operational agronomic advisories: optimal morning spray windows, leaf wetness alerts, and drip irrigation scheduling."""
    }
]

DEFAULT_RESPONSE = """Hello! I am **AgriTrust AI**, your agricultural decision support assistant.
I can assist you with:
- **Crop Planning & Soil Prep:** Choosing optimal crops, testing soil, and bed preparation.
- **Irrigation & Plant Nutrition:** Drip scheduling, N-P-K ratios, and organic manure.
- **Pest & Disease Control:** Identifying symptoms, organic neem remedies, and IPM.
- **Specific Crop Guides:** Cultivation manuals for Tomatoes, Rice, Bananas, Cucumbers, and Bell Peppers.
- **Direct Marketplace:** Listing produce, fair price intelligence, and harvest advance bookings.

How may I assist your farm today?"""

SUGGESTED_PROMPTS = [
    "What is the best fertilizer schedule for tomatoes?",
    "How do I prevent powdery mildew in cucumbers?",
    "How does harvest reservation work?",
    "What soil preparation is needed for basmati rice?",
    "How do I list my produce directly for buyers?"
]

def get_chatbot_response(user_query):
    raw_query = user_query.strip()
    query = raw_query.lower()

    if not query:
        return {
            'reply': DEFAULT_RESPONSE,
            'topic': 'General Assistant',
            'suggested_questions': SUGGESTED_PROMPTS,
            'is_rule_based': True
        }

    # 1. Chit-chat / Politeness handling
    if re.search(r'\b(thank|thanks|dhanyawad|shukriya)\b', query, re.IGNORECASE):
        return {
            'reply': "You are very welcome! May your crops yield abundantly. If you have any more questions about fertilizers, pests, weather, or selling produce, feel free to ask anytime!",
            'topic': 'Assistant Greeting',
            'suggested_questions': SUGGESTED_PROMPTS[:3],
            'is_rule_based': True
        }

    if re.search(r'\b(who are you|what can you do|about you|help me)\b', query, re.IGNORECASE) and len(query.split()) <= 6:
        return {
            'reply': DEFAULT_RESPONSE,
            'topic': 'General Assistant',
            'suggested_questions': SUGGESTED_PROMPTS,
            'is_rule_based': True
        }

    # Isolated greetings without agronomic query
    if re.search(r'^(hi|hello|hey|namaste|good morning|good afternoon|good evening)[!.,? ]*$', query, re.IGNORECASE):
        return {
            'reply': DEFAULT_RESPONSE,
            'topic': 'General Assistant',
            'suggested_questions': SUGGESTED_PROMPTS,
            'is_rule_based': True
        }

    # 2. Tokenize and stem user query words
    query_tokens = re.findall(r'[a-z0-9]+', query)
    stemmed_tokens = set(_stem(t) for t in query_tokens)

    # 3. Match against knowledge base with weighted scoring + priority
    best_match = None
    best_score = 0

    for item in CHAT_KNOWLEDGE_BASE:
        score = 0
        base_priority = item.get('priority', 5)

        # Anchor matching (highest weight)
        for anchor in item.get('anchors', []):
            anchor_lower = anchor.lower()
            if ' ' in anchor_lower:
                if anchor_lower in query:
                    score += 15 + base_priority
            else:
                if anchor_lower in query_tokens:
                    score += 10 + base_priority
                elif _stem(anchor_lower) in stemmed_tokens:
                    score += 8 + base_priority

        # Keyword matching
        for kw in item['keywords']:
            kw_lower = kw.lower()
            if ' ' in kw_lower:
                if kw_lower in query:
                    score += 6
            else:
                if kw_lower in query_tokens:
                    score += 4
                elif _stem(kw_lower) in stemmed_tokens:
                    score += 2

        if score > best_score:
            best_score = score
            best_match = item

    # If confidence threshold met
    if best_match and best_score >= 6:
        return {
            'reply': best_match['response'],
            'topic': best_match['topic'],
            'suggested_questions': SUGGESTED_PROMPTS[:3],
            'is_rule_based': True
        }

    # If greeting accompanied by other words but no strong match
    if re.search(r'\b(hi|hello|hey|namaste)\b', query, re.IGNORECASE):
        return {
            'reply': DEFAULT_RESPONSE,
            'topic': 'General Assistant',
            'suggested_questions': SUGGESTED_PROMPTS,
            'is_rule_based': True
        }

    # 4. Helpful contextual fallback
    return {
        'reply': f"I received your question about: *'{raw_query}'*.\n\nHere are some quick pointers from AgriTrust's agronomic advisory:\n- **Crop Nutrition:** Apply basal N-P-K at sowing and foliar sprays during flowering.\n- **Irrigation:** Use drip lines to conserve water and prevent foliar fungal diseases.\n- **Pest Management:** Deploy sticky traps and spray cold-pressed neem oil (3 ml/L) at first sighting.\n- **Marketplace & Booking:** You can list harvested produce or lock in advance harvest reservations directly.\n\nCould you try rephrasing with specific terms like *tomato*, *fertilizer*, *pest*, *blight*, *irrigation*, or *reservation*?",
        'topic': 'Agronomic Guidance',
        'suggested_questions': SUGGESTED_PROMPTS[:3],
        'is_rule_based': True
    }
