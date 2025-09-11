<h1>Predictive Analytics for Motorsport: An F1 Race Strategy Simulation Model</h1>
<img width="1920" height="2673" alt="screencapture-f1strategysimulator-6sxj7sypamnqf7iamcplzl-streamlit-app-2025-09-09-00_19_18" src="https://github.com/user-attachments/assets/a4da396f-7f82-4883-9ba2-66bf86a2039b" />

<p>This project applies data science principles to the high-stakes world of Formula 1, demonstrating a full pipeline from data ingestion and cleaning to predictive modeling, simulation, and business-focused recommendations. The final result is an interactive Streamlit dashboard that finds the optimal pit stop strategy for any given F1 race.
</p>

<h2>1. Executive Summary</h2>
<p>In Formula 1, race strategy is a multi-million dollar decision made under extreme pressure. This project addresses the core business problem of identifying the fastest possible strategy from thousands of combinations.
The solution is a Python-based application that models the performance of a key depreciating asset—the tyres. By analyzing practice session data, the model predicts tyre wear, simulates every viable one-stop and two-stop strategy, and provides a clear, data-driven recommendation for the optimal approach. When validated against the 2025 Monza Grand Prix, the model's predicted optimal race time was within 2 second of the actual winning time, demonstrating its high accuracy and business value.</p>

<h2>2. Business Problem</h2>
<p>Formula 1 is a sport of marginal gains where strategic decisions can be more impactful than the raw speed of the car. The central challenge for any team strategist is to determine the optimal time to make a pit stop.

<ul>
  <li>Pitting too early might provide a short-term advantage but results in longer, slower stints on worn tyres later in the race.</li>
  <li>Pitting too late means losing valuable time to competitors on fresher, faster tyres.</li>
</ul>

Making the wrong call can cost a team millions in prize money and championship points. This project aims to solve this problem by moving beyond intuition and using a data-driven approach to find the mathematically fastest way to complete a race.</p>

<h2>3. Methodology</h2>
<p>To solve this business problem, a four-step data analysis and simulation methodology was employed:

1. Data Ingestion and Cleaning: Sourced raw, lap-by-lap data from real F1 sessions using the fastf1 library. This noisy data was cleaned to remove non-representative laps, such as those during pit stops or Safety Car periods, using a median-based outlier detection rule (the 107% rule).

2. Predictive Modeling (Linear Regression): Modeled the performance of the key asset (tyres). The biggest challenge was correcting for a major confounding variable: the car's fuel load. As a car gets lighter, it gets faster, masking the true rate of tyre wear. A "fuel-corrected lap time" was calculated to isolate the tyre degradation, and a linear regression model was fitted to this clean data to determine the performance loss in seconds per lap for each tyre compound.

3. Simulation & Optimization: Developed a simulation engine that uses the degradation model to predict the total time for any given strategy. An automated search algorithm (using nested loops) was implemented to exhaustively test thousands of one-stop and two-stop combinations to find the true optimum.

4. Dashboarding & Visualization: The entire analysis was wrapped in an interactive dashboard using Streamlit. This allows a user to select a race, see the underlying tyre model, and view the final strategic recommendations. A key feature is the "Driver Performance Deep Dive," which provides a head-to-head visual comparison of how different drivers managed their tyres.</p>

<h2>4. Skills</h2>
<ul>
  <li>Languages: Python</li>
  <li>Libraries & Frameworks:</li>
    <li>Data Analysis & Modeling: Pandas (for data manipulation), NumPy (for numerical operations), Matplotlib (for visualization).</li>
</ul>

