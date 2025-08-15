# app.py
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# ---- PAGE CONFIG ----
st.set_page_config(page_title="Local Food Donation Dashboard", layout="wide")

# ---- DATABASE CONNECTION ----
DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# ---- QUERY FUNCTIONS ----
@st.cache_data(ttl=60)
def q(sql, params=None):
    """Execute a SELECT query and return a dataframe."""
    with engine.connect() as conn:
        if params:
            df = pd.read_sql(text(sql), conn, params=params)
        else:
            df = pd.read_sql(text(sql), conn)
    return df

def exec_write(sql, params=None):
    """Execute INSERT, UPDATE, DELETE queries."""
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})

# ---- LOAD CSVS INTO DATABASE ----
def load_csv_if_empty(table_name, csv_file):
    """Load CSV into Neon only if table is empty."""
    try:
        count = q(f"SELECT COUNT(*) AS cnt FROM {table_name};")["cnt"][0]
    except Exception:
        count = 0
    if count == 0:
        df = pd.read_csv(csv_file)
        df.columns = [c.lower() for c in df.columns]  # enforce lowercase schema
        df.to_sql(table_name, engine, if_exists="append", index=False)  # no dropping!
        st.info(f"📥 Loaded {table_name} from CSV ({len(df)} rows)")

# Mapping tables to CSV files
base_path = r"D:\DOCUMENTS\DATA ANALYTICS PROJECTS\Local Food Wastage Management System Project\clean datasets"
csv_files = {
    "providers": os.path.join(base_path, "providers_clean_dataset.csv"),
    "receivers": os.path.join(base_path, "receivers_clean_dataset.csv"),
    "food_listings": os.path.join(base_path, "food_listing_clean_dataset.csv"),
    "claims": os.path.join(base_path, "claims_clean_dataset.csv")
}

# ---- PAGE TITLE ----
st.title("🍽️ Local Food Donation Dashboard")
st.caption("Filter donations, view contacts, run analyses, and perform CRUD operations.")

# ---- SIDEBAR FILTERS ----
st.sidebar.header("Filters")

# Cities
cities_df = q('SELECT DISTINCT city FROM providers UNION SELECT DISTINCT location AS city FROM food_listings ORDER BY city;')
cities = cities_df["city"].dropna().unique().tolist()
city = st.sidebar.selectbox("City", ["(All)"] + cities)

# Providers
provider_names_df = q('SELECT DISTINCT name FROM providers ORDER BY name;')
provider_names = provider_names_df["name"].dropna().unique().tolist()
provider = st.sidebar.selectbox("Provider", ["(All)"] + provider_names)

# Food Types
food_types_df = q('SELECT DISTINCT food_type FROM food_listings ORDER BY food_type;')
food_types = food_types_df["food_type"].dropna().unique().tolist()
food_type = st.sidebar.selectbox("Food Type", ["(All)"] + food_types)

# Meal Types
meal_types_df = q('SELECT DISTINCT meal_type FROM food_listings ORDER BY meal_type;')
meal_types = meal_types_df["meal_type"].dropna().unique().tolist()
meal_type = st.sidebar.selectbox("Meal Type", ["(All)"] + meal_types)

# ---- FILTERED FOOD LISTINGS ----
def get_filtered_food_listings(city, provider, food_type, meal_type):
    sql = """
    SELECT fl.food_id, fl.food_name, fl.quantity, fl.expiry_date,
           fl.location AS city, fl.food_type, fl.meal_type,
           p.provider_id, p.name AS provider_name, p.contact AS provider_contact
    FROM food_listings fl
    JOIN providers p ON p.provider_id = fl.provider_id
    WHERE 1=1
    """
    params = {}
    if city != "(All)":
        sql += " AND fl.location = :city"
        params["city"] = city
    if provider != "(All)":
        sql += " AND p.name = :provider"
        params["provider"] = provider
    if food_type != "(All)":
        sql += " AND fl.food_type = :food_type"
        params["food_type"] = food_type
    if meal_type != "(All)":
        sql += " AND fl.meal_type = :meal_type"
        params["meal_type"] = meal_type
    sql += " ORDER BY fl.expiry_date ASC, fl.quantity DESC;"
    return q(sql, params)

listings = get_filtered_food_listings(city, provider, food_type, meal_type)
st.dataframe(listings, use_container_width=True)

# ---- CONTACT PROVIDERS ----
with st.expander("📇 Contact Providers in Current View"):
    if not listings.empty:
        contacts = listings[["provider_name", "provider_contact"]].drop_duplicates().reset_index(drop=True)
        st.dataframe(contacts, use_container_width=True)
    else:
        st.info("No providers found for the selected filters.")

