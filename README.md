<h1>F1 Race Strategy Simulator & Predictor</h1>
<img width="1920" height="2673" alt="screencapture-f1strategysimulator-6sxj7sypamnqf7iamcplzl-streamlit-app-2025-09-09-00_19_18" src="https://github.com/user-attachments/assets/a4da396f-7f82-4883-9ba2-66bf86a2039b" />


This project is a data-driven tool built with Python to analyze real Formula 1 race data, model tyre performance, and predict the optimal pit stop strategy. The application takes raw lap-by-lap data from an F1 Grand Prix, calculates the true degradation rate of each tyre compound while correcting for confounding variables like fuel load, and simulates thousands of potential strategies to find the fastest way to the finish line. The entire analysis is presented in an interactive web application built with Streamlit.
</p>

<h2>Key Features</h2>
<b>1. Data-Driven Tyre Model:</b> Automatically calculates tyre degradation rates from real race data.
<p></p><b>2. Intelligent Data Cleaning:</b> Corrects for the masking effect of fuel burn and removes outlier laps from on-track incidents like Safety Cars.</p>
<p><b>3. Strategy Simulation Engine:</b> Predicts the total race time for any given one-stop or two-stop strategy.</p>
<p></p><b>4. Automated Optimal Search:</b> Programmatically searches thousands of possible pit stop windows to find the absolute fastest strategy.</p>
<p><b>5. Interactive Dashboard:</b> A user-friendly web interface built with Streamlit to visualize driver performance and display the final strategic recommendations. </p>

<h2>How it Works</h2>
<p>The project follows a four step data analysis pipeline to go from raw data to a final prediction</p>
<p><h4>1. Data Sourcing & Cleaning</h4></p>
<p> The process starts by sourcing granular lap by lap data for a given race using the fastf1 library. This raw data has discrepancies and not suitable for data analysis. The first step is to clean it by:</p>
<ul>
  <li>Filtering out laps that are not represtative fo a car's true pace, such as pit in laps and pit out laps.</li>
  <li>Removing laps completed under Safety Car or Virtual Safety Car conditions, which are indentified as significant outliers.</li>
</ul>
<h4>2. Modelling Tyre Performance</h4>
<p>The core of the predictor is a robust model of a tyre performance. A key insight during this project was that the raw lap times are misleading; at the start of a race, cars get faster each lap as they burn fuel, masking the effect of tyre wear. </p>
<p>To solve this, the model calculates a "Fuel-Corrected Lap Time" for each lap. By adding back the time gained from the car getting lighter, we can isolate the true degradation rate of the tyres. A linear regression model is then fitted to this corrected data to derive a single metric which is <b>'degradation in seconds per lap'</b></p>
<img width="1460" height="948" alt="image" src="https://github.com/user-attachments/assets/77712e58-a4f8-4cb8-8bf9-f46b2c4d907c" />
<h4>3. Simulating Race Strategies</h4>
<p>With accurate degradation numbers, the applications can predict the time for any lap in a stint using the following formula:</p>
<p></p><b><i>Predicted Time = Base Time + (Tyre Life x Degradation) - (Lap Number x Fuel Effect)</i></b></p>
<p>A simulation engine uses this formula to calculate the total predicted time for any sequence of tyre stints, adding a time penalty for each pit stop.</p>
<h4>4. Finding the Optimal Strategy</h4>
<p>Instead of manually comparing a few strategies, the predictor uses an automated search to find the true optimum. It programmatically simulates every possible one-stop and two-stop strategy within a realistic pit window, using nested loops to cover thousands of combinations. The strategy with the lowest total simulates race time is then presented as the final recommendation. </p>
<h4> Technologies Used </h4>
<ul>
  <li> Language: Python </li>
  <li> Data Analysis: Pandas, NumPy </li>
  <li> F1 Data API: fastf1 </li>
  <li> Visualization: Matplotlib </li>
  <li> Web Framework: Streamlit </li>
</ul>
<h4>Getting Started</h4>
<h5>Prerequisites</h5>
<ul>
  <li> Python 3.9+</li>
  <li> Pip </li>
</ul>

<h4> Installation </h4>

<p>You can directly access the web app from this link: https://f1strategysimulator-6sxj7sypamnqf7iamcplzl.streamlit.app/ or follow the steps below to run it locally on your device.</p>

<p>1. Clone the repository</p>
<p><i>git clone [https://github.com/ThenameisAan/F1_Strategy_Simulator.git](https://github.com/ThenameisAan/F1_Strategy_Simulator.git)</i></p>
<p><i></p>cd F1_Strategy_Simulator</i></p>
<p>2. Install the required packages: <i>pip install -r requirements.txt</i>
<h4>Running the Application</h4>
<p>To launch the interactive dashboard, run the following command in your terminal: </p>
<p><i>streamlit run app.py</i></p>

<h4>Video Tutorial:</h4> 
<h4>Future Improvements</h4>
<ul>
  <li> Context Awareness Penalties: Adding penalties for traffic, tyre warm-up, and track position value to create an even more realistic simulation</li>
<li> Safety Car Proabability: Incorporating a Monte Carlo simulations to model the likelihood of a safety cat and its impact on strategy.</li>
<li>More Complex Models: Using non-linear models to better capture the "cliff" where tyre performance drops off sharply.</li>
<ul>


