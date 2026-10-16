# AgriTrust — Smart Agriculture Decision Support & Direct Farmer-to-Buyer Marketplace

> **Tagline:** *"Grow Smarter. Sell Fairer. Build Trust."*

AgriTrust is a comprehensive, production-grade agricultural decision support system and direct marketplace web application built in **Python and Flask**. It enables farmers to make data-driven agronomic choices, detect crop diseases early, understand real wholesale market demand, secure advance harvest reservations, and trade directly with commercial buyers without exploitative intermediaries.

---

## 1. System Architecture

```
                    Browser (Client)
                           │
                           ▼
                  HTML5 + CSS3 + Jinja2
             (Chart.js + Responsive UI)
                           │
                           ▼
                      Python Flask
            (Routes, Blueprints, Sessions)
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     Agronomy & AI   Computer Vision    MySQL DB
     Decision Rules     & OpenCV      (SQLAlchemy)
  (Suitability/Chat)  (Preprocess/TF) (Models/Ledger)
```

### AI Crop Disease Detection Pipeline:
```
Leaf Image Upload ──► OpenCV Validation & Preprocessing ──► TensorFlow/Keras Classifier ──► Actionable Pathology Advisory
```

---

## 2. Implemented Features

1. **Farmer Authentication & RBAC**:
   - Role-Based Access Control (`FARMER`, `BUYER`, `ADMIN`).
   - Werkzeug secure password hashing and protected session state.
   - Strict data ownership: farmers can only modify their own crops, farms, and batches.
2. **Farmer Decision Dashboard ("What Should I Do Today?")**:
   - Automated daily prioritized tasks (harvest preparations, scouting alerts, drip irrigation checks).
   - Real-time farm cards: registered holdings, active plantings, total direct revenue, reserved future volume.
   - Interactive Chart.js visualizations for monthly revenue and crop health distribution.
3. **Farm Land Management**:
   - Full CRUD operations for farm holdings (soil classification, acreage, irrigation type, location).
4. **Crop Cycle Monitoring**:
   - Tracking development phases (Germination, Vegetative, Flowering, Fruiting, Maturation, Harvest Ready).
   - Dynamic progress indicators, expected harvest dates, expenses, and projected returns.
5. **Crop Recommendation Engine ("What Should I Grow?")**:
   - Multi-parameter evaluation: location, acreage, soil chemistry, season, and water availability.
   - Transparent agronomic suitability score, projected yield, input costs, and estimated net profit.
6. **Crop Health Scanner (OpenCV & Computer Vision)**:
   - Server-side image validation (allowed extensions, OpenCV decoding, minimum resolution check).
   - TensorFlow/Keras model integration structure (`ai/models/crop_disease_model.h5`).
   - Integrated heuristic agronomy scanner with full pathology details (symptoms, causes, preventive measures, next steps).
   - Prominent agricultural advisory disclaimer.
7. **Smart Farming Guide**:
   - Step-by-step 11-stage agricultural manuals for staple crops (**Tomato, Rice, Banana, Cucumber**).
   - Covers soil prep, seed selection, transplanting, drip irrigation, N-P-K nutrition, IPM pest control, harvesting, and marketing.
8. **AgriTrust AI Farming Assistant (Chatbot)**:
   - Interactive conversational assistant answering agronomy queries with suggested question pills.
   - Pattern-matched knowledge base for soil preparation, fertilizers, disease prevention, and marketplace policies.
9. **Weather & Crop Advisory**:
   - Agrometeorology monitoring with OpenWeatherMap API integration.
   - Automated field advisories (rain probability, leaf wetness, optimal morning irrigation windows).
   - Honest fallback demonstration mode when API key is unconfigured.
10. **Direct Farmer-to-Buyer Marketplace**:
    - "DIRECT FROM FARMER" produce listings with grading, location, and transparent farm-gate pricing.
    - Search, category filters, and price range filters.
    - Transactional purchase orders with atomic stock decrements and explicit Pay-on-Delivery / Demo status.
11. **Harvest Reservation System**:
    - Advance listing of future crops weeks ahead of picking.
    - Capacity limits enforced on the backend to prevent overbooking.