# ---- SQL ANALYSIS QUERIES ----
st.subheader("📊 SQL Analyses")
query_map = {
    "Providers per city": 'SELECT city, COUNT(*) AS provider_count FROM providers GROUP BY city ORDER BY provider_count DESC;',
    "Receivers per city": 'SELECT city, COUNT(*) AS receiver_count FROM receivers GROUP BY city ORDER BY receiver_count DESC;',
    "Top provider type by quantity": 'SELECT provider_type, SUM(quantity) AS total_quantity FROM food_listings GROUP BY provider_type ORDER BY total_quantity DESC LIMIT 1;',
    "Provider contacts by city": 'SELECT name, contact FROM providers WHERE city = :city ORDER BY name;',
    "Top receiver by claims": 'SELECT r.receiver_id, r.name, COUNT(c.claim_id) AS total_claims FROM claims c JOIN receivers r ON c.receiver_id = r.receiver_id GROUP BY r.receiver_id, r.name ORDER BY total_claims DESC LIMIT 1;',
    "Total available quantity (not expired)": 'SELECT SUM(quantity) AS total_available FROM food_listings WHERE expiry_date >= CURRENT_DATE;',
    "City with most food listings": 'SELECT location AS city, COUNT(*) AS listings_count FROM food_listings GROUP BY location ORDER BY listings_count DESC LIMIT 1;',
    "Most common food types": 'SELECT food_type, COUNT(*) AS count_type FROM food_listings GROUP BY food_type ORDER BY count_type DESC;',
    "Claims per food item": 'SELECT f.food_id, f.food_name, COUNT(c.claim_id) AS claims_count FROM food_listings f LEFT JOIN claims c ON f.food_id = c.food_id GROUP BY f.food_id, f.food_name ORDER BY claims_count DESC;',
    "Top provider by successful claims": 'SELECT p.provider_id, p.name, COUNT(c.claim_id) AS successful_claims FROM claims c JOIN food_listings f ON c.food_id = f.food_id JOIN providers p ON f.provider_id = p.provider_id WHERE c.status = \'Completed\' GROUP BY p.provider_id, p.name ORDER BY successful_claims DESC LIMIT 1;',
    "Percentage of claim statuses": 'SELECT status, ROUND((COUNT(*) * 100.0)/(SELECT COUNT(*) FROM claims),2) AS percentage FROM claims GROUP BY status;',
    "Average quantity claimed per receiver": 'SELECT r.receiver_id, r.name, ROUND(AVG(f.quantity),2) AS avg_quantity FROM claims c JOIN food_listings f ON c.food_id = f.food_id JOIN receivers r ON c.receiver_id = r.receiver_id GROUP BY r.receiver_id, r.name ORDER BY avg_quantity DESC;',
    "Most claimed meal type": 'SELECT f.meal_type, COUNT(c.claim_id) AS claims_count FROM claims c JOIN food_listings f ON c.food_id = f.food_id GROUP BY f.meal_type ORDER BY claims_count DESC LIMIT 1;',
    "Total quantity donated by each provider": 'SELECT p.provider_id, p.name, SUM(f.quantity) AS total_donated FROM food_listings f JOIN providers p ON f.provider_id = p.provider_id GROUP BY p.provider_id, p.name ORDER BY total_donated DESC;',
    "Expired but unclaimed food items": 'SELECT f.food_id, f.food_name, f.expiry_date, f.quantity FROM food_listings f LEFT JOIN claims c ON f.food_id = c.food_id WHERE f.expiry_date < CURRENT_DATE AND c.claim_id IS NULL;'
}

chosen = st.selectbox("Choose an analysis", list(query_map.keys()))
if chosen == "Provider contacts by city":
    df = q(query_map[chosen], {"city": city if city != "(All)" else (cities[0] if cities else "")})
else:
    df = q(query_map[chosen])
st.dataframe(df, use_container_width=True)

# ---- CRUD OPERATIONS ----
st.subheader("🛠️ CRUD Operations")
tab1, tab2, tab3 = st.tabs(["Providers", "Food Listings", "Claims"])

# --- Providers CRUD ---
with tab1:
    st.markdown("**Create / Update Provider**")
    p_id = st.number_input("Provider ID", min_value=1, step=1, key="p_id")
    p_name = st.text_input("Name", key="p_name")
    p_type = st.selectbox("Type", ['Restaurant','Grocery Store','Supermarket','Bakery','Caterer','Other'], key="p_type")
    p_addr = st.text_input("Address", key="p_addr")
    p_city = st.text_input("City", key="p_city")
    p_contact = st.text_input("Contact", key="p_contact")
    if st.button("Save Provider", key="save_provider"):
        sql = """
        INSERT INTO providers (provider_id, name, type, address, city, contact)
        VALUES (:id,:name,:type,:address,:city,:contact)
        ON CONFLICT (provider_id) DO UPDATE SET
          name=EXCLUDED.name, type=EXCLUDED.type, address=EXCLUDED.address,
          city=EXCLUDED.city, contact=EXCLUDED.contact;
        """
        exec_write(sql, {"id": p_id, "name": p_name, "type": p_type, "address": p_addr, "city": p_city, "contact": p_contact})
        st.success("Provider saved.")

    del_id = st.number_input("Delete Provider ID", min_value=1, step=1, key="del_p_id")
    if st.button("Delete Provider", key="del_provider"):
        exec_write("DELETE FROM providers WHERE provider_id=:id;", {"id": del_id})
        st.warning("Provider deleted (and their listings cascaded).")

