# ───────────────────────────────────────────────────────────────────────────
# app.py - Dash Dashboard with Algebraic Scenario Sensitivity (No ML Model)
#   - Computes ROIC directly from EBIT, TaxRate & InvestedCapital.
#   - Baseline = the maximum year in the user‐selected range.
#   - Scenarios: CapEx -10%, InvestedCapital +15%, Revenue +10%.
#   - ΔROIC = ROIC_scenario - ROIC_baseline.
# ───────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# ─── 1) LOAD & INITIAL CLEAN ──────────────────────────────────────────────────
df = pd.read_csv('airline financials.csv')

df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')
df = df.dropna(subset=['Year'])
df['Year'] = df['Year'].astype(int)

numeric_cols = [
    'Revenue', 'EBIT', 'Tax Rates', 'InvestedCapital',
    'ROIC', 'Net Income', 'Total Assets', 'Total Debt',
    'CapEx', 'Depreciation'
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

before_drop = len(df)
df = df.dropna(subset=['ROIC'])
after_drop = len(df)
if before_drop != after_drop:
    print(f"**INFO**: Dropped {before_drop - after_drop} rows because 'ROIC' was not numeric or missing.")

df = df[df['Year'].between(2012, 2024)].copy()

df['TaxRate'] = df['Tax Rates']
df['NOPAT'] = df['EBIT'] * (1 - df['TaxRate'])
df['BaseROIC'] = df['NOPAT'] / df['InvestedCapital']

full_service = {'Finnair', 'Lufthansa', 'Air France - KLM', 'Aegean Airlines'}
low_cost = {'Ryanair', 'Norwegian', 'Wizz Air'}
df['BusinessModel'] = df['Company'].apply(
    lambda x: 'Full-Service' if x in full_service
    else ('Low-Cost' if x in low_cost else 'Hybrid')
)

df['COVID'] = df['Year'].apply(lambda y: 1 if y in [2020, 2021] else 0)

# ─── 2) DASH APP SETUP ───────────────────────────────────────────────────────
app = Dash(__name__)
server = app.server 

all_years = sorted(df['Year'].unique())
min_year, max_year = all_years[0], all_years[-1]
all_companies = sorted(df['Company'].unique())

app.layout = html.Div(style={'fontFamily': 'Arial', 'margin': '20px'}, children=[
    html.H1("A Comparative Scenario Analysis of Finnair & Competitors", style={'textAlign': 'center'}),

    # ── Controls: Year-Range Slider & Company Dropdown ─────────────────────────
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '20px'}, children=[
        html.Div(style={'width': '65%'}, children=[
            html.Label("Select Year Range:", style={'fontWeight': 'bold'}),
            dcc.RangeSlider(
                id='year-range-slider',
                min=int(min_year),
                max=int(max_year),
                value=[int(min_year), int(max_year)],
                marks={int(y): str(int(y)) for y in all_years},
                step=1
            )
        ]),
        html.Div(style={'width': '30%'}, children=[
            html.Label("Select Company(s):", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='company-dropdown',
                options=[{'label': c, 'value': c} for c in all_companies],
                value=all_companies,  # select all by default
                multi=True,
                placeholder="Choose airlines"
            )
        ])
    ]),

    # ── Row 1: Average ROIC ± Std Dev & Business Model Pie ─────────────────────
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[
        html.Div(style={'width': '49%'}, children=[dcc.Graph(id='avg-roic-bar')]),
        html.Div(style={'width': '49%'}, children=[dcc.Graph(id='business-model-pie')])
    ]),

    # ── Row 2: Volatility of Drivers & Scenario Sensitivity ────────────────────
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '20px'}, children=[
        html.Div(style={'width': '49%'}, children=[dcc.Graph(id='volatility-bar')]),
        html.Div(style={'width': '49%'}, children=[dcc.Graph(id='scenario-bar')])
    ]),

    # ── Row 3: Historical vs Holt-Winters Forecast (All Companies) ─────────────
    html.Div(style={'marginTop': '20px'}, children=[dcc.Graph(id='hist-forecast-line')]),

    html.Div(style={'textAlign': 'center', 'color': '#555', 'marginTop': '10px'},
             children="Use the controls above to filter by year range and companies.")
])

