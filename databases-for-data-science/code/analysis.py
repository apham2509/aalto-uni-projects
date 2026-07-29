import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

def get_db_connection():
    return psycopg2.connect(
        database="group_12_2024",
        user="group_12_2024",
        password="73JKSEnw6YJZ",
        host="dbcourse.cs.aalto.fi",
        port="5432"
    )

def execute_query(query):
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(result, columns=colnames)
        return df
    except (Exception, psycopg2.Error) as error:
        print("Error while executing query:", error)
    finally:
        if connection:
            connection.close()

#Analysis 1
#Query to get number of volunteers available by city
query_volunteers_available = """
SELECT c.cityID, c.name, COUNT(vr.volunteerID) as volunteers_available
FROM City c
JOIN volunteerRange vr ON c.cityID = vr.cityID
GROUP BY c.cityID, c.name;
"""
df_volunteers_available = execute_query(query_volunteers_available)

#Query to get number of unique volunteers who applied for a request in each city
query_volunteers_applied = """
SELECT c.cityID, c.name, COUNT(DISTINCT a.volunteerID) as volunteers_applied
FROM City c
JOIN requestLocation rl ON c.cityID = rl.cityID
JOIN volunteerRequest vr ON rl.requestID = vr.requestID
JOIN Application a ON vr.requestID = a.requestID
GROUP BY c.cityID, c.name;
"""
df_volunteers_applied = execute_query(query_volunteers_applied)

#Merge dataframes
city_volunteer_data = pd.merge(df_volunteers_available, df_volunteers_applied, on=['cityid', 'name'], how='outer').fillna(0)

#Sort the data to highlight the top and bottom cities
city_volunteer_data_sorted = city_volunteer_data.sort_values(by='volunteers_available', ascending=False)

#Plotting the data with side-by-side bars
fig, ax = plt.subplots(figsize=(12, 8))
bar_width = 0.35
index = range(len(city_volunteer_data_sorted))
bar1 = ax.bar(index, city_volunteer_data_sorted['volunteers_available'], bar_width, label='Volunteers Available')
bar2 = ax.bar([i + bar_width for i in index], city_volunteer_data_sorted['volunteers_applied'], bar_width, label='Volunteers Applied')

#Adding titles and labels
ax.set_xlabel('City')
ax.set_ylabel('Number of Volunteers')
ax.set_title('Number of Volunteers Available vs. Volunteers Applied by City')
ax.set_xticks([i + bar_width / 2 for i in index])
ax.set_xticklabels(city_volunteer_data_sorted['name'], rotation=45, ha='right')
ax.legend()

#Show the plot
plt.tight_layout()
plt.show()

#Top 2 and bottom 2 cities
top_2_cities = city_volunteer_data_sorted.head(2)
bottom_2_cities = city_volunteer_data_sorted.tail(2)

#Show result
top_2_result = "\n".join([f"{row['name']} (City ID {row['cityid']}): {row['volunteers_available']} volunteers available, {row['volunteers_applied']} volunteers applied" for _, row in top_2_cities.iterrows()])
bottom_2_result = "\n".join([f"{row['name']} (City ID {row['cityid']}): {row['volunteers_available']} volunteers available, {row['volunteers_applied']} volunteers applied" for _, row in bottom_2_cities.iterrows()])
result = f"""Top 2 Cities with the Most Volunteers: 
{top_2_result}
Bottom 2 Cities with the Least Volunteers: 
{bottom_2_result}"""
print(result)

#Analysis 2
# Retrieve data from the database
volunteers_query = "SELECT * FROM Volunteer"
volunteer_skills_query = "SELECT * FROM volunteerSkill"
volunteer_interests_query = "SELECT * FROM volunteerInterest"
volunteer_ranges_query = "SELECT * FROM volunteerRange"
requests_query = "SELECT * FROM volunteerRequest"
request_skills_query = "SELECT * FROM requestSkill"
request_locations_query = "SELECT * FROM requestLocation"
applications_query = "SELECT * FROM Application"

volunteers = execute_query(volunteers_query)
volunteer_skills = execute_query(volunteer_skills_query)
volunteer_interests = execute_query(volunteer_interests_query)
volunteer_ranges = execute_query(volunteer_ranges_query)
requests = execute_query(requests_query)
request_skills = execute_query(request_skills_query)
request_locations = execute_query(request_locations_query)
applications = execute_query(applications_query)

# Maximum travel readiness value for normalization
max_readiness = volunteers['readiness'].max()

# Prepare dictionaries for quick lookups
volunteer_skill_dict = volunteer_skills.groupby('volunteerid')['name'].apply(list).to_dict()
volunteer_interest_dict = volunteer_interests.groupby('volunteerid')['name'].apply(list).to_dict()
volunteer_range_dict = volunteer_ranges.groupby('volunteerid')['cityid'].apply(list).to_dict()
request_skill_dict = request_skills.groupby('requestid')['name'].apply(list).to_dict()
request_location_dict = request_locations.groupby('requestid')['cityid'].apply(list).to_dict()

