# Data Analytics for Accounting and Audit (ABL-C1103)

Aalto University · 6 ECTS · Spring 2025 · Group project · Grade: 3 (Good)

## ROIC sensitivity among European airlines

The airline industry is highly capital-intensive and sensitive to external shocks (fuel prices, business cycles, pandemics). We analyzed which financial drivers most affect airlines' **Return on Invested Capital (ROIC)** and built an interactive dashboard for scenario analysis.

- Statistical analysis of airline financials (revenue, EBIT, invested capital, CapEx, …) — regression and feature-importance analysis showing invested capital and CapEx as the dominant ROIC drivers
- Dash web app computing ROIC directly from EBIT, tax rate, and invested capital, with algebraic scenario sensitivity (CapEx −10 %, invested capital +15 %, revenue +10 %) and Holt-Winters forecasting

## Files

| File | Description |
|------|-------------|
| `airline_roic_analysis.ipynb` | Statistical analysis: EDA, regression, feature importances |
| `roic_dashboard.py` | Interactive Dash dashboard with scenario sensitivity |
| `data/airline_financials.csv` | Airline financials dataset |
| `team_presentation.pptx` | Team presentation of the analysis |

## Running the dashboard

```bash
pip install dash pandas numpy plotly statsmodels
python roic_dashboard.py   # expects airline financials.csv — point it at data/airline_financials.csv
```

**Tools:** Python (pandas, statsmodels, scikit-learn), Dash/Plotly
