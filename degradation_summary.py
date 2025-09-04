import fastf1 as ff1
import pandas as pd
import numpy as np

def calculate_degradation(laps, driver, compound, fuel_effect_per_lap = 0.04):
    # Calculate the tyre degradation for a specific driver and compound, including fuel correction and outlier removal.

        #1. Select the driver's lap for specified compound
            stint_laps = laps.pick_driver(driver).loc[laps['Compound'] == compound].copy()
        #2. Remove pit in/out laps
            stint_laps = stint_laps.loc[stint_laps['PitInTime'].isnull() & stint_laps['PitOutTime'].isnull()].copy()
        #3. Check if enough data is available to analyze 
            if len(stint_laps) < 5:
                return None
        #4. Remove outliers 
            stint_laps['LapTimeSeconds'] = stint_laps['LapTime'].dt.total_seconds()
            median_lap_time = stint_laps['LapTimeSeconds'].median()
            stint_laps = stint_laps.loc[stint_laps['LapTimeSeconds'] < median_lap_time * 1.07]. copy()
        #5. Check again if enough data is available after removing outliers
            if len (stint_laps) < 5:
                    return None
        #6. Calculate fuel-corrected lap time
            fuel_correction = stint_laps['LapNumber'] * fuel_effect_per_lap
            stint_laps['CorrectedLapTime'] = stint_laps['LapTimeSeconds'] + fuel_correction
        #7. Fit a linear regression model
            x = stint_laps ['TyreLife']
            y = stint_laps ['CorrectedLapTime']
            coeffs = np.polyfit(x,y,1)

            degradation = coeffs[0]

            return degradation

# === Main part of the script === 
ff1.Cache.enable_cache('cache')
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

#Load the session data
session = ff1.get_session(2023, 'Bahrain', 'R')
session.load (telemetry=False, weather = False)
laps = session.laps

# === Loop through all drivers and compounds to build the summary ===
results = []
drivers = session.drivers #Get a list of all driver numbers
compounds = laps['Compound'].unique() #Get a list of all unique compounds

for driver_num in drivers:
    driver_abbr = laps.loc[laps['DriverNumber'] == driver_num, 'Driver'].iloc[0]
    for compound in compounds:
           #Check stint length before calculating degradation
           stint_laps = laps.pick_driver(driver_abbr).loc[laps['Compound'] == compound]
           if len(stint_laps) >= 10: #stint laps greater than 10 to ensure no outliers effect
            degradation = calculate_degradation(laps, driver_abbr, compound)
            if degradation is not None:
                  results.append({
                    'Driver': driver_abbr,
                    'Compound': compound,
                    'Degradation': degradation     
                  })

#Convert the results list to a DataFrame and sort it
reliable_summary = pd.DataFrame(results)

#Calculate average degradation per second
degradation_summary = reliable_summary.groupby('Compound')['Degradation'].mean().reset_index()
degradation_summary = degradation_summary.sort_values (by='Degradation')

print("--- Average Tyre Degradation Summary (Bahrain 2023) ---")
print(degradation_summary)