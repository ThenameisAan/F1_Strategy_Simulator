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
total_laps = 57

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

def simulate_strategy(strategy):
    #Calculate the total race time for a given strategy
    total_race_time = 0
    start_lap = 1

    for stint in strategy:
        stint_time = simulate_stint(
            start_lap=start_lap,
            stint_length=stint['StintLength'],
            compound=stint['Compound']
        )
        total_race_time = total_race_time + stint_time
        start_lap = start_lap + stint['StintLength']

    # Add time for pit stops (number of stints - 1)
    num_pit_stops = len(strategy) - 1
    total_race_time = total_race_time + (num_pit_stops * pit_stop_time_loss)

    return total_race_time

# --- Simulate and compare two strategies ---

#Strategy 1: One pit stop (Soft -> Hard)
strategy_one_stop = [
    {'Compound': 'SOFT', 'StintLength': 14},
    {'Compound': 'HARD', 'StintLength': 43} # (total laps = 57) - 14
]

#Strategy 2: Two pit stop (Soft -> Hard -> Soft)
strategy_two_stop = [
    {'Compound': 'SOFT', 'StintLength': 14},
    {'Compound': 'HARD', 'StintLength': 25},
    {'Compound': 'HARD', 'StintLength': 18},
]

total_time_one_stop = simulate_strategy(strategy_one_stop)
total_time_two_stop = simulate_strategy(strategy_two_stop)

print(f"Predicted time for 1-stop strategy: {total_time_one_stop /60:.2f} min")
print(f"Predicted time for 2-stop strategy: {total_time_two_stop /60:.2f} min")
 