-- CREATING TABLE AND LOADING DATA

-- Providers Table
CREATE TABLE providers (
    Provider_ID INT PRIMARY KEY,
    Name TEXT,
    Type TEXT,
    Address TEXT,
    City TEXT,
    Contact TEXT
);

COPY providers(Provider_ID,Name,Type,Address,City,Contact)
FROM 'D:\DOCUMENTS\DATA ANALYTICS PROJECTS\Local Food Wastage Management System Project\clean datasets\providers_clean_dataset.csv'
DELIMITER ',' CSV HEADER;

-- Receivers Table
CREATE TABLE receivers (
    Receiver_ID INT PRIMARY KEY,
    Name TEXT,
    Type TEXT,
    City TEXT,
    Contact TEXT
);

COPY receivers(Receiver_ID,Name,Type,City,Contact)
FROM 'D:\DOCUMENTS\DATA ANALYTICS PROJECTS\Local Food Wastage Management System Project\clean datasets\receivers_clean_dataset.csv'
DELIMITER ',' CSV HEADER;

-- Food_Listing Table
CREATE TABLE food_listings (
    Food_ID INT PRIMARY KEY,
    Food_Name TEXT,
    Quantity INT,
    Expiry_Date DATE,
    Provider_ID INT REFERENCES providers(Provider_ID),
    Provider_Type TEXT,
    Location TEXT,
    Food_Type TEXT,
    Meal_Type TEXT
);

COPY food_listings(Food_ID,Food_Name,Quantity,Expiry_Date,Provider_ID,Provider_Type,Location,Food_Type,Meal_Type)
FROM 'D:\DOCUMENTS\DATA ANALYTICS PROJECTS\Local Food Wastage Management System Project\clean datasets\food_listing_clean_dataset.csv'
DELIMITER ',' CSV HEADER;

-- Claims Table
CREATE TABLE claims (
    Claim_ID INT PRIMARY KEY,
    Food_ID INT REFERENCES food_listings(Food_ID),
    Receiver_ID INT REFERENCES receivers(Receiver_ID),
    Status TEXT,
    Timestamp TIMESTAMP
);

COPY claims(Claim_ID,Food_ID,Receiver_ID,Status,Timestamp)
FROM 'D:\DOCUMENTS\DATA ANALYTICS PROJECTS\Local Food Wastage Management System Project\clean datasets\claims_clean_dataset.csv'
DELIMITER ',' CSV HEADER;


-- CRUD OPERATIONS

-- Create
INSERT INTO providers(Provider_ID,Name,Type,Address,City,Contact)
VALUES (1001, 'Test Store', 'Grocery Store', '123 Test St', 'TestCity', '+11234567890')

-- Read
SELECT * FROM providers;

-- Update
UPDATE providers SET City = 'UpdatedCity' WHERE Provider_ID = 1001

-- Delete
DELETE FROM providers WHERE Provider_ID = 1001;

-- Check row counts
select count(*) from providers;
select count(*) from receivers;
select count(*) from food_listings;
select count(*) from claims;


--- ADVANCE QUERYING 

-- Number of providers per city
SELECT City, COUNT(*) AS provider_count
FROM providers
GROUP BY City
ORDER BY provider_count DESC;

-- Number of receivers per city
SELECT City, COUNT(*) AS receiver_count
FROM receivers
GROUP BY City
ORDER BY receiver_count DESC;

-- Provider type contributing the most food
SELECT Provider_Type, SUM(Quantity) AS total_quantity
FROM food_listings
GROUP BY Provider_Type
ORDER BY total_quantity DESC
LIMIT 1;

-- Contact info of all providers in a specific city
SELECT Name, Contact
FROM providers
WHERE City = 'New Jessica';  -- Change city name as needed

-- Receiver who claimed the most items
SELECT r.Receiver_ID, r.Name, COUNT(c.Claim_ID) AS total_claims
FROM claims c
JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
GROUP BY r.Receiver_ID, r.Name
ORDER BY total_claims DESC
LIMIT 1;

-- Total quantity currently available (not expired)
SELECT SUM(Quantity) AS total_available
FROM food_listings
WHERE Expiry_Date >= CURRENT_DATE;

-- City with the highest number of food listings
SELECT Location AS City, COUNT(*) AS listings_count
FROM food_listings
GROUP BY Location
ORDER BY listings_count DESC
LIMIT 1;

-- Most common food types
SELECT Food_Type, COUNT(*) AS count_type
FROM food_listings
GROUP BY Food_Type
ORDER BY count_type DESC;

-- Claims per food item
SELECT f.Food_ID, f.Food_Name, COUNT(c.Claim_ID) AS claims_count
FROM food_listings f
LEFT JOIN claims c ON f.Food_ID = c.Food_ID
GROUP BY f.Food_ID, f.Food_Name
ORDER BY claims_count DESC;

-- Provider with highest successful claims
SELECT p.Provider_ID, p.Name, COUNT(c.Claim_ID) AS successful_claims
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
JOIN providers p ON f.Provider_ID = p.Provider_ID
WHERE c.Status = 'Completed'
GROUP BY p.Provider_ID, p.Name
ORDER BY successful_claims DESC
LIMIT 1;

-- Percentage of claim statuses
SELECT Status,
       ROUND( (COUNT(*) * 100.0) / (SELECT COUNT(*) FROM claims), 2) AS percentage
FROM claims
GROUP BY Status;

-- Average quantity claimed per receiver
SELECT r.Receiver_ID, r.Name, ROUND(AVG(f.Quantity), 2) AS avg_quantity
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
GROUP BY r.Receiver_ID, r.Name
ORDER BY avg_quantity DESC;

-- Most claimed meal type
SELECT f.Meal_Type, COUNT(c.Claim_ID) AS claims_count
FROM claims c
JOIN food_listings f ON c.Food_ID = f.Food_ID
GROUP BY f.Meal_Type
ORDER BY claims_count DESC
LIMIT 1;

-- Total quantity donated by each provider
SELECT p.Provider_ID, p.Name, SUM(f.Quantity) AS total_donated
FROM food_listings f
JOIN providers p ON f.Provider_ID = p.Provider_ID
GROUP BY p.Provider_ID, p.Name
ORDER BY total_donated DESC;

-- Expired but unclaimed food items
SELECT f.Food_ID, f.Food_Name, f.Expiry_Date, f.Quantity
FROM food_listings f
LEFT JOIN claims c ON f.Food_ID = c.Food_ID
WHERE f.Expiry_Date < CURRENT_DATE
  AND c.Claim_ID IS NULL;

