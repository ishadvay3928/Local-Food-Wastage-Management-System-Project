# Local-Food-Wastage-Management-System-Project

## 🍽️ Local Food Donation Dashboard

A Streamlit-based dashboard to manage and analyze local food donations, now fully compatible with **SQLite**.
The app allows users to view food listings, apply filters, contact providers, run analyses, and perform CRUD operations on Providers, Food Listings, and Claims.

---

## 🚀 Features

### 🔎 Filters

* Filter food listings by **City**, **Provider**, **Food Type**, and **Meal Type**
* Only show listings with expiry date `>= CURRENT_DATE` (or current date in SQLite)

### 📋 Food Listings

* View available food items with quantity, expiry date, and provider details
* Real-time filtering updates
* Contact providers directly from the filtered results

### 📊 SQL Analyses

Pre-built analysis queries, including:

* Providers per city
* Receivers per city
* Top provider type by donated quantity
* Top receiver by claims
* Total available (not expired) food
* Most common food types
* Claims per food item
* Percentage of claim statuses
* Expired but unclaimed items
  …and more!

### 🛠️ CRUD Operations

Manage data directly from the dashboard:

* **Providers**: Create, update, or delete provider details
* **Recievers**: Create, update, or delete recievers details
* **Food Listings**: Create, update (quantity), or delete listings
* **Claims**: Create, update, or delete claims

---

## 🗂️ Project Structure

```
Local-Food-Wastage-Management-System-Project/
│── app.py                  # Main Streamlit application
│── clean_datasets/          # CSV datasets (used if DB is empty)
│── requirements.txt         # Python dependencies
└── README.md               # Project documentation
```

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yourusername/local-food-donation-dashboard.git
cd local-food-donation-dashboard
```

### 2️⃣ Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Database setup

The app supports **SQLite** by default:

* If `local_food_donation.db` exists, it will be used directly.
* If the DB is missing or empty, CSVs in `clean_datasets/` will be loaded automatically.

Example SQLite schema:

```sql
CREATE TABLE providers (
    provider_id INTEGER PRIMARY KEY,
    name TEXT,
    type TEXT,
    address TEXT,
    city TEXT,
    contact TEXT
);

CREATE TABLE food_listings (
    food_id INTEGER PRIMARY KEY,
    food_name TEXT,
    quantity INTEGER,
    expiry_date DATE,
    provider_id INTEGER REFERENCES providers(provider_id) ON DELETE CASCADE,
    provider_type TEXT,
    location TEXT,
    food_type TEXT,
    meal_type TEXT
);

CREATE TABLE receivers (
    receiver_id INTEGER PRIMARY KEY,
    name TEXT,
    city TEXT,
    contact TEXT
);

CREATE TABLE claims (
    claim_id INTEGER PRIMARY KEY,
    food_id INTEGER REFERENCES food_listings(food_id) ON DELETE CASCADE,
    receiver_id INTEGER REFERENCES receivers(receiver_id) ON DELETE CASCADE,
    status TEXT,
    timestamp DATE
);
```

---

### 5️⃣ Run the app

```bash
streamlit run app.py
```

---

## 📦 Requirements

`requirements.txt` example:

```
streamlit
sqlalchemy
pandas
plotly
```

---

## 📬 Contact

**Isha Chaudhary**
📧 [ishachaudhary3928@gmail.com](mailto:ishachaudhary3928@gmail.com)
🔗 [LinkedIn](https://www.linkedin.com/in/ishachaudhary18)
📍 Noida, India

