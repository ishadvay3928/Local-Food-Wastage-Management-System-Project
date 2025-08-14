# Local-Food-Wastage-Management-System-Project

# 🍽️ Local Food Donation Dashboard

A Streamlit-based dashboard to manage and analyze local food donations, built with PostgreSQL as the backend database.  
The app allows users to view food listings, apply filters, contact providers, run SQL analyses, and perform CRUD operations on Providers, Food Listings, and Claims.

---

## 🚀 Features

### 🔎 Filters
- Filter food listings by **City**, **Provider**, **Food Type**, and **Meal Type**
- Only show listings with expiry date `>= CURRENT_DATE`

### 📋 Food Listings
- View available food items with quantity, expiry date, and provider details
- Real-time filtering updates
- Contact providers directly from the current filtered results

### 📊 SQL Analyses
Pre-built analysis queries, including:
- Providers per city
- Receivers per city
- Top provider type by donated quantity
- Provider contacts by city
- Top receiver by claims
- Total available (not expired) food
- Most common food types
- Claims per food item
- Percentage of claim statuses
- Expired but unclaimed items  
…and more!

### 🛠️ CRUD Operations
Manage data directly from the dashboard:
- **Providers**: Create, update, or delete provider details
- **Food Listings**: Create, update (quantity), or delete listings
- **Claims**: Create, update, or delete claims

---

## 🗂️ Project Structure

```

.
├── app.py          # Main Streamlit application
├── requirements.txt # Python dependencies
└── README.md        # Project documentation

````

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/yourusername/local-food-donation-dashboard.git
cd local-food-donation-dashboard
````

### 2️⃣ Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Database

Create a PostgreSQL database (default name: `food_wastage`).

Update environment variables in your system or `.env` file:

```env
DB_USER=postgres
DB_PASS=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=food_wastage
```

Alternatively, edit directly in `app.py`.

### 5️⃣ Run database migrations / schema

Example schema:

```sql
CREATE TABLE providers (
    provider_id SERIAL PRIMARY KEY,
    name TEXT,
    type TEXT,
    address TEXT,
    city TEXT,
    contact TEXT
);

CREATE TABLE food_listings (
    food_id SERIAL PRIMARY KEY,
    food_name TEXT,
    quantity INT,
    expiry_date DATE,
    provider_id INT REFERENCES providers(provider_id) ON DELETE CASCADE,
    provider_type TEXT,
    location TEXT,
    food_type TEXT,
    meal_type TEXT
);

CREATE TABLE receivers (
    receiver_id SERIAL PRIMARY KEY,
    name TEXT,
    city TEXT,
    contact TEXT
);

CREATE TABLE claims (
    claim_id SERIAL PRIMARY KEY,
    food_id INT REFERENCES food_listings(food_id) ON DELETE CASCADE,
    receiver_id INT REFERENCES receivers(receiver_id) ON DELETE CASCADE,
    status TEXT,
    "timestamp" DATE
);
```

### 6️⃣ Run the app

```bash
streamlit run app.py
```

---

## 📦 Requirements

`requirements.txt` example:

```
streamlit
sqlalchemy
psycopg2-binary
pandas
```

---


```