# ─── 3) CALLBACK FUNCTIONS ────────────────────────────────────────────────────
@app.callback(
    [
        Output('avg-roic-bar','figure'),
        Output('business-model-pie','figure'),
        Output('volatility-bar','figure'),
        Output('scenario-bar','figure'),
        Output('hist-forecast-line','figure')
    ],
    [
        Input('year-range-slider','value'),
        Input('company-dropdown','value')
    ]
)
def update_charts(year_range, selected_companies):
    start_year, end_year = year_range

    # ── 3.1) FILTER DF BY Year RANGE & Companies ────────────────────────────────
    mask = (
        df['Year'].between(start_year, end_year)
        & df['Company'].isin(selected_companies)
    )
    filtered_df = df[mask].copy()

    # Print debug info: which companies are missing in this filter
    missing = [c for c in selected_companies if c not in filtered_df['Company'].unique()]
    if missing:
        print(f"**DEBUG**: No data for {missing} in years {start_year}-{end_year}.")

    # ── 3.2) AVERAGE ROIC ± STD DEV ─────────────────────────────────────────────
    if not filtered_df.empty:
        summary_kpis = (
            filtered_df
            .groupby('Company')['ROIC']
            .agg(['mean','std'])
            .reset_index()
        )
    else:
        summary_kpis = pd.DataFrame({'Company':[], 'mean':[], 'std':[]})

    full_list_df = pd.DataFrame({'Company': all_companies})
    summary_kpis = full_list_df.merge(summary_kpis, on='Company', how='left').fillna(0)

    fig_avg = px.bar(
        summary_kpis,
        x='Company',
        y='mean',
        error_y='std',
        color='Company',
        color_discrete_sequence=px.colors.qualitative.Dark24,
        title=f"Average ROIC ± Std Dev ({start_year}-{end_year})"
    )
    fig_avg.update_layout(
        template='plotly_white',
        xaxis_title='Company',
        yaxis_title='Average ROIC',
        showlegend=False,
        margin=dict(t=50)
    )

    # ── 3.3) BUSINESS MODEL COMPOSITION PIE ────────────────────────────────────
    if not filtered_df.empty:
        bm_counts = (
            filtered_df[['Company','BusinessModel']]
            .drop_duplicates()
            .groupby('BusinessModel')
            .size()
            .reset_index(name='Count')
        )
    else:
        bm_counts = pd.DataFrame({'BusinessModel':[], 'Count':[]})

    fig_pie = px.pie(
        bm_counts,
        values='Count',
        names='BusinessModel',
        color='BusinessModel',
        color_discrete_map={'Full-Service':'royalblue','Low-Cost':'seagreen','Hybrid':'orange'},
        title='Business Model Composition'
    )
    fig_pie.update_traces(textinfo='percent+label')
    fig_pie.update_layout(template='plotly_white', margin=dict(t=50))

    # ── 3.4) VOLATILITY OF FINANCIAL DRIVERS ───────────────────────────────────
    if not filtered_df.empty:
        drivers = ['Revenue','EBIT','Net Income','CapEx','InvestedCapital','Total Assets','Depreciation']
        vol = (filtered_df[drivers].std().sort_values()).reset_index()
        vol.columns = ['Driver','StdDev']
    else:
        vol = pd.DataFrame({
            'Driver':['Revenue','EBIT','Net Income','CapEx','InvestedCapital','Total Assets','Depreciation'],
            'StdDev':[0]*7
        })

    fig_vol = px.bar(
        vol,
        x='StdDev',
        y='Driver',
        orientation='h',
        color='StdDev',
        color_continuous_scale='Blues',
        title='Volatility of Financial Drivers'
    )
    fig_vol.add_vline(
        x=vol['StdDev'].mean() if not vol.empty else 0,
        line_dash='dash',
        line_color='red'
    )
    fig_vol.update_layout(
        template='plotly_white',
        xaxis_title='Standard Deviation',
        yaxis_title='Driver',
        margin=dict(t=50)
    )

    # ── 3.5) SCENARIO SENSITIVITY (ALGEBRAIC, LATEST YEAR ONLY) ─────────────────
    #  Step A: Identify max_year in this filtered_df
    if not filtered_df.empty:
        max_year = filtered_df['Year'].max()
        baseline = filtered_df[filtered_df['Year'] == max_year].copy()
    else:
        baseline = pd.DataFrame(columns=df.columns)

    if baseline.empty or baseline['Company'].nunique() == 0:
        fig_scen = go.Figure()
        fig_scen.add_annotation(
            x=0.5, y=0.5, xref='paper', yref='paper',
            text="No data for Scenario Testing",
            font=dict(size=20, color="grey"),
            showarrow=False,
            align="center"
        )
        fig_scen.update_xaxes(visible=False)
        fig_scen.update_yaxes(visible=False)
        fig_scen.update_layout(
            template='plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=60, b=0),
            title=dict(text="ROIC Prediction Under Different Scenarios", x=0.5, xanchor='center')
        )
    else:
        baseline = baseline[baseline['Company'].isin(selected_companies)].copy()

        baseline['NOPAT_base'] = baseline['EBIT'] * (1 - baseline['TaxRate'])
        baseline['ROIC_base'] = baseline['NOPAT_base'] / baseline['InvestedCapital']

        rows = []

        for _, r in baseline.iterrows():
            rows.append({
                'Company': r['Company'],
                'Scenario': 'Baseline',
                'ROIC_pred': r['ROIC_base'],
                'ROIC_delta': 0.0
            })

        # 1) CapEx -10%
        for _, r in baseline.iterrows():
            new_ic = r['InvestedCapital'] * 0.90
            roic_scen = r['NOPAT_base'] / new_ic if new_ic != 0 else np.nan
            rows.append({
                'Company': r['Company'],
                'Scenario': 'CapEx -10%',
                'ROIC_pred': roic_scen,
                'ROIC_delta': roic_scen - r['ROIC_base']
            })

        # 2) InvestedCapital +15%
        for _, r in baseline.iterrows():
            new_ic = r['InvestedCapital'] * 1.15
            roic_scen = r['NOPAT_base'] / new_ic if new_ic != 0 else np.nan
            rows.append({
                'Company': r['Company'],
                'Scenario': 'InvestedCapital +15%',
                'ROIC_pred': roic_scen,
                'ROIC_delta': roic_scen - r['ROIC_base']
            })

        # 3) Revenue +10% (assume EBIT ↑10%)
        for _, r in baseline.iterrows():
            new_ebit = r['EBIT'] * 1.10
            new_nopat = new_ebit * (1 - r['TaxRate'])
            roic_scen = new_nopat / r['InvestedCapital'] if r['InvestedCapital'] != 0 else np.nan
            rows.append({
                'Company': r['Company'],
                'Scenario': 'Revenue +10%',
                'ROIC_pred': roic_scen,
                'ROIC_delta': roic_scen - r['ROIC_base']
            })

        scenario_df = pd.DataFrame(rows)

        # Build the grouped‐bar chart of Predicted ROIC under each scenario
        fig_scen = px.bar(
            scenario_df,
            x='ROIC_pred',
            y='Company',
            color='Scenario',
            orientation='h',
            barmode='group',
            title=f"ROIC Prediction Under Baseline & Stress Scenarios ({min_year}-{max_year})"
        )

        fig_scen.add_vline(x=0, line_dash='dash', line_color='black')
        fig_scen.update_layout(
            template='plotly_white',
            xaxis_title='Predicted ROIC',
            yaxis_title='',
            margin=dict(t=50)
        )

    # ── 3.6) HISTORICAL vs. HOLT-WINTERS FORECAST ───────────────────────────────
    traces = []
    forecast_horizon = 5  # next 5 years

    for company in selected_companies:
        comp_ts = filtered_df[filtered_df['Company'] == company].sort_values('Year').set_index('Year')['ROIC']
        if len(comp_ts) >= 2:
            try:
                hw_model = ExponentialSmoothing(comp_ts, trend='add', seasonal=None).fit(optimized=True)
                fvals = hw_model.forecast(forecast_horizon)
                fyears = list(range(comp_ts.index.max()+1, comp_ts.index.max()+1+forecast_horizon))
            except Exception:
                coeffs = np.polyfit(comp_ts.index, comp_ts.values, 1)
                fyears = list(range(comp_ts.index.max()+1, comp_ts.index.max()+1+forecast_horizon))
                lin_vals = np.polyval(coeffs, fyears)
                fvals = pd.Series(lin_vals, index=fyears)

            # Historical trace
            traces.append(
                go.Scatter(
                    x=comp_ts.index.astype(int),
                    y=comp_ts.values,
                    mode='lines+markers',
                    name=f"{company} (Hist)",
                    marker=dict(size=6),
                    line=dict(width=2),
                    hovertemplate='%{x}: %{y:.3f}<extra>' + company + ' (Hist)</extra>'
                )
            )
            # Forecast trace
            traces.append(
                go.Scatter(
                    x=fyears,
                    y=fvals.values,
                    mode='lines+markers',
                    name=f"{company} (Forecast)",
                    line=dict(dash='dash', width=2),
                    marker=dict(size=6),
                    hovertemplate='%{x}: %{y:.3f}<extra>' + company + ' (Forecast)</extra>'
                )
            )
        else:
            if len(comp_ts) == 1:
                traces.append(
                    go.Scatter(
                        x=comp_ts.index.astype(int),
                        y=comp_ts.values,
                        mode='markers',
                        name=f"{company} (Only 1 Year)",
                        marker=dict(size=8, color='gray'),
                        hovertemplate='%{x}: %{y:.3f}<extra>' + company + '</extra>'
                    )
                )

    fig_hist = go.Figure(data=traces)
    fig_hist.update_layout(
        template='plotly_white',
        title=f"ROIC forecast (Next {forecast_horizon} Years)",
        xaxis=dict(
            title='Year',
            range=[start_year, end_year + forecast_horizon],
            dtick=1,
            showgrid=True,
            gridcolor='#e1e1e1'
        ),
        yaxis=dict(
            title='ROIC',
            showgrid=True,
            gridcolor='#e1e1e1'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        margin=dict(l=60, r=30, t=170, b=50),
        hovermode='x unified'
    )

    return fig_avg, fig_pie, fig_vol, fig_scen, fig_hist

# ─── 4) RUN THE DASH APP ──────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)
