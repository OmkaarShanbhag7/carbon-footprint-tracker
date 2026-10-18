import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from calculations import (
    calculate_emissions,
    generate_recommendations,
    GLOBAL_AVERAGE_ANNUAL_KG,
    NATIONAL_AVERAGE_ANNUAL_KG
)
from database import (
    init_db,
    register_user,
    verify_user,
    save_record,
    get_history
)

# Page configuration
st.set_page_config(
    page_title="Carbon Footprint Calculator & Dashboard",
    page_icon="🌱",
    layout="wide"
)

# Initialize Database
init_db()

# Initialize Session State
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# --------------------------
# AUTHENTICATION SCREEN
# --------------------------
if not st.session_state["logged_in"]:
    st.title("🌱 Carbon Footprint Calculator & Dashboard")
    st.subheader("Welcome! Please log in or create an account to start tracking.")

    auth_tab1, auth_tab2 = st.tabs(["🔒 Login", "📝 Create Account"])

    with auth_tab1:
        st.markdown("### User Login")
        login_user = st.text_input("Username", key="login_user")
        login_pwd = st.text_input("Password", type="password", key="login_pwd")
        
        if st.button("Log In", type="primary"):
            if login_user and login_pwd:
                if verify_user(login_user, login_pwd):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = login_user
                    st.success(f"Welcome back, {login_user}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            else:
                st.warning("Please enter both username and password.")

    with auth_tab2:
        st.markdown("### Register New Account")
        reg_user = st.text_input("Choose Username", key="reg_user")
        reg_pwd = st.text_input("Choose Password", type="password", key="reg_pwd")
        reg_pwd_confirm = st.text_input("Confirm Password", type="password", key="reg_pwd_confirm")

        if st.button("Create Account"):
            if reg_user and reg_pwd:
                if reg_pwd != reg_pwd_confirm:
                    st.error("Passwords do not match!")
                else:
                    success, message = register_user(reg_user, reg_pwd)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            else:
                st.warning("Please fill out all registration fields.")

# --------------------------
# MAIN DASHBOARD (LOGGED IN)
# --------------------------
else:
    # Sidebar - User Info & Logout
    st.sidebar.markdown(f"### 👤 Logged in as: **{st.session_state['username']}**")
    if st.sidebar.button("Log Out"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

    st.title("🌱 Carbon Footprint Calculator & Dashboard")
    st.markdown(f"Welcome **{st.session_state['username']}**! Estimate your carbon footprint, visualize category breakdowns, compare with benchmarks, and track your history over time.")

    # Sidebar - Input Controls
    st.sidebar.header("📥 Input Your Lifestyle Data")

    st.sidebar.subheader("🚗 Transportation")
    car_km = st.sidebar.number_input("Car Travel (km/month)", min_value=0.0, value=150.0, step=10.0)
    bus_km = st.sidebar.number_input("Bus Travel (km/month)", min_value=0.0, value=50.0, step=5.0)
    train_km = st.sidebar.number_input("Train/Metro Travel (km/month)", min_value=0.0, value=100.0, step=10.0)
    flight_km_yr = st.sidebar.number_input("Flights (km/year)", min_value=0.0, value=1000.0, step=100.0)

    st.sidebar.subheader("💡 Electricity")
    electricity_kwh = st.sidebar.number_input("Electricity Consumption (kWh/month)", min_value=0.0, value=200.0, step=10.0)

    st.sidebar.subheader("🥗 Food Habits")
    diet_type = st.sidebar.selectbox(
        "Diet Type",
        ["Meat Heavy", "Medium Meat", "Pescatarian / Low Meat", "Vegetarian", "Vegan"],
        index=3
    )

    st.sidebar.subheader("♻️ Household Waste")
    waste_kg = st.sidebar.number_input("Waste Generated (kg/week)", min_value=0.0, value=10.0, step=1.0)

    st.sidebar.subheader("💧 Water Usage")
    water_liters = st.sidebar.number_input("Water Usage (Liters/day)", min_value=0.0, value=150.0, step=10.0)

    calculate_btn = st.sidebar.button("Calculate & Save Footprint", type="primary")

    # Main Tabs
    tab1, tab2 = st.tabs(["📊 Footprint Dashboard", "📜 My Personal History"])

    with tab1:
        results = calculate_emissions(
            car_km=car_km,
            bus_km=bus_km,
            train_km=train_km,
            flight_km_yr=flight_km_yr,
            electricity_kwh=electricity_kwh,
            diet_type=diet_type,
            waste_kg=waste_kg,
            water_liters=water_liters
        )

        if calculate_btn:
            save_record(st.session_state["username"], results)
            st.success("Results saved to your personal history log!")

        # Metric Cards
        col1, col2, col3 = st.columns(3)
        col1.metric("Daily CO₂ Emissions", f"{results['daily_kg']} kg")
        col2.metric("Monthly CO₂ Emissions", f"{results['monthly_kg']} kg")
        col3.metric("Yearly CO₂ Emissions", f"{results['yearly_kg']} kg")

        st.divider()

        # Visualizations
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.subheader("Emissions Breakdown by Category")
            breakdown = results["breakdown"]
            categories = [k for k, v in breakdown.items() if v > 0]
            values = [v for k, v in breakdown.items() if v > 0]

            if sum(values) > 0:
                fig1, ax1 = plt.subplots(figsize=(6, 5))
                colors = ["#2ecc71", "#3498db", "#e67e22", "#9b59b6", "#1abc9c"]
                wedges, texts, autotexts = ax1.pie(
                    values,
                    labels=categories,
                    autopct="%1.1f%%",
                    startangle=140,
                    colors=colors[:len(categories)],
                    wedgeprops=dict(width=0.4, edgecolor='white')
                )
                plt.setp(autotexts, size=10, weight="bold")
                ax1.set_title("Monthly Breakdown (kg CO₂e)", fontsize=12, pad=15)
                st.pyplot(fig1)
                plt.close(fig1)
            else:
                st.info("No emissions data to display.")

        with chart_col2:
            st.subheader("Annual Benchmark Comparison")
            user_yearly = results["yearly_kg"]
            
            benchmarks = {
                "Your Footprint": user_yearly,
                "National Avg (India)": NATIONAL_AVERAGE_ANNUAL_KG,
                "Global Avg": GLOBAL_AVERAGE_ANNUAL_KG
            }

            fig2, ax2 = plt.subplots(figsize=(6, 5))
            bar_colors = ["#e74c3c" if user_yearly > NATIONAL_AVERAGE_ANNUAL_KG else "#2ecc71", "#3498db", "#95a5a6"]
            bars = ax2.bar(benchmarks.keys(), benchmarks.values(), color=bar_colors, width=0.5)
            
            ax2.set_ylabel("Annual CO₂e (kg)", fontsize=11)
            ax2.set_title("Annual Footprint vs. Benchmarks", fontsize=12, pad=15)
            
            for bar in bars:
                yval = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2.0, yval + (max(benchmarks.values()) * 0.02), f"{yval:,.0f} kg", ha='center', va='bottom', fontweight='bold')

            ax2.set_ylim(0, max(benchmarks.values()) * 1.2)
            st.pyplot(fig2)
            plt.close(fig2)

        st.divider()

        # Recommendations
        st.subheader("💡 Personalized Recommendations")
        recommendations = generate_recommendations(breakdown)
        for rec in recommendations:
            st.markdown(f"- {rec}")

    with tab2:
        st.subheader(f"📜 Personal Calculation Logs for {st.session_state['username']}")
        history_data = get_history(st.session_state["username"])

        if history_data:
            columns = [
                "Timestamp", "Daily (kg)", "Monthly (kg)", "Yearly (kg)",
                "Transport (kg)", "Electricity (kg)", "Food (kg)", "Waste (kg)", "Water (kg)"
            ]
            df_history = pd.DataFrame(history_data, columns=columns)
            
            st.dataframe(df_history, use_container_width=True)

            if len(df_history) > 1:
                st.subheader("📈 Carbon Emissions Progress Over Time")
                df_history_sorted = df_history.sort_values(by="Timestamp")
                
                fig3, ax3 = plt.subplots(figsize=(10, 4))
                ax3.plot(df_history_sorted["Timestamp"], df_history_sorted["Monthly (kg)"], marker='o', color="#27ae60", linewidth=2, label="Monthly CO₂e (kg)")
                ax3.set_xlabel("Date/Time")
                ax3.set_ylabel("Monthly Emissions (kg CO₂e)")
                ax3.set_title("Emission Trend", fontsize=12)
                plt.xticks(rotation=45)
                ax3.grid(True, linestyle="--", alpha=0.6)
                st.pyplot(fig3)
                plt.close(fig3)
        else:
            st.info("No calculation history recorded yet for your account. Use the sidebar to calculate and save your first log!")
