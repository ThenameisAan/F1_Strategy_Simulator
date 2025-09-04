import pandas as pd

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

# Stint Simulator Function 
def simulate_stint(start_lap, stint_length, compound):
    #Calculate total time for a single race stint
    #Get degradation rate for the chosen compound

    degradation_rate = degradation_summary.loc[
      degradation_summary['Compound'] == compound, 'Degradation'
    ].iloc[0]

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

# Test function

# Simulate a 14-lap opening stint on SOFT tyres
stint1_time = simulate_stint(start_lap = 1, stint_length=14, compound='SOFT')
print(f"Predicted time for a 14 lap SOFT stint: {stint1_time:.2f} seconds")

# Simulate a 25-lap middle stint on HARD tyres
stint2_time = simulate_stint(start_lap = 1, stint_length=14, compound='HARD')
print(f"Predicted time for a 25 lap HARD stint: {stint2_time:.2f} seconds")