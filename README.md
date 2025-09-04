<h1>F1 Race Strategy Simulator & Predictor</h1>
<img width="1915" height="876" alt="image" src="https://github.com/user-attachments/assets/61744019-85ec-4196-b940-9115b7368cb5" />

This project is a data-driven tool built with Python to analyze real Formula 1 race data, model tyre performance, and predict the optimal pit stop strategy. The application takes raw lap-by-lap data from an F1 Grand Prix, calculates the true degradation rate of each tyre compound while correcting for confounding variables like fuel load, and simulates thousands of potential strategies to find the fastest way to the finish line. The entire analysis is presented in an interactive web application built with Streamlit.

<h2>Key Features</h2>
<b>Data-Driven Tyre Model:</b> Automatically calculates tyre degradation rates from real race data.
<p></p><b>Intelligent Data Cleaning:</b> Corrects for the masking effect of fuel burn and removes outlier laps from on-track incidents like Safety Cars.</p>
<p><b>Strategy Simulation Engine:</b> Predicts the total race time for any given one-stop or two-stop strategy.</p>
<p></p><b>Automated Optimal Search:</b> Programmatically searches thousands of possible pit stop windows to find the absolute fastest strategy.</p>
<p><b>Interactive Dashboard:</b> A user-friendly web interface built with Streamlit to visualize driver performance and display the final strategic recommendations. </p>