12. **Harvest Verification & Farm-to-Table Traceability**:
    - Unique auditable Batch IDs (`BATCH-2026-XXXX`).
    - 6-stage lifecycle progression: *Farm Origin ➔ Harvested ➔ Verified ➔ Quality Check ➔ Packaging ➔ In Transit / Delivered*.
    - Public digital batch passport and certificate view.
13. **Farmer Trust Profile**:
    - Calculated trust indicators derived strictly from database records: completed orders, verified batches, buyer rating average, and delivery reliability rate.
14. **Revenue Analytics**:
    - Total realized revenue, volume delivered, average price per kg, and crop-wise revenue contribution charts.
15. **Food Waste Reduction Dashboard**:
    - Shelf-life risk alerts for unsold vegetable lots.
    - One-click quick-sale bulk discounts to clear inventory before spoilage.
16. **Admin Moderation**:
    - Platform oversight, user role management, and independent harvest batch verification.

---

## 3. Technology Stack

- **Backend**: Python 3.10+ / Flask 3.1+
- **Database**: MySQL 8.0+ via SQLAlchemy & PyMySQL (with automatic fallback to local SQLite for zero-configuration testing)
- **Computer Vision**: OpenCV (`cv2`)
- **AI / ML**: TensorFlow / Keras
- **Frontend**: HTML5, CSS3 (Custom Design System), Jinja2, Vanilla JavaScript
- **Visualizations**: Chart.js

---

## 4. Installation & Setup Instructions

### Step 1: Clone or Navigate to Directory
```bash
cd "d:\Anuja\Agritrust real"
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configuration variables in `.env`:
```ini
SECRET_KEY=your-secure-random-secret-key
PORT=5000

# MySQL Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=agritrust_db
DB_USER=root
DB_PASSWORD=your_mysql_password

# Set to True to allow automatic fallback to local SQLite if MySQL is offline
USE_SQLITE_FALLBACK=True

# Optional External API Keys:
WEATHER_API_KEY=your_openweathermap_api_key
AI_API_KEY=
```

---

## 5. MySQL Database Setup

1. Open MySQL CLI or MySQL Workbench:
```sql
CREATE DATABASE IF NOT EXISTS agritrust_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Run the schema creation script:
```bash
mysql -u root -p agritrust_db < database/schema.sql
```

3. (Optional) Populate initial seed records:
```bash
mysql -u root -p agritrust_db < database/seed.sql
```

*Note: If MySQL is not running locally, AgriTrust automatically initializes SQLite (`agritrust.db`) and seeds the default test accounts automatically upon first startup.*

---

## 6. How to Run the Application

Start the Flask development server:
```bash
python app.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

---

## 7. Demo Accounts & Credentials

| Role | Username | Password | Email |
| :--- | :--- | :--- | :--- |
| **Farmer** | `farmer1` | `Farmer@123` | `farmer@agritrust.com` |
| **Buyer** | `buyer1` | `Buyer@123` | `buyer@agritrust.com` |
| **Admin** | `admin` | `Admin@123` | `admin@agritrust.com` |

---

## 8. Automated Testing

Run the comprehensive pytest suite:
```bash
python -m pytest tests/test_app.py -v
```

All 11 test modules test registration, login, crop and farm management, recommendation algorithms, OpenCV scanner validation, order limits, and role access control.

---

## 9. Required Models & External APIs

1. **Crop Disease Model (Optional)**:
   - Expected path: `ai/models/crop_disease_model.h5`
   - Input shape: `(224, 224, 3)` normalized `float32` RGB.
   - When not placed in directory, AgriTrust displays a clear configuration notice and activates transparent OpenCV heuristic pathology scanning.
2. **Weather API (Optional)**:
   - Provider: OpenWeatherMap Free API.
   - Configure: Set `WEATHER_API_KEY` in `.env`.
   - When absent, AgriTrust displays sample regional agrometeorological values clearly labeled as demonstration data.

---

## 10. Transparency & Known Limitations

- **Advisory Nature**: AI diagnoses and crop recommendations are advisory decision aids. In real-world farming, local soil tests and agricultural extension officer consultations are recommended.
- **Payment Processing**: Orders use explicit Pay-on-Delivery or Direct Demo Settlement; no fake payment gateway transactions are executed.
- **Traceability Verification**: Harvest batches distinguish registered self-attested lots from officially verified inspection certificates.

