import os
import pandas as pd

CSV_PATH = "emission_factors.csv"

# Standard annual benchmark averages (in kg CO2e per person)
GLOBAL_AVERAGE_ANNUAL_KG = 4700.0
NATIONAL_AVERAGE_ANNUAL_KG = 1900.0  # India per capita average (~1.9 tonnes)


def load_emission_factors():
    """
    Reads emission factors from emission_factors.csv.
    Returns a dictionary mapping (category, subcategory) -> factor.
    """
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Dataset file '{CSV_PATH}' was not found.")

    df = pd.read_csv(CSV_PATH)
    
    factors = {}
    for _, row in df.iterrows():
        key = (row["category"].strip(), row["subcategory"].strip())
        factors[key] = float(row["emission_factor_kg_co2e"])
        
    return factors


def calculate_emissions(car_km, bus_km, train_km, flight_km_yr, electricity_kwh, diet_type, waste_kg, water_liters):
    """
    Calculates monthly, yearly, and daily CO2 emissions (in kg CO2e).
    Inputs:
    - car_km, bus_km, train_km: Monthly distance in km
    - flight_km_yr: Annual flight distance in km
    - electricity_kwh: Monthly electricity consumption
    - diet_type: Diet category name string
    - waste_kg: Weekly household waste in kg
    - water_liters: Daily water usage in liters
    """
    factors = load_emission_factors()

    # 1. Transportation (Monthly)
    car_ef = factors.get(("Transportation", "Car (Petrol/Diesel)"), 0.170)
    bus_ef = factors.get(("Transportation", "Bus (City)"), 0.089)
    train_ef = factors.get(("Transportation", "Train / Metro)"), 0.035)
    flight_ef = factors.get(("Transportation", "Flight"), 0.255)

    transport_monthly = (car_km * car_ef) + \
                        (bus_km * bus_ef) + \
                        (train_km * train_ef) + \
                        ((flight_km_yr / 12.0) * flight_ef)

    # 2. Electricity (Monthly)
    elec_ef = factors.get(("Electricity", "Grid Electricity"), 0.850)
    electricity_monthly = electricity_kwh * elec_ef

    # 3. Food & Diet (30 days/month)
    diet_ef = factors.get(("Diet", diet_type), 2.700)
    diet_monthly = diet_ef * 30.0

    # 4. Household Waste (Weekly to Monthly conversion factor ~ 4.33 weeks)
    waste_ef = factors.get(("Waste", "Household Waste"), 0.450)
    waste_monthly = (waste_kg * 4.33) * waste_ef

    # 5. Water Usage (Daily to Monthly conversion ~ 30 days)
    water_ef = factors.get(("Water", "Municipal Water Supply"), 0.030)
    water_monthly = (water_liters * 30.0 / 100.0) * water_ef

    # Total Calculations
    total_monthly = transport_monthly + electricity_monthly + diet_monthly + waste_monthly + water_monthly
    total_yearly = total_monthly * 12.0
    total_daily = total_monthly / 30.0

    breakdown = {
        "Transportation": round(transport_monthly, 2),
        "Electricity": round(electricity_monthly, 2),
        "Food & Diet": round(diet_monthly, 2),
        "Household Waste": round(waste_monthly, 2),
        "Water Usage": round(water_monthly, 2)
    }

    return {
        "daily_kg": round(total_daily, 2),
        "monthly_kg": round(total_monthly, 2),
        "yearly_kg": round(total_yearly, 2),
        "breakdown": breakdown
    }


def generate_recommendations(breakdown):
    """
    Generates actionable advice based on emission hotspots.
    """
    recommendations = []

    if breakdown["Transportation"] > 100:
        recommendations.append("🚲 **Transportation**: Consider switching to public transit, carpooling, or electric vehicles for daily travel.")
    if breakdown["Electricity"] > 150:
        recommendations.append("💡 **Electricity**: Switch to energy-star rated appliances, LED bulbs, and consider rooftop solar panels.")
    if breakdown["Food & Diet"] > 100:
        recommendations.append("🥗 **Food & Diet**: Replacing 2–3 meat-heavy meals weekly with plant-based options significantly lowers food emissions.")
    if breakdown["Household Waste"] > 20:
        recommendations.append("♻️ **Household Waste**: Compost organic waste and minimize single-use plastic packaging.")
    if breakdown["Water Usage"] > 5:
        recommendations.append("💧 **Water Usage**: Install low-flow aerators on taps and optimize hot water heating cycles.")

    if not recommendations:
        recommendations.append("🌟 **Outstanding!** Your calculated carbon footprint is below high-emission thresholds across all categories.")

    return recommendations
