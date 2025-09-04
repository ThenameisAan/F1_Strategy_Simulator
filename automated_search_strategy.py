import pandas as pd
import numpy as np
import fastf1 as ff1

# --- Model Inputs ---

#1. Final degradation summary calculated from degradation_summary
degradation_data = {
'Compound': ['SOFT', 'HARD', 'MEDIUM'],
'Degradation': [0.014756, 0.071352, 0.275393]
}
degradation_summary = pd.DataFrame(degradation_data)

#2. Assumption for bahrain circuit
base_lap_time = 99.5 #in sec
fuel_effect_per_lap = 0.04 #sec gained per lap from fuel burn
pit_stop_time_loss = 22 
total_laps = 57

# Stint Simulator Function 
def simulate_stint(start_lap, stint_length, compound):
    #Calculate total time for a single race stint
    #Get degradation rate for the chosen compound

    degradation_rate = degradation_summary.loc[degradation_summary['Compound'] == compound, 'Degradation'].iloc[0]

    total_stint_time = 0

    for i in range(stint_length):
        current_lap_in_race = start_lap + i
        current_tyre_life = i + 1

        # Calculate the different time effects
        tyre_effect = current_tyre_life * degradation_rate
        fuel_effect = current_lap_in_race * fuel_effect_per_lap

        #Calculate final predicted lap time
        predicted_lap_time = base_lap_time + tyre_effect - fuel_effect

        #Add lap time to the total
        total_stint_time = total_stint_time + predicted_lap_time
    
    return total_stint_time

def simulate_strategy(strategy):
    #Calculate the total race time for a given strategy
    total_race_time = 0
    start_lap = 1

    for stint in strategy:
        stint_time = simulate_stint(start_lap=start_lap, stint_length=stint['StintLength'], compound=stint['Compound'])
        total_race_time = total_race_time + stint_time
        start_lap = start_lap + stint['StintLength']

    # Add time for pit stops (number of stints - 1)
    num_pit_stops = len(strategy) - 1
    total_race_time = total_race_time + (num_pit_stops * pit_stop_time_loss)

    return total_race_time

# === Automated Search for the best one-stop strategy

def find_best_one_stop (start_compound, end_compound):
    pit_window_start = 12
    pit_window_end = 30
    results = []

    for pit_lap in range(pit_window_start, pit_window_end + 1):
        stint1_length = pit_lap
        stint2_length = total_laps - stint1_length
        strategy = [
            {'Compound': start_compound, 'StintLength': stint1_length},
            {'Compound': end_compound, 'StintLength': stint2_length}

        ]
        total_time = simulate_strategy(strategy)
        results.append({'Pit Lap': pit_lap, 'Total Time (s)': total_time})
    
    results_df = pd.DataFrame(results)
    best_strategy = results_df.loc[results_df['Total Time (s)'].idxmin()]
    return best_strategy

# === Run the search for both starting tyres ===

#1. Find the best strategy on SOFT
best_soft_start = find_best_one_stop('SOFT', 'HARD')
print("\nBest 1-stop strategy starting on SOFT:")
print(best_soft_start)

#2. Find the best strategy starting on MEDIUM
best_medium_start = find_best_one_stop('MEDIUM', 'HARD')
print("\nBest 1-stop strategy starting on MEDIUM:")
print(best_medium_start)

#Compare final results
soft_time = best_soft_start['Total Time (s)']
medium_time = best_medium_start['Total Time (s)']
