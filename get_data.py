import fastf1 as ff1
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#Store f1 data in the cache folder
ff1.Cache.enable_cache('cache')

#Show all columns of the dataframe
pd.set_option('display.max_columns', None)

#Load the session data
session = ff1.get_session(2023, 'Bahrain', 'R')
session.load()
laps = session.laps

#pick driver
ver_laps = laps.pick_drivers('VER')

#Select soft tyre laps
ver_soft_laps = ver_laps.loc[ver_laps['Compound'] == 'SOFT'].copy()

#Filer PitInTime and PitTimeOut
ver_soft_laps = ver_soft_laps.loc[ver_soft_laps['PitInTime'].isnull() & ver_soft_laps['PitOutTime'].isnull()].copy()

#Convert LapTime to seconds
ver_soft_laps['LapTimeSeconds'] = ver_soft_laps['LapTime'].dt.total_seconds()

# Get data from cleaned DataFrame
x= ver_soft_laps['TyreLife']
y= ver_soft_laps['LapTimeSeconds']

#Scatter Plot
plt.scatter(x,y)
plt.xlabel("Tyre Life (Laps)")
plt.ylabel("Lap Time (Seconds)")
plt.title("Verstappen's Soft Tyre Stint")

#np.polyfit() finds the slope and intercept of the best fit line
coeffs = np.polyfit(x,y,1)

#np.poly1d() creates a function from those coefficients 
line = np.poly1d(coeffs)

#Plot of best fit line
plt.plot(x, line(x), color = 'purple')

#Display the plot
plt.show()
print(f"The slope of the original line is: {coeffs[0]}")

#Fuel Correction
fuel_correction = ver_soft_laps['LapNumber'] * 0.04 #.04 seconds is the avg time gained each lap due to loss of ~1.5kg fuel

#Create fuel corrected lap time column
ver_soft_laps['CorrectedLapTime'] = ver_soft_laps['LapTimeSeconds'] + fuel_correction

#Plot corrected lap times
plt.scatter(ver_soft_laps['TyreLife'], ver_soft_laps['CorrectedLapTime'])
plt.xlabel("Tyre Life (Laps)")
plt.ylabel("Fuel-Corrected Lap Time (Seconds)")
plt.title("Verstappen's Soft Tyre Stint (Fuel Corrected)")

#Fit new line to the corrected data
coeffs_corrected = np.polyfit(ver_soft_laps['TyreLife'], ver_soft_laps['CorrectedLapTime'],1)
line_corrected = np.poly1d(coeffs_corrected)

plt.plot(ver_soft_laps['TyreLife'],line_corrected(ver_soft_laps['TyreLife']),color='green')

#Show corrected plot
plt.show()

#Print the slope of the new line
print(f"The slope of the new corrected line is: {coeffs_corrected[0]}")