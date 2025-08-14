# app.py
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# ---- PAGE CONFIG ----
st.set_page_config(page_title="Local Food Donation Dashboard", layout="wide")

# ---- LOAD ENV VARIABLES ----
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

# ---- DB CONNECTION ----
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


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

# ---- PAGE TITLE ----
st.title("🍽️ Local Food Donation Dashboard")
st.caption("Filter donations, view contacts, run analyses, and perform CRUD operations.")

# ---- SIDEBAR FILTERS ----
st.sidebar.header("Filters")

cities_df = q("SELECT DISTINCT city FROM providers UNION SELECT DISTINCT location AS city FROM food_listings ORDER BY city;")
cities = cities_df["city"].dropna().unique().tolist()
city = st.sidebar.selectbox("City", ["(All)"] + cities)

provider_names_df = q("SELECT DISTINCT name FROM providers ORDER BY name;")
provider_names = provider_names_df["name"].dropna().unique().tolist()
provider = st.sidebar.selectbox("Provider", ["(All)"] + provider_names)

food_types_df = q("SELECT DISTINCT food_type FROM food_listings ORDER BY food_type;")
food_types = food_types_df["food_type"].dropna().unique().tolist()
food_type = st.sidebar.selectbox("Food Type", ["(All)"] + food_types)

meal_types_df = q("SELECT DISTINCT meal_type FROM food_listings ORDER BY meal_type;")
meal_types = meal_types_df["meal_type"].dropna().unique().tolist()
meal_type = st.sidebar.selectbox("Meal Type", ["(All)"] + meal_types)

# ---- FILTERED FOOD LISTINGS ----
st.subheader("Available Food Listings")

def get_filtered_food_listings(city, provider, food_type, meal_type):
    sql = """
    SELECT fl.food_id, fl.food_name, fl.quantity, fl.expiry_date,
           fl.location AS city, fl.food_type, fl.meal_type,
           p.provider_id, p.name AS provider_name, p.contact AS provider_contact
    FROM food_listings fl
    JOIN providers p ON p.provider_id = fl.provider_id
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
    "Providers per city": "SELECT City, COUNT(*) AS provider_count FROM providers GROUP BY City ORDER BY provider_count DESC;",
    "Receivers per city": "SELECT City, COUNT(*) AS receiver_count FROM receivers GROUP BY City ORDER BY receiver_count DESC;",
    "Top provider type by quantity": "SELECT Provider_Type, SUM(Quantity) AS total_quantity FROM food_listings GROUP BY Provider_Type ORDER BY total_quantity DESC LIMIT 1;",
    "Provider contacts by city": "SELECT Name, Contact FROM providers WHERE City = :city ORDER BY Name;",
    "Top receiver by claims": "SELECT r.Receiver_ID, r.Name, COUNT(c.Claim_ID) AS total_claims FROM claims c JOIN receivers r ON c.Receiver_ID = r.Receiver_ID GROUP BY r.Receiver_ID, r.Name ORDER BY total_claims DESC LIMIT 1;",
    "Total available quantity (not expired)": "SELECT SUM(Quantity) AS total_available FROM food_listings WHERE Expiry_Date >= CURRENT_DATE;",
    "City with most food listings": "SELECT Location AS City, COUNT(*) AS listings_count FROM food_listings GROUP BY Location ORDER BY listings_count DESC LIMIT 1;",
    "Most common food types": "SELECT Food_Type, COUNT(*) AS count_type FROM food_listings GROUP BY Food_Type ORDER BY count_type DESC;",
    "Claims per food item": "SELECT f.Food_ID, f.Food_Name, COUNT(c.Claim_ID) AS claims_count FROM food_listings f LEFT JOIN claims c ON f.Food_ID = c.Food_ID GROUP BY f.Food_ID, f.Food_Name ORDER BY claims_count DESC;",
    "Top provider by successful claims": "SELECT p.Provider_ID, p.Name, COUNT(c.Claim_ID) AS successful_claims FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID JOIN providers p ON f.Provider_ID = p.Provider_ID WHERE c.Status = 'Completed' GROUP BY p.Provider_ID, p.Name ORDER BY successful_claims DESC LIMIT 1;",
    "Percentage of claim statuses": "SELECT Status, ROUND((COUNT(*) * 100.0)/(SELECT COUNT(*) FROM claims),2) AS percentage FROM claims GROUP BY Status;",
    "Average quantity claimed per receiver": "SELECT r.Receiver_ID, r.Name, ROUND(AVG(f.Quantity),2) AS avg_quantity FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID JOIN receivers r ON c.Receiver_ID = r.Receiver_ID GROUP BY r.Receiver_ID, r.Name ORDER BY avg_quantity DESC;",
    "Most claimed meal type": "SELECT f.Meal_Type, COUNT(c.Claim_ID) AS claims_count FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID GROUP BY f.Meal_Type ORDER BY claims_count DESC LIMIT 1;",
    "Total quantity donated by each provider": "SELECT p.Provider_ID, p.Name, SUM(f.Quantity) AS total_donated FROM food_listings f JOIN providers p ON f.Provider_ID = p.Provider_ID GROUP BY p.Provider_ID, p.Name ORDER BY total_donated DESC;",
    "Expired but unclaimed food items": "SELECT f.Food_ID, f.Food_Name, f.Expiry_Date, f.Quantity FROM food_listings f LEFT JOIN claims c ON f.Food_ID = c.Food_ID WHERE f.Expiry_Date < CURRENT_DATE AND c.Claim_ID IS NULL;"
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
        INSERT INTO providers (provider_id,name,type,address,city,contact)
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
        INSERT INTO food_listings (food_id,food_name,quantity,expiry_date,provider_id,provider_type,location,food_type,meal_type)
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
    c_time = st.date_input("Timestamp", key="c_time")  # date_input used instead of datetime_input

    if st.button("Save Claim", key="save_claim"):
        sql = """
        INSERT INTO claims (claim_id,food_id,receiver_id,status,"timestamp")
        VALUES (:id,:food,:recv,:status,:ts)
        ON CONFLICT (claim_id) DO UPDATE SET
          food_id=EXCLUDED.food_id, receiver_id=EXCLUDED.receiver_id,
          status=EXCLUDED.status, "timestamp"=EXCLUDED."timestamp";
        """
        exec_write(sql, {"id": c_id,"food": c_food,"recv": c_recv,"status": c_status,"ts": c_time})
        st.success("Claim saved.")

    del_claim = st.number_input("Delete Claim ID", min_value=1, step=1, key="del_claim")
    if st.button("Delete Claim", key="del_claim_btn"):
        exec_write("DELETE FROM claims WHERE claim_id=:id;", {"id": del_claim})
        st.warning("Claim deleted.")
