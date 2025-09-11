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