# Function to calculate the matching score (The scoring system is in Gitlab doc folder under the name "scoring_system_analysis_2.pdf")
def calculate_matching_score(volunteer, request_id):
    volunteer_id = volunteer['volunteerid']
    readiness = volunteer['readiness']

    # Skills Match Score
    required_skills = request_skill_dict.get(request_id, [])
    volunteer_skills = volunteer_skill_dict.get(volunteer_id, [])
    if request_id not in request_skill_dict:
        skill_score = 40
    else:
        required_skills = request_skill_dict.get(request_id, [])
        volunteer_skills = volunteer_skill_dict.get(volunteer_id, [])
        skill_score = 40 if set(required_skills).intersection(set(volunteer_skills)) else 0

    # Travel Readiness Score
    travel_readiness_score = (1 - (readiness / max_readiness)) * 20

    # Volunteer Range Score
    request_cities = request_location_dict.get(request_id, [])
    volunteer_cities = volunteer_range_dict.get(volunteer_id, [])
    range_score = 20 if set(request_cities).intersection(set(volunteer_cities)) else 0

    # Interest Alignment Score
    volunteer_interests = volunteer_interest_dict.get(volunteer_id, [])
    matching_interests = set(required_skills).intersection(set(volunteer_interests))
    interest_score = (len(matching_interests) / len(required_skills)) * 20 if required_skills else 0

    # Total Score
    total_score = skill_score + travel_readiness_score + range_score + interest_score
    return total_score

# Calculate scores for each valid application and store the results
application_scores = []
for _, application in applications.iterrows():
    if application['isvalid']:
        volunteer_id = application['volunteerid']
        request_id = application['requestid']
        volunteer = volunteers[volunteers['volunteerid'] == volunteer_id].iloc[0]
        score = calculate_matching_score(volunteer, request_id)
        application_scores.append((request_id, volunteer_id, volunteer['name'], score))

# Convert to DataFrame for easy manipulation
scores_df = pd.DataFrame(application_scores, columns=['requestid', 'volunteerid', 'volunteer_name', 'score'])

# Find top 5 candidates for each request
top_candidates = scores_df.sort_values(by=['requestid', 'score'], ascending=[True, False]).groupby('requestid').head(5)
print(top_candidates)

#Analysis 3
# Query to get valid applications
applications_query = """
SELECT applicationID, requestID, volunteerID, time, isValid
FROM Application
WHERE isValid = TRUE;
"""
valid_applications_df = execute_query(applications_query)

# Query to get volunteer requests
volunteer_requests_query = """
SELECT requestID, startDate, endDate
FROM volunteerRequest;
"""
volunteer_requests_df = execute_query(volunteer_requests_query)

# Convert date columns to datetime format
valid_applications_df['time'] = pd.to_datetime(valid_applications_df['time'])
volunteer_requests_df['startdate'] = pd.to_datetime(volunteer_requests_df['startdate'])
volunteer_requests_df['enddate'] = pd.to_datetime(volunteer_requests_df['enddate'])

# Extract the month from the 'time' column in the applications dataframe
valid_applications_df['month'] = valid_applications_df['time'].dt.month
print(valid_applications_df['month'])

# Extract the month from the 'startDate' column in the volunteer requests dataframe
volunteer_requests_df['month'] = volunteer_requests_df['startdate'].dt.month
print(volunteer_requests_df['month'])

# Count the number of valid applications and requests for each month
applications_count_by_month = valid_applications_df.groupby('month').size()
requests_count_by_month = volunteer_requests_df.groupby('month').size()

# Combine the counts into a single dataframe
counts_by_month = pd.DataFrame({
    'applications': applications_count_by_month,
    'requests': requests_count_by_month
}).reset_index().rename(columns={'index': 'month'})
print(counts_by_month)

# Calculate the difference between requests and applications
counts_by_month['difference_requests_application'] = counts_by_month['requests'] - counts_by_month['applications']
counts_by_month['difference_application_request'] = counts_by_month['applications'] - counts_by_month['requests']
print(counts_by_month)

