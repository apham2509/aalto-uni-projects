from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
from callbacks import register_callbacks
from data_fetcher import fetch_data

# Fetch data
data_frames = fetch_data()

# Extract DataFrames
city_df = data_frames['city']
volunteer_df = data_frames['volunteer']
beneficiary_df = data_frames['beneficiary']
volunteer_request_df = data_frames['volunteer_request']
request_skill_df = data_frames['request_skill']
request_location_df = data_frames['request_location']
application_df = data_frames['application']
volunteer_skill_df = data_frames['volunteer_skill']
skill_df = data_frames['skill']
interest_df = data_frames['interest']
volunteer_interest_df = data_frames['volunteer_interest']
volunteer_range_df = data_frames['volunteer_range']

# Convert date columns to datetime
volunteer_request_df['startdate'] = pd.to_datetime(volunteer_request_df['startdate'])
volunteer_request_df['enddate'] = pd.to_datetime(volunteer_request_df['enddate'])
volunteer_df['birthdate'] = pd.to_datetime(volunteer_df['birthdate'])
application_df['time'] = pd.to_datetime(application_df['time'])

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Volunteer Management Dashboard", style={'fontWeight': 'bold', 'textAlign': 'center'}), className="mb-4")
    ]),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label('Select Date Range', style={'marginRight': '10px', 'fontSize': '12px'}),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    start_date=volunteer_request_df['startdate'].min().date(),
                    end_date=volunteer_request_df['enddate'].max().date(),
                    display_format='YYYY-MM-DD',
                    style={'fontSize': '10px', 'height': '35px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center'}),
        ], width=4),
        dbc.Col([
            html.Div([
                html.Label('Select Request ID', style={'marginRight': '10px', 'fontSize': '12px'}),
                dcc.Dropdown(
                    id='request-id-dropdown',
                    options=[{'label': f"Request {rid}", 'value': rid} for rid in volunteer_request_df['requestid'].unique()],
                    multi=True,
                    placeholder="Select one or more request IDs",
                    style={'width': '100%', 'height': '45px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], width=4),
        dbc.Col([
            html.Div([
                html.Label('Select Beneficiary', style={'marginRight': '10px', 'fontSize': '12px'}),
                dcc.Dropdown(
                    id='beneficiary-dropdown',
                    options=[{'label': name, 'value': bid} for bid, name in zip(beneficiary_df['beneficiaryid'], beneficiary_df['name'])],
                    multi=True,
                    placeholder="Select one or more beneficiaries",
                    style={'width': '100%', 'height': '45px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], width=4)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(html.Div(id='overview-metrics'), width=12, style={'textAlign': 'center'})
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='volunteers-by-city'), width=6),
        dbc.Col(dcc.Graph(id='age-distribution'), width=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='requests-by-priority'), width=6),
        dbc.Col(dcc.Graph(id='requests-by-city'), width=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='requests-over-time'), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='skills-distribution'), width=6),
        dbc.Col(dcc.Graph(id='interests-distribution'), width=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='applications-per-request'), width=6),
        dbc.Col(dcc.Graph(id='valid-invalid-applications'), width=6)
    ])
])

register_callbacks(app, volunteer_request_df, volunteer_df, beneficiary_df, city_df, request_location_df, volunteer_skill_df, volunteer_interest_df, application_df)

if __name__ == '__main__':
    app.run_server(debug=True)
