import streamlit as st
import pandas as pd
import numpy as np
import fastf1 as ff1
import matplotlib.pyplot as plt
import os

CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
ff1.Cache.enable_cache(CACHE_DIR)

# --- Model Functions ---

@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_data(year, race, session_code):
    """Loads and processes lap data for a given F1 session."""
    try:
        ff1.Cache.enable_cache('cache') 
        session = ff1.get_session(year, race, session_code)
        session.load(telemetry=False, weather=False)
        laps = session.laps
        return laps
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def calculate_degradation(laps, driver, compound, fuel_effect_per_lap=0.04):
    """Calculates tyre degradation, including fuel correction and outlier removal."""
    stint_laps = laps.pick_driver(driver).loc[laps['Compound'] == compound].copy()
    stint_laps = stint_laps.loc[stint_laps['PitInTime'].isnull() & stint_laps['PitOutTime'].isnull()].copy()
    
    if len(stint_laps) < 10:
        return None
    
    stint_laps['LapTimeSeconds'] = stint_laps['LapTime'].dt.total_seconds()
    median_lap_time = stint_laps['LapTimeSeconds'].median()
    stint_laps = stint_laps.loc[stint_laps['LapTimeSeconds'] < median_lap_time * 1.07].copy()
    
    if len(stint_laps) < 10:
        return None
    
    fuel_correction = stint_laps['LapNumber'] * fuel_effect_per_lap
    stint_laps['CorrectedLapTime'] = stint_laps['LapTimeSeconds'] + fuel_correction
    
    x = stint_laps['TyreLife']
    y = stint_laps['CorrectedLapTime']
    coeffs = np.polyfit(x, y, 1)
    
    return coeffs[0]

def simulate_stint(start_lap, stint_length, compound, degradation_summary, base_lap_time, fuel_effect_per_lap):
    """Calculates the total time for a single race stint."""
    #Check if  the compound exists in degradation data

    if compound not in degradation_summary['Compound'].values:
        return 999999
    
    #Get degradation rate for chosen compond
    degradation_rate = degradation_summary.loc[degradation_summary['Compound'] == compound, 'Degradation'].iloc[0]
    total_stint_time = 0
    for i in range(stint_length):
        current_lap_in_race = start_lap + i
        current_tyre_life = i + 1
        tyre_effect = current_tyre_life * degradation_rate
        fuel_effect = current_lap_in_race * fuel_effect_per_lap
        predicted_lap_time = base_lap_time + tyre_effect - fuel_effect
        total_stint_time += predicted_lap_time
    return total_stint_time

def simulate_strategy(strategy, degradation_summary, base_lap_time, fuel_effect_per_lap, pit_stop_time_loss):
    """Calculates the total race time for a given strategy."""
    total_race_time = 0
    start_lap = 1
    for stint in strategy:
        stint_time = simulate_stint(start_lap, stint['StintLength'], stint['Compound'], degradation_summary, base_lap_time, fuel_effect_per_lap)
        total_race_time += stint_time
        start_lap += stint['StintLength']
    num_pit_stops = len(strategy) - 1
    total_race_time += (num_pit_stops * pit_stop_time_loss)
    return total_race_time

def find_best_one_stop(compounds, total_laps, degradation_summary, base_lap_time, fuel_effect_per_lap, pit_stop_time_loss):
    """Finds the optimal one-stop strategy."""
    pit_window_start = 12
    pit_window_end = 35
    results = []
    for pit_lap in range(pit_window_start, pit_window_end + 1):
        strategy = [
            {'Compound': compounds[0], 'StintLength': pit_lap},
            {'Compound': compounds[1], 'StintLength': total_laps - pit_lap}
        ]
        total_time = simulate_strategy(strategy, degradation_summary, base_lap_time, fuel_effect_per_lap, pit_stop_time_loss)
        
        # Standardize the output dictionary
        results.append({
            'Strategy': f"{compounds[0]}-{compounds[1]}",
            'Total Time (s)': total_time,
            'Pit Lap 1': pit_lap,
            'Pit Lap 2': None  # Add a placeholder for the second stop
        })
        
    if not results: return None
    results_df = pd.DataFrame(results)
    return results_df.loc[results_df['Total Time (s)'].idxmin()]

