import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import time

def get_db_connection():
    return psycopg2.connect(
        database="group_12_2024",
        user="group_12_2024",
        password="73JKSEnw6YJZ",
        host="dbcourse.cs.aalto.fi",
        port="5432"
    )

# Execute a query that returns results
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
        print("Error while executing query", error)
    finally:
        if connection:
            cursor.close()
            connection.close()

# Execute a query that does not return results (INSERT, UPDATE, DELETE)
def execute_non_query(query):
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        print("Executed successfully:", query)
    except (Exception, psycopg2.Error) as error:
        print("Error while executing non-query", error)
    finally:
        if connection:
            cursor.close()
            connection.close()

# Fetch all active volunteer requests
def fetch_open_requests():
    query = """
    SELECT r.requestID, r.title, r.volunteerNumber, rs.name as skill_name, rs.minimumNeed
    FROM volunteerRequest r
    JOIN requestSkill rs ON r.requestID = rs.requestID
    WHERE r.endDate >= CURRENT_DATE AND r.priority > 0
    """
    df = execute_query(query)
    print("Open Requests Columns:", df.columns)
    print(df.head())
    return df
fetch_open_requests()

# Fetch all available volunteers
def fetch_available_volunteers():
    query = """
    SELECT v.volunteerID, v.name, vs.name as skill_name
    FROM Volunteer v
    JOIN volunteerSkill vs ON v.volunteerID = vs.volunteerID
    WHERE v.readiness >= 1
    """
    df = execute_query(query)
    print("Available Volunteers Columns:", df.columns)
    print(df.head())
    return df

fetch_available_volunteers()

# Match volunteers to requests based on skills and needs
def match_volunteers_to_requests():
    requests = fetch_open_requests()
    volunteers = fetch_available_volunteers()
    
    matches = []
    max_matches =50 # Limit the number of matches to 50
    for _, req in requests.iterrows(): # Iterate through each request to find suitable volunteers
        if len(matches) >= max_matches: # Stop if the maximum number of matches is reached
            break
     # Extract necessary details from the current request
        req_id = req['requestid']
        req_skill = req['skill_name']
        minimum_need = req['minimumneed']

        # Find suitable volunteers with the required skill
        suitable_volunteers = volunteers[volunteers['skill_name'] == req_skill]
        
        # Check if there are enough suitable volunteers
        if not suitable_volunteers.empty and len(suitable_volunteers) >= minimum_need:
             # Iterate through the suitable volunteers and create matches
            for _, vol in suitable_volunteers.iterrows():
                vol_id = vol['volunteerid']

                 # Insert potential match into the DB
                potential_match_query = f"""
                INSERT INTO PotentialMatches (volunteerID, requestID, matchDate)
                VALUES ('{vol_id}', {req_id}, '{datetime.now().date()}')
                """
                execute_non_query(potential_match_query)
                
                matches.append((vol_id, req_id))
                if len(matches) >= minimum_need:
                    break
    
    return matches

# Create the PotentialMatches table (if it  not already exists)
create_potential_matches_table_query = """
CREATE TABLE IF NOT EXISTS PotentialMatches (
    matchID SERIAL PRIMARY KEY,
    volunteerID TEXT NOT NULL,
    requestID INT NOT NULL,
    matchDate DATE NOT NULL,
    FOREIGN KEY (volunteerID) REFERENCES Volunteer(volunteerID),
    FOREIGN KEY (requestID) REFERENCES volunteerRequest(requestID)
);
"""
 # Create the table
execute_non_query(create_potential_matches_table_query)

#Matching process + display the results
matched_volunteers = match_volunteers_to_requests()
print("Matched Volunteers to Requests:", matched_volunteers)

def fetch_potential_matches():
    query = "SELECT * FROM PotentialMatches"
    df = execute_query(query)
    print("Potential Matches:")
    print(df)
    return df
fetch_potential_matches()

# Function to periodically match volunteers to requests
def dynamic_matching_scheduler():
    while True:
        matched_volunteers = match_volunteers_to_requests()
        print("Matched Volunteers to Requests:", matched_volunteers)
        time.sleep(3600) # Wait for 1 hour before running again

# Uncomment to activate periodic updating
# dynamic_matching_scheduler()