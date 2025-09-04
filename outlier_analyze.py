import fastf1 as ff1
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt

def calculate_degradation(laps, driver, compound, fuel_effect_per_lap = 0.04):
    #Calculate the tyre degradation of a specific driver and compound.

    #Args:
     #laps (pd.DataFrame): The DataFrame of all laps in the session.
     #driver (str): The three letter abbreviation for the driver
     #compound (str): The tyre compund to analyse 
     #fuel_effect_per_lap (float): The assumed time gain per lap from fuel burn

     #Returns
        #The Calculated degradation in seconds per lap, or none if the stint is too short

        #1. Select the driver's lap for specified compound
            stint_laps = laps.pick_driver(driver).loc[laps['Compound'] == compound].copy()
        #2. Remove pit in/out laps
            stint_laps = stint_laps.loc[stint_laps['PitInTime'].isnull() & stint_laps['PitOutTime'].isnull()].copy()
        #3. Check if enough data is available to analyze 
            if len(stint_laps) < 5:
                return None
        #4. Calculate lap time in seconds and correct for fuel:
            stint_laps['LapTimeSeconds'] = stint_laps['LapTime'].dt.total_seconds()
            fuel_correction = stint_laps['LapNumber'] * fuel_effect_per_lap
            stint_laps['CorrectedLapTime'] = stint_laps['LapTimeSeconds'] + fuel_correction
        #5. Fit a linear regression model
            x = stint_laps['TyreLife']
            y = stint_laps['CorrectedLapTime']
            coeffs = np.polyfit(x,y,1)
        #6. The slope of the line is degradation value
            degradation = coeffs[0]

            return degradation

#Store f1 data in the cache folder
ff1.Cache.enable_cache('cache')

#Show all columns of the dataframe
pd.set_option('display.max_columns', None)

#Load the session data
session = ff1.get_session(2023, 'Bahrain', 'R')
session.load (telemetry=False, weather = False)
laps = session.laps

# --- Investigate Verstappen's HARD tyre stint ---

ver_laps = laps.pick_drivers('VER')

# Create a clean DataFrame for the Hard tyre stint
ver_hard_laps = ver_laps.loc[ver_laps['Compound'] == 'HARD'].copy()
ver_hard_laps = ver_hard_laps.loc[ver_hard_laps['PitInTime'].isnull() & ver_hard_laps['PitOutTime'].isnull()].copy()
ver_hard_laps['LapTimeSeconds'] = ver_hard_laps['LapTime'].dt.total_seconds()

# --- NEW CODE FOR OUTLIER REMOVAL ---
# We calculate the median lap time and keep only laps that are within 107% of it
median_lap_time = ver_hard_laps['LapTimeSeconds'].median()
ver_hard_laps = ver_hard_laps.loc[ver_hard_laps['LapTimeSeconds'] < median_lap_time * 1.07].copy() 
# --- END OF NEW CODE ---

# Calculate fuel-corrected lap time for the Hard stint
fuel_correction_hard = ver_hard_laps['LapNumber'] * 0.04
# Add a .copy() here as well to be safe and avoid the warning
ver_hard_laps['CorrectedLapTime'] = ver_hard_laps['LapTimeSeconds'] + fuel_correction_hard

# Plot the corrected lap times for the HARD stint
plt.scatter(ver_hard_laps['TyreLife'], ver_hard_laps['CorrectedLapTime'])
plt.xlabel("Tyre Life (Laps)")
plt.ylabel("Fuel-Corrected Lap Time (Seconds)")
plt.title("Verstappen's HARD Tyre Stint (Fuel Corrected & Outliers Removed)")

# Fit and plot the trend line
coeffs_hard = np.polyfit(ver_hard_laps['TyreLife'], ver_hard_laps['CorrectedLapTime'], 1)
line_hard = np.poly1d(coeffs_hard)
plt.plot(ver_hard_laps['TyreLife'], line_hard(ver_hard_laps['TyreLife']), color='orange')

plt.show()

# Print the new, more accurate degradation value
print(f"Verstappen HARD degradation (outliers removed): {coeffs_hard[0]:.4f} sec/lap")