def find_best_two_stop(compounds, total_laps, degradation_summary, base_lap_time, fuel_effect_per_lap, pit_stop_time_loss):
    """Finds the optimal two-stop strategy."""
    pit_window_1_start, pit_window_1_end = 10, 25
    min_stint_length = 8
    results = []
    for pit_lap_1 in range(pit_window_1_start, pit_window_1_end + 1):
        pit_window_2_start = pit_lap_1 + min_stint_length
        pit_window_2_end = total_laps - min_stint_length
        for pit_lap_2 in range(pit_window_2_start, pit_window_2_end + 1):
            strategy = [
                {'Compound': compounds[0], 'StintLength': pit_lap_1},
                {'Compound': compounds[1], 'StintLength': pit_lap_2 - pit_lap_1},
                {'Compound': compounds[2], 'StintLength': total_laps - pit_lap_2}
            ]
            total_time = simulate_strategy(strategy, degradation_summary, base_lap_time, fuel_effect_per_lap, pit_stop_time_loss)
            
            # Standardize the output dictionary
            results.append({
                'Strategy': f"{compounds[0]}-{compounds[1]}-{compounds[2]}",
                'Total Time (s)': total_time,
                'Pit Lap 1': pit_lap_1,
                'Pit Lap 2': pit_lap_2
            })

    if not results: return None
    results_df = pd.DataFrame(results)
    return results_df.loc[results_df['Total Time (s)'].idxmin()]

# --- Streamlit App ---

st.title("F1 Race Strategy Predictor")

# --- Initialize Session State ---
# This ensures our variables persist across reruns
if 'analysis_run' not in st.session_state:
    st.session_state.analysis_run = False
if 'laps_data' not in st.session_state:
    st.session_state.laps_data = None


# --- Sidebar for user inputs ---
st.sidebar.header("Race Parameters")
year = st.sidebar.number_input("Year", value=2023, min_value=2018)
race = st.sidebar.text_input("Race Name", value="Bahrain")
session_type = st.sidebar.selectbox("Select Session to Analyze:", options=['Race', 'FP1', 'FP2', 'FP3', 'Qualifying'])

# Handle text inputs with proper type conversion and error checking
try:
    total_laps_str = st.sidebar.text_input("Total Laps", value="57")
    total_laps = int(total_laps_str)
except ValueError:
    st.sidebar.error("Please enter a valid integer for Total Laps.")
    total_laps = 57 # Fallback to default

try:
    pit_stop_loss_str = st.sidebar.text_input("Pit Stop Time Loss (s)", value="22.0")
    pit_stop_loss = float(pit_stop_loss_str)
except ValueError:
    st.sidebar.error("Please enter a valid number for Pit Stop Time Loss.")
    pit_stop_loss = 22.0 # Fallback to default

try:
    base_lap_time_str = st.sidebar.text_input("Base Lap Time (s)", value="99.5")
    base_lap_time = float(base_lap_time_str)
except ValueError:
    st.sidebar.error("Please enter a valid number for Base Lap Time.")
    base_lap_time = 99.5 # Fallback to default

fuel_effect = st.sidebar.number_input("Fuel Effect (s/lap)", value=0.04, format="%.3f")

# Map user-friendly session names to the codes fastf1 expects
session_mapping = {
    'Race': 'R',
    'FP1': 'FP1',
    'FP2': 'FP2',
    'FP3': 'FP3',
    'Qualifying': 'Q'
}
session_code = session_mapping[session_type]

# --- Button to Trigger Analysis ---
if st.button("Press here to Analyze Race and Predict Strategy"):
    with st.spinner("Loading session data and running analysis..."):
        st.session_state.laps_data = load_data(year, race, session_code)
        st.session_state.analysis_run = True # Set the flag to True