# --- Food Listings CRUD ---
with tab2:
    st.markdown("**Create / Update Listing**")
    f_id = st.number_input("Food ID", min_value=1, step=1, key="f_id")
    f_name = st.text_input("Food Name", key="f_name")
    f_qty = st.number_input("Quantity", min_value=0, step=1, key="f_qty")
    f_exp = st.date_input("Expiry Date", key="f_exp")
    f_pid = st.number_input("Provider ID (must exist)", min_value=1, step=1, key="f_pid")
    f_ptype = st.selectbox("Provider Type", ['Restaurant','Grocery Store','Supermarket','Bakery','Caterer','Other'], key="f_ptype")
    f_loc = st.text_input("Location (City)", key="f_loc")
    f_ftype = st.selectbox("Food Type", ['Vegetarian','Non-Vegetarian','Vegan','Other'], key="f_ftype")
    f_meal = st.selectbox("Meal Type", ['Breakfast','Lunch','Dinner','Snacks','Other'], key="f_meal")
    if st.button("Save Listing", key="save_listing"):
        sql = """
        INSERT INTO food_listings (food_id, food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type)
        VALUES (:id,:name,:qty,:exp,:pid,:ptype,:loc,:ftype,:meal)
        ON CONFLICT (food_id) DO UPDATE SET
          food_name=EXCLUDED.food_name, quantity=EXCLUDED.quantity, expiry_date=EXCLUDED.expiry_date,
          provider_id=EXCLUDED.provider_id, provider_type=EXCLUDED.provider_type, location=EXCLUDED.location,
          food_type=EXCLUDED.food_type, meal_type=EXCLUDED.meal_type;
        """
        exec_write(sql, {"id": f_id,"name": f_name,"qty": f_qty,"exp": f_exp,"pid": f_pid,"ptype": f_ptype,
                         "loc": f_loc,"ftype": f_ftype,"meal": f_meal})
        st.success("Listing saved.")

    up_food = st.number_input("Update Qty - Food ID", min_value=1, step=1, key="up_food")
    up_qty = st.number_input("New Quantity", min_value=0, step=1, key="up_qty")
    if st.button("Update Quantity", key="update_qty_btn"):
        exec_write("UPDATE food_listings SET quantity=:q WHERE food_id=:id;", {"q": up_qty, "id": up_food})
        st.info("Quantity updated.")

    del_food = st.number_input("Delete Listing - Food ID", min_value=1, step=1, key="del_food")
    if st.button("Delete Listing", key="del_listing_btn"):
        exec_write("DELETE FROM food_listings WHERE food_id=:id;", {"id": del_food})
        st.warning("Listing deleted.")

# --- Claims CRUD ---
with tab3:
    st.markdown("**Create / Update Claim**")
    c_id = st.number_input("Claim ID", min_value=1, step=1, key="c_id")
    c_food = st.number_input("Food ID", min_value=1, step=1, key="c_food")
    c_recv = st.number_input("Receiver ID", min_value=1, step=1, key="c_recv")
    c_status = st.selectbox("Status", ['Pending','Completed','Cancelled'], key="c_status")
    c_time = st.date_input("Timestamp", key="c_time")

    if st.button("Save Claim", key="save_claim"):
        sql = """
        INSERT INTO claims (claim_id, food_id, receiver_id, status, timestamp)
        VALUES (:id,:food,:recv,:status,:ts)
        ON CONFLICT (claim_id) DO UPDATE SET
          food_id=EXCLUDED.food_id, receiver_id=EXCLUDED.receiver_id,
          status=EXCLUDED.status, timestamp=EXCLUDED.timestamp;
        """
        exec_write(sql, {"id": c_id,"food": c_food,"recv": c_recv,"status": c_status,"ts": c_time})
        st.success("Claim saved.")

    del_claim = st.number_input("Delete Claim ID", min_value=1, step=1, key="del_claim")
    if st.button("Delete Claim", key="del_claim_btn"):
        exec_write("DELETE FROM claims WHERE claim_id=:id;", {"id": del_claim})
        st.warning("Claim deleted.")


