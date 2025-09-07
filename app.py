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
def load_data(year, race):
    """Loads and processes lap data for a given F1 session."""
    try:
        ff1.Cache.enable_cache('cache') 
        session = ff1.get_session(year, race, 'R')
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

# Sidebar for user inputs
st.sidebar.header("Race Parameters")
year = st.sidebar.number_input("Year", value=2023, min_value=2018)
race = st.sidebar.text_input("Race Name", value="Bahrain")
total_laps = st.sidebar.number_input("Total Laps", value=57)
pit_stop_loss = st.sidebar.number_input("Pit Stop Time Loss (s)", value=22.0)
base_lap_time = st.sidebar.number_input("Base Lap Time (s)", value=99.5)
fuel_effect = st.sidebar.number_input("Fuel Effect (s/lap)", value=0.04, format="%.3f")


if st.button("Press here to Analyze Race and Predict Strategy"):
    # Load data
    laps_data = load_data(year, race)

    if laps_data is not None:
        col1, col2, = st.columns(2)

        # Calculate degradation model
        with col1:
         st.header(f"Analysis for {year} {race} GP")
         drivers = laps_data['Driver'].unique()
         compounds = laps_data['Compound'].unique()
         reliable_stints = []
         for driver in drivers:
            for compound in compounds:
                degradation = calculate_degradation(laps_data, driver, compound, fuel_effect)
                if degradation is not None:
                    reliable_stints.append({'Driver': driver, 'Compound': compound, 'Degradation': degradation})
        
        reliable_summary = pd.DataFrame(reliable_stints)
        final_degradation_summary = reliable_summary.groupby('Compound')['Degradation'].mean().reset_index()

        st.subheader("Tyre Degradation Model")
        st.write("Average degradation in seconds per lap, calculated from reliable race stints:")
        st.dataframe(final_degradation_summary.sort_values(by='Degradation'))

        st.header("Optimal Strategy Prediction")

            one_stop_strategies = [
                find_best_one_stop(['SOFT', 'HARD'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_one_stop(['MEDIUM', 'HARD'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_one_stop(['HARD', 'SOFT'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_one_stop(['HARD', 'MEDIUM'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_one_stop(['SOFT', 'MEDIUM'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_one_stop(['MEDIUM', 'SOFT'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
            ]   
            
            two_stop_strategies = [
                find_best_two_stop(['SOFT','SOFT','MEDIUM'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['SOFT','SOFT','HARD'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['SOFT','MEDIUM','SOFT'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['SOFT','MEDIUM','MEDIUM'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['SOFT','MEDIUM','HARD'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['SOFT','HARD','SOFT'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['SOFT','HARD','MEDIUM'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['SOFT','HARD','HARD'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['MEDIUM','SOFT','SOFT'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['MEDIUM','SOFT','MEDIUM'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['MEDIUM','SOFT','HARD'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['MEDIUM','MEDIUM','SOFT'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['MEDIUM','MEDIUM','HARD'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['MEDIUM','HARD','SOFT'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['MEDIUM','HARD','MEDIUM'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['MEDIUM','HARD','HARD'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),

                find_best_two_stop(['HARD','SOFT','SOFT'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['HARD','SOFT','MEDIUM'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['HARD','SOFT','HARD'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['HARD','MEDIUM','SOFT'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['HARD','MEDIUM','MEDIUM'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['HARD','MEDIUM','HARD'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['HARD','HARD','SOFT'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss),
                find_best_two_stop(['HARD','HARD','MEDIUM'], total_laps, final_degradation_summary, base_lap_time, fuel_effect, pit_stop_loss)

            ]

        all_results = pd.DataFrame([s for s in one_stop_strategies + two_stop_strategies if s is not None])

        if not all_results.empty:
            overall_best = all_results.loc[all_results['Total Time (s)'].idxmin()]
        
            st.subheader("Comparison of Top Strategies")
            st.dataframe(all_results.sort_values(by='Total Time (s)'))

            optimal_strategy_name = np.atleast_1d(overall_best['Strategy'])[0]


    # Safely extract scalar values
            optimal_pit_lap_1 = int(np.atleast_1d(overall_best['Pit Lap 1'])[0])
            optimal_pit_lap_2 = np.atleast_1d(overall_best['Pit Lap 2'])[0]  # extract single value
            optimal_time_seconds = float(np.atleast_1d(overall_best['Total Time (s)'])[0])

    # Handle NaN for second pit stop
        if pd.isna(optimal_pit_lap_2):
         optimal_pit_laps_str = str(optimal_pit_lap_1)
        else:
         optimal_pit_lap_2 = int(optimal_pit_lap_2)
         optimal_pit_laps_str = f"{optimal_pit_lap_1}, {optimal_pit_lap_2}"

        
        st.success(f"**Optimal Strategy Found:** A **{optimal_strategy_name}** strategy, pitting on lap(s) **{optimal_pit_laps_str}**.")
        st.info(f"Predicted total race time: **{optimal_time_seconds / 60:.2f} minutes**.")

    else:
            st.warning("Could not find any viable strategies based on the data.")
        
        with col2:
            # --- Interactive Driver Degradation Comparison ---
            laps_data = load_data(year, race)
            st.header("Driver Performance Deep Dive")
            st.write("Select multiple drivers and a tyre compound to compare their degradation.")

            all_drivers = sorted(laps_data['Driver'].unique())
            selected_drivers = st.multiselect(
            "Select Drivers to Compare:",
            options=all_drivers,
            default=['VER', 'GAS', 'TSU']
            )
            compound_to_analyze = st.selectbox(
            "Select Tyre Compound:",
            options=sorted(laps_data['Compound'].unique())
            )
        
            if selected_drivers and compound_to_analyze:
            fig, ax = plt.subplots(figsize=(10, 6))
            for driver in selected_drivers:
                stint_data = laps_data.pick_driver(driver).loc[laps_data['Compound'] == compound_to_analyze].copy()
                stint_data = stint_data.loc[stint_data['PitInTime'].isnull() & stint_data['PitOutTime'].isnull()].copy()
                if len(stint_data) < 5: continue
                
                stint_data['LapTimeSeconds'] = stint_data['LapTime'].dt.total_seconds()
                median = stint_data['LapTimeSeconds'].median()
                stint_data = stint_data.loc[stint_data['LapTimeSeconds'] < median * 1.07].copy()
                if len(stint_data) < 5: continue
                
                fuel_correction = stint_data['LapNumber'] * fuel_effect
                stint_data['CorrectedLapTime'] = stint_data['LapTimeSeconds'] + fuel_correction
                
                # Explicitly define x and y for the current driver in the loop
                x_values = stint_data['TyreLife']
                y_values = stint_data['CorrectedLapTime']
                
                # Plot this driver's scatter points
                scatter = ax.scatter(x_values, y_values, label=driver)
                
                # Get the color of the scatter plot to use for the trend line
                plot_color = scatter.get_facecolor()[0]
                
                # Fit and plot the trend line using this driver's specific x and y values
                coeffs = np.polyfit(x_values, y_values, 1)
                line = np.poly1d(coeffs)
                ax.plot(x_values, line(x_values), color=plot_color, label=f"{driver} Trend")
                
            ax.set_xlabel("Tyre Life (Laps)")
            ax.set_ylabel("Fuel-Corrected Lap Time (s)")
            ax.set_title(f"Degradation Comparison on {compound_to_analyze} Tyre")
            ax.legend()

            st.pyplot(fig)
            

    