# Plot the data for better visualization
plt.figure(figsize=(14, 7))
# Plot applications and requests
plt.plot(counts_by_month['month'], counts_by_month['applications'], label='Applications', marker='o')
plt.plot(counts_by_month['month'], counts_by_month['requests'], label='Requests', marker='o')
# Plot the differences
plt.plot(counts_by_month['month'], counts_by_month['difference_application_request'], label='Difference', marker='o', linestyle='--')
# Add labels and legend
plt.xlabel('Month')
plt.ylabel('Count')
plt.title('Valid Volunteer Applications and Requests by Month')
plt.xticks(range(1, 13),
           ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
plt.legend()
plt.grid(True)
# Show the plot
plt.show()

# Plot the data for better visualization
plt.figure(figsize=(14, 7))
# Plot applications and requests
plt.plot(counts_by_month['month'], counts_by_month['applications'], label='Applications', marker='o')
plt.plot(counts_by_month['month'], counts_by_month['requests'], label='Requests', marker='o')
# Plot the differences
plt.plot(counts_by_month['month'], counts_by_month['difference_requests_application'], label='Difference', marker='o', linestyle='--')
# Add labels and legend
plt.xlabel('Month')
plt.ylabel('Count')
plt.title('Valid Volunteer Requests and Applications by Month')
plt.xticks(range(1, 13),
           ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
plt.legend()
plt.grid(True)
# Show the plot
plt.show()

# Seasonal Trend Analysis
print("Seasonal Trend Analysis")
# Display the counts by month for inspection
print(counts_by_month)
print(' The data shows a seasonal trend in volunteer applications, '
      'with a significant increase during the summer months (June, July, and August). '
      'The peak occurs in July with 307 applications, while the lowest point is in March with 127 applications.'
      'The number of requests does not show as clear a seasonal pattern as the applications. '
      'There is a slight increase in requests during the summer and early autumn months (June to September).'
      'The highest number of requests is in August and September, both with 43 requests, while the lowest is in February with 19 requests.')

# Correlation Analysis
correlation_applications = pearsonr(counts_by_month['month'], counts_by_month['applications'])
correlation_requests = pearsonr(counts_by_month['month'], counts_by_month['requests'])

print("\nCorrelation Analysis")
print(f"Correlation between month and applications: {correlation_applications[0]}, p-value: {correlation_applications[1]}")
print('Interpretation: There is a positive but weak correlation between the month and the number of applications. '
      'The p-value is greater than 0.05, indicating that the correlation is not statistically significant. '
      'This suggests that while there is an increase in applications during certain months, '
      'the trend is not strong enough to be deemed significant.'
)
print(f"Correlation between month and requests: {correlation_requests[0]}, p-value: {correlation_requests[1]}")
print('Interpretation: There is a moderate positive correlation between the month and the number of requests. '
      'The p-value is less than 0.05, indicating that the correlation is statistically significant. '
      'This suggests that there is a significant trend of increased requests as the year progresses, '
      'especially during the summer and early autumn months.')

# Display the result
print("Months with the most and least valid applications:")
most_applications_month = counts_by_month.loc[counts_by_month['applications'].idxmax()]
least_applications_month = counts_by_month.loc[counts_by_month['applications'].idxmin()]
print(f"Most applications: {most_applications_month}")
print(f"Least applications: {least_applications_month}")

print("\nMonths with the most and least valid requests:")
most_requests_month = counts_by_month.loc[counts_by_month['requests'].idxmax()]
least_requests_month = counts_by_month.loc[counts_by_month['requests'].idxmin()]
print(f"Most requests: {most_requests_month}")
print(f"Least requests: {least_requests_month}")

#Analysis 4:
"""This analysis is to understand the distribution and readiness of volunteers across different cities and to 
investigate if there is any relationship between the number of volunteers in a city and their readiness to travel."""
# SQL query to fetch volunteer and city data
query = """
SELECT c.name AS city, COUNT(v.volunteerID) AS volunteer_count, AVG(v.readiness) AS average_readiness
FROM Volunteer v
JOIN City c ON v.cityID = c.cityID
GROUP BY c.name
ORDER BY c.name;
"""

# Execute the query
volunteer_data = execute_query(query)

# Convert columns to numeric types
volunteer_data['volunteer_count'] = pd.to_numeric(volunteer_data['volunteer_count'])
volunteer_data['average_readiness'] = pd.to_numeric(volunteer_data['average_readiness'])

# Perform correlation analysis
correlation, _ = pearsonr(volunteer_data['volunteer_count'], volunteer_data['average_readiness'])
print(f'Correlation between number of volunteers and average readiness: {correlation:.2f}')
print(f'The correlation coefficient between the number of volunteers and the average readiness is approximately {correlation:.2f}.'
      f'This indicates a moderate negative correlation, which means that as the number of volunteers in a city increases, '
      f'the average readiness score tends to decrease (which is better since lower readiness scores indicate faster preparation times).')

# Plotting the number of volunteers and average readiness in each city on the same graph
fig, ax1 = plt.subplots(figsize=(14, 7))

# Plotting the number of volunteers
color = 'tab:blue'
ax1.set_xlabel('City')
ax1.set_ylabel('Number of Volunteers', color=color)
ax1.bar(volunteer_data['city'], volunteer_data['volunteer_count'], color=color, alpha=0.6, label='Number of Volunteers')
ax1.tick_params(axis='y', labelcolor=color)
ax1.legend(loc='upper left')

# Creating a secondary y-axis to plot the average readiness
ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Average Readiness (lower is better)', color=color)
ax2.plot(volunteer_data['city'], volunteer_data['average_readiness'], color=color, marker='o', linestyle='-', label='Average Readiness')
ax2.tick_params(axis='y', labelcolor=color)
ax2.legend(loc='upper right')

# Adding the title and rotating x-axis labels for better readability
plt.title('Number of Volunteers and Average Travel Readiness in Each City')
plt.xticks(rotation=45, ha='right')

# Display the plot
plt.show()