# --- Display Results ---
# This block checks the flag. If True, it displays all results.
# This section will now remain visible during reruns caused by other widgets.
if st.session_state.analysis_run:
    laps_data = st.session_state.laps_data

    if laps_data is not None and not laps_data.empty:
        st.header(f"Analysis for {year} {race} GP ({session_type})")

        # --- Degradation and Strategy Prediction ---
        drivers = laps_data['Driver'].unique()
        compounds = laps_data['Compound'].unique()
        reliable_stints = []
        for driver in drivers:
            for compound in compounds:
                degradation = calculate_degradation(laps_data, driver, compound, fuel_effect)
                if degradation is not None:
                    reliable_stints.append({'Driver': driver, 'Compound': compound, 'Degradation': degradation})
        
        if not reliable_stints:
            st.warning("Could not calculate degradation. Not enough reliable stint data found for this session.")
        else:
            reliable_summary = pd.DataFrame(reliable_stints)
            final_degradation_summary = reliable_summary.groupby('Compound')['Degradation'].mean().reset_index()

            st.subheader("Tyre Degradation Model")
            st.dataframe(final_degradation_summary.sort_values(by='Degradation'))

            
            st.header("Optimal Strategy Prediction")

            # --- Generate All Possible Strategy Combinations ---
            
            # Define the available tyre compounds for the race
            compounds = ['SOFT', 'MEDIUM', 'HARD']
            
            # Generate all valid one-stop strategies (using two different compounds)
            one_stop_combinations = [
                (c1, c2) for c1 in compounds for c2 in compounds if c1 != c2
            ]

            # Generate all valid two-stop strategies (must use at least two different compounds)
            two_stop_combinations = [
                (c1, c2, c3) for c1 in compounds for c2 in compounds for c3 in compounds
                if len(set([c1, c2, c3])) >= 2
            ]

            # --- Simulate and Collect Strategy Results ---

            # Simulate all one-stop strategies
            one_stop_strategies = [
                find_best_one_stop(
                    list(combo), total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss
                ) for combo in one_stop_combinations
            ]
            
            # Simulate all two-stop strategies
            two_stop_strategies = [
                find_best_two_stop(
                    list(combo), total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss
                ) for combo in two_stop_combinations
            ]
            
            all_results = pd.DataFrame([s for s in one_stop_strategies + two_stop_strategies if s is not None])

            if not all_results.empty:
                overall_best = all_results.loc[all_results['Total Time (s)'].idxmin()]
                st.subheader("Comparison of Top Strategies")
                st.dataframe(all_results.sort_values(by='Total Time (s)'))

                optimal_strategy_name = np.atleast_1d(overall_best['Strategy'])[0]
                optimal_pit_lap_1 = int(np.atleast_1d(overall_best['Pit Lap 1'])[0])
                optimal_pit_lap_2 = np.atleast_1d(overall_best['Pit Lap 2'])[0]
                optimal_time_seconds = float(np.atleast_1d(overall_best['Total Time (s)'])[0])

                if pd.isna(optimal_pit_lap_2):
                    optimal_pit_laps_str = str(optimal_pit_lap_1)
                else:
                    optimal_pit_lap_2 = int(optimal_pit_lap_2)
                    optimal_pit_laps_str = f"{optimal_pit_lap_1}, {optimal_pit_lap_2}"
                
                st.success(f"**Optimal Strategy Found:** A **{optimal_strategy_name}** strategy, pitting on lap(s) **{optimal_pit_laps_str}**.")
                # Convert total seconds (float) to HH:MM:SS format
                # First, round to the nearest whole second
                total_seconds_int = int(round(optimal_time_seconds))

                # Calculate hours, minutes, and seconds
                hours = total_seconds_int // 3600
                minutes = (total_seconds_int % 3600) // 60
                seconds = total_seconds_int % 60

                # Create the formatted string, padding with leading zeros where needed
                formatted_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                st.info(f"Predicted total race time: **{formatted_time_str} (HH:MM:SS)**.")
            else:
                st.warning("Could not find any viable strategies based on the data.")

        # --- Interactive Driver Degradation Comparison ---
        st.header("Driver Performance Deep Dive")
        st.write("Select multiple drivers and a tyre compound to compare their degradation.")

        all_drivers = sorted(laps_data['Driver'].unique())
        selected_drivers = st.multiselect(
            "Select Drivers to Compare:",
            options=all_drivers,
            default=[d for d in ['VER', 'HAM', 'LEC'] if d in all_drivers]
        )
        compound_to_analyze = st.selectbox(
            "Select Tyre Compound:",
            options=sorted(laps_data['Compound'].unique())
        )

        if selected_drivers and compound_to_analyze:
            fig, ax = plt.subplots(figsize=(10, 6))
            for driver in selected_drivers:
                # (Your plotting logic remains exactly the same here)
                stint_data = laps_data.pick_driver(driver).loc[laps_data['Compound'] == compound_to_analyze].copy()
                stint_data = stint_data.loc[stint_data['PitInTime'].isnull() & stint_data['PitOutTime'].isnull()].copy()
                if len(stint_data) < 5: continue
                
                stint_data['LapTimeSeconds'] = stint_data['LapTime'].dt.total_seconds()
                median = stint_data['LapTimeSeconds'].median()
                stint_data = stint_data.loc[stint_data['LapTimeSeconds'] < median * 1.07].copy()
                if len(stint_data) < 5: continue
                
                fuel_correction = stint_data['LapNumber'] * fuel_effect
                stint_data['CorrectedLapTime'] = stint_data['LapTimeSeconds'] + fuel_correction
                
                x_values = stint_data['TyreLife']
                y_values = stint_data['CorrectedLapTime']
                
                scatter = ax.scatter(x_values, y_values, label=driver)
                plot_color = scatter.get_facecolor()[0]
                
                coeffs = np.polyfit(x_values, y_values, 1)
                line = np.poly1d(coeffs)
                ax.plot(x_values, line(x_values), color=plot_color)
            
            ax.set_xlabel("Tyre Life (Laps)")
            ax.set_ylabel("Fuel-Corrected Lap Time (s)")
            ax.set_title(f"Degradation Comparison on {compound_to_analyze} Tyre")
            ax.legend()
            st.pyplot(fig)
    
    # This 'else' corresponds to 'if laps_data is not None'
    elif st.session_state.analysis_run: # Only show error if an analysis was attempted
        st.error(f"No data found for {year} {race} GP ({session_type}). Please check the event name and year.")
            

    






















