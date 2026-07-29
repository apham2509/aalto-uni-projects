import pandas as pd
import plotly.express as px
from dash import Output, Input, html
import dash_bootstrap_components as dbc


def register_callbacks(app, volunteer_request_df, volunteer_df, beneficiary_df, city_df, request_location_df,
                       volunteer_skill_df, volunteer_interest_df, application_df):
    @app.callback(
        [
            Output('overview-metrics', 'children'),
            Output('volunteers-by-city', 'figure'),
            Output('age-distribution', 'figure'),
            Output('requests-by-priority', 'figure'),
            Output('requests-by-city', 'figure'),
            Output('requests-over-time', 'figure'),
            Output('skills-distribution', 'figure'),
            Output('interests-distribution', 'figure'),
            Output('applications-per-request', 'figure'),
            Output('valid-invalid-applications', 'figure')
        ],
        [
            Input('date-picker-range', 'start_date'),
            Input('date-picker-range', 'end_date'),
            Input('request-id-dropdown', 'value'),
            Input('beneficiary-dropdown', 'value')
        ]
    )
    def update_dashboard(start_date, end_date, selected_request_ids, selected_beneficiaries):
        # Filter data based on date range
        filtered_requests = volunteer_request_df[
            (volunteer_request_df['startdate'] >= pd.to_datetime(start_date)) &
            (volunteer_request_df['enddate'] <= pd.to_datetime(end_date))
            ]

        # Filter data based on selected request IDs
        if selected_request_ids:
            filtered_requests = filtered_requests[filtered_requests['requestid'].isin(selected_request_ids)]

        # Filter data based on selected beneficiaries
        if selected_beneficiaries:
            filtered_requests = filtered_requests[filtered_requests['beneficiaryid'].isin(selected_beneficiaries)]

        # Filter applications based on date range and selected request IDs
        filtered_applications = application_df[
            (application_df['time'] >= pd.to_datetime(start_date)) &
            (application_df['time'] <= pd.to_datetime(end_date))
            ]

        if selected_request_ids:
            filtered_applications = filtered_applications[filtered_applications['requestid'].isin(selected_request_ids)]

        if selected_beneficiaries:
            filtered_applications = filtered_applications[
                filtered_applications['requestid'].isin(filtered_requests['requestid'])]

        # Join with volunteer data to get volunteer details
        filtered_volunteers = filtered_applications.merge(volunteer_df, on='volunteerid')

        # Drop duplicates based on volunteerID to get unique volunteers
        unique_volunteers = filtered_volunteers.drop_duplicates(subset=['volunteerid'])

        # Filter beneficiaries based on the filtered requests
        filtered_beneficiary_ids = filtered_requests['beneficiaryid'].unique()
        filtered_beneficiaries = beneficiary_df[beneficiary_df['beneficiaryid'].isin(filtered_beneficiary_ids)]

        total_volunteers = len(unique_volunteers)
        total_beneficiaries = len(filtered_beneficiaries)
        total_requests = len(filtered_requests)
        total_active_requests = len(filtered_requests[filtered_requests['enddate'] >= pd.to_datetime('today')])
        total_applications = len(filtered_applications)
        total_valid_applications = len(filtered_applications[filtered_applications['isvalid']])

        overview_metrics = dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H4('Total Volunteers', style={'fontSize': '0.9rem'}),
                html.H2(total_volunteers, style={'fontSize': '2rem'})
            ]), className="mb-2"), width=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H4('Total Beneficiaries', style={'fontSize': '0.9rem'}),
                html.H2(total_beneficiaries, style={'fontSize': '2rem'})
            ]), className="mb-2"), width=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H4('Total Active Requests / Total Requests', style={'fontSize': '0.9rem'}),
                html.H2(f"{total_active_requests} / {total_requests}", style={'fontSize': '2rem'})
            ]), className="mb-2"), width=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H4('Total Valid Applications / Total Applications', style={'fontSize': '0.85rem'}),
                html.H2(f"{total_valid_applications} / {total_applications}", style={'fontSize': '2rem'})
            ]), className="mb-2"), width=3)
        ])

        # Volunteers per city
        city_volunteer_count = unique_volunteers['cityid'].value_counts().reset_index()
        city_volunteer_count.columns = ['cityid', 'volunteer_count']
        city_volunteer_count = city_volunteer_count.merge(city_df, on='cityid')
        fig_volunteers_by_city = px.bar(city_volunteer_count, x='name', y='volunteer_count',
                                        title='Number of Volunteers per City')

        # Age distribution of volunteers
        unique_volunteers['age'] = (pd.to_datetime('today') - unique_volunteers['birthdate']).dt.days // 365
        fig_age_distribution = px.histogram(unique_volunteers, x='age', title='Age Distribution of Volunteers')

        # Requests by priority
        priority_count = filtered_requests['priority'].value_counts().reset_index()
        priority_count.columns = ['priority', 'count']
        fig_requests_by_priority = px.bar(priority_count, x='priority', y='count', title='Number of Requests by Priority')

        # Requests by city
        filtered_request_ids = filtered_requests['requestid'].unique()
        filtered_request_locations = request_location_df[request_location_df['requestid'].isin(filtered_request_ids)]
        request_city_count = filtered_request_locations['cityid'].value_counts().reset_index()
        request_city_count.columns = ['cityid', 'request_count']
        request_city_count = request_city_count.merge(city_df, on='cityid')
        fig_requests_by_city = px.bar(request_city_count, x='name', y='request_count', title='Number of Requests by City')

        # Requests and Applications over time
        filtered_requests['startdate'] = pd.to_datetime(filtered_requests['startdate'])
        filtered_applications['time'] = pd.to_datetime(filtered_applications['time'])

        request_over_time = filtered_requests.groupby(filtered_requests['startdate'].dt.to_period('D')).size().reset_index(name='count')
        request_over_time['time'] = request_over_time['startdate'].dt.to_timestamp()
        request_over_time['Type'] = 'Request'

        application_over_time = filtered_applications.groupby(filtered_applications['time'].dt.to_period('D')).size().reset_index(name='count')
        application_over_time['time'] = application_over_time['time'].dt.to_timestamp()
        application_over_time['Type'] = 'Application'

        combined_over_time = pd.concat([request_over_time[['time', 'count', 'Type']], application_over_time[['time', 'count', 'Type']]])
        combined_over_time = combined_over_time.sort_values(by='time')

        fig_requests_over_time = px.line(combined_over_time, x='time', y='count', color='Type', title='Requests and Applications Over Time')

        # Skills distribution
        volunteer_skills_filtered = volunteer_skill_df[volunteer_skill_df['volunteerid'].isin(unique_volunteers['volunteerid'])]
        skill_count = volunteer_skills_filtered['name'].value_counts().reset_index()
        skill_count.columns = ['skill', 'count']
        fig_skills_distribution = px.bar(skill_count, x='skill', y='count', title='Distribution of Skills among Volunteers')

        # Interests distribution
        volunteer_interests_filtered = volunteer_interest_df[volunteer_interest_df['volunteerid'].isin(unique_volunteers['volunteerid'])]
        interest_count = volunteer_interests_filtered['name'].value_counts().reset_index()
        interest_count.columns = ['interest', 'count']
        fig_interests_distribution = px.bar(interest_count, x='interest', y='count', title='Distribution of Interests among Volunteers')

        # Applications per request
        application_count = filtered_applications.groupby('requestid').size().reset_index(name='application_count')
        application_count = application_count.merge(volunteer_request_df[['requestid', 'title_request']], on='requestid')
        application_count = application_count.groupby('title_request')['application_count'].sum().reset_index()
        fig_applications_per_request = px.bar(application_count, x='title_request', y='application_count', title='Number of Applications per Request')
        fig_applications_per_request.update_traces(marker=dict(pattern_shape=None))

        # Valid vs Invalid applications
        filtered_applications['isvalid'] = filtered_applications['isvalid'].map({True: 'Valid', False: 'Invalid'})
        valid_count = filtered_applications['isvalid'].value_counts().reset_index()
        valid_count.columns = ['isvalid', 'count']
        fig_valid_invalid_applications = px.pie(valid_count, names='isvalid', values='count', title='Valid vs Invalid Applications')

        return (
            overview_metrics,
            fig_volunteers_by_city.to_dict(),
            fig_age_distribution.to_dict(),
            fig_requests_by_priority.to_dict(),
            fig_requests_by_city.to_dict(),
            fig_requests_over_time.to_dict(),
            fig_skills_distribution.to_dict(),
            fig_interests_distribution.to_dict(),
            fig_applications_per_request.to_dict(),
            fig_valid_invalid_applications.to_dict()
        )

