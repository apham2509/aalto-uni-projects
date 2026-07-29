import psycopg2
import pandas as pd

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
        print("Error while executing query", error)
    finally:
        if connection:
            cursor.close()
            connection.close()


            
# Question 1: Include the starting date and the end date in the title.
def update_request_titles():
    # Update the titles
    update_query = """
    UPDATE volunteerRequest
    SET title = title || ' (' || startdate || ' - ' || endDate || ')'
    WHERE startDate IS NOT NULL AND endDate IS NOT NULL;
    """
    execute_command(update_query)
    print("Request titles updated successfully.")
    
    # Fetch the updated rows
    select_query = """
    SELECT title FROM volunteerRequest
    """
    updated_rows = execute_query(select_query)
    print(updated_rows)
update_request_titles()

# Question 2: Find volunteers whose skill assignments match the requesting skills.
def find_matching_volunteers():
    query = """
    SELECT v.name,
           v.volunteerID,
           rs.requestID,
           COUNT(DISTINCT CASE WHEN rs.name = vs.name THEN rs.name END) AS skill_match
    FROM volunteer v
    JOIN application a ON v.volunteerID = a.volunteerID
    JOIN requestSkill rs ON a.requestID = rs.requestID
    JOIN volunteerSkill vs ON v.volunteerID = vs.volunteerID
    WHERE a.isValid = TRUE
    GROUP BY rs.requestID, v.volunteerID, v.name
    ORDER BY rs.requestID, skill_match DESC;
    """
    result_df = execute_query(query)
    print("Matching Volunteers for each request:")
    print(result_df)

find_matching_volunteers()

# Question 3: Show the missing number of volunteers needed per skill.
def show_missing_volunteers_per_skill():
    query = """
    WITH ValidApplications AS (
        SELECT *
        FROM Application
        WHERE isValid = TRUE
    ),
    VolunteerSkills AS (
        SELECT va.requestID, vs.volunteerID, vs.name AS volunteer_skill
        FROM ValidApplications va
        JOIN volunteerSkill vs ON va.volunteerID = vs.volunteerID
    ),
    RequestSkills AS (
        SELECT rs.requestID, rs.name AS request_skill, rs.minimumNeed
        FROM requestSkill rs
    ),
    MatchingSkills AS (
        SELECT rs.requestID, rs.request_skill, rs.minimumNeed, COUNT(vs.volunteerID) AS volunteer_count
        FROM RequestSkills rs
        LEFT JOIN VolunteerSkills vs ON rs.requestID = vs.requestID AND rs.request_skill = vs.volunteer_skill
        GROUP BY rs.requestID, rs.request_skill, rs.minimumNeed
    ),
    MissingVolunteers AS (
        SELECT requestID, request_skill, minimumNeed, 
               volunteer_count,
               minimumNeed - volunteer_count AS missing_volunteers
        FROM MatchingSkills
    )
    SELECT *
    FROM MissingVolunteers
    WHERE missing_volunteers > 0
    ORDER BY requestID, request_skill;
    """
    result_df = execute_query(query)
    print("Missing Volunteers per Skill:")
    print(result_df)

show_missing_volunteers_per_skill()

# Question 4: Sort requests and the beneficiaries by the highest number of priority and the closest 'register by date'.
def sort_requests_by_priority_and_date():
    query = """
    SELECT vr.requestID, vr.title, vr.priority, vr.registerByDate, b.name AS beneficiary_name
    FROM volunteerRequest vr
    JOIN Beneficiary b ON vr.beneficiaryID = b.beneficiaryID
    ORDER BY vr.priority DESC, vr.registerByDate ASC;
    """
    result_df = execute_query(query)
    print("Sorted Requests and Beneficiaries by Priority and Register Date:")
    print(result_df)

sort_requests_by_priority_and_date()

# Question 5: List requests within volunteers' range and match at least 2 skills.
def list_requests_within_volunteers_range():
    query = """
    WITH VolunteerSkills AS (
        SELECT vs.volunteerID, vs.name AS skill_name
        FROM volunteerSkill vs
    ),
    RequestSkills AS (
        SELECT rs.requestID, rs.name AS skill_name
        FROM requestSkill rs
    ),
    VolunteerRequestSkills AS (
        SELECT vs.volunteerID, rs.requestID, COUNT(DISTINCT rs.skill_name) AS skill_match_count
        FROM VolunteerSkills vs
        JOIN RequestSkills rs ON vs.skill_name = rs.skill_name
        GROUP BY vs.volunteerID, rs.requestID
    ),
    RequestsInRange AS (
        SELECT vr.volunteerID, rl.requestID
        FROM volunteerRange vr
        JOIN requestLocation rl ON vr.cityID = rl.cityID
    ),
    RequestsWithoutSkills AS (
        SELECT vr.volunteerID, rl.requestID
        FROM volunteerRange vr
        JOIN requestLocation rl ON vr.cityID = rl.cityID
        LEFT JOIN requestSkill rs ON rl.requestID = rs.requestID
        WHERE rs.requestID IS NULL
    ),
    QualifiedRequests AS (
        SELECT rir.volunteerID, rir.requestID
        FROM RequestsInRange rir
        LEFT JOIN VolunteerRequestSkills vrs ON rir.volunteerID = vrs.volunteerID AND rir.requestID = vrs.requestID
        WHERE vrs.skill_match_count >= 2
        UNION
        SELECT * FROM RequestsWithoutSkills
    )
    SELECT q.volunteerID, q.requestID
    FROM QualifiedRequests q
    ORDER BY q.volunteerID, q.requestID;
    """
    result_df = execute_query(query)
    print("Requests within Volunteers' Range:")
    print(result_df)

list_requests_within_volunteers_range()

# Question 6
# Question 6
def list_matching_requests_for_volunteers():
    query = r"""
    DROP TABLE IF EXISTS InterestKeyword CASCADE;
    CREATE TABLE InterestKeyword (
        interest_name TEXT PRIMARY KEY,
        keyword TEXT NOT NULL
    );
    
    INSERT INTO InterestKeyword (interest_name, keyword) VALUES
    ('FoodHelp', 'food help'),
    ('GuideAndTeach', 'guide and teach'),
    ('CollectDonations', 'collect donations'),
    ('ImmigrantSupport', 'immigrant support'),
    ('PromoteWellbeing', 'promote wellbeing'),
    ('HelpInCrisis', 'help in crisis'),
    ('WorkWithYoung', 'work with young'),
    ('OrganiseActivities', 'organise activities'),
    ('WorkInMulticulturalEnvironment', 'work in multicultural environment'),
    ('FirstAid', 'first aid'),
    ('WorkWithElderly', 'work with elderly'),
    ('WorkInTeam', 'work in team');
    
    SELECT
        v.volunteerID,
        vr.requestID,
        vr.title,
        vr.registerByDate
    FROM
        Volunteer v
    JOIN
        VolunteerInterest vi ON v.volunteerID = vi.volunteerID
    JOIN
        InterestKeyword ik ON vi.name = ik.interest_name
    JOIN
        volunteerRequest vr ON vr.title ILIKE '%' || ik.keyword || '%'
    WHERE
        vr.registerByDate >= CURRENT_DATE;
    """

    result_df = execute_query(query)
    print("Requests where title matches volunteers' area of interest and are still available to register:")
    print(result_df)

list_matching_requests_for_volunteers()

# Question 7
def list_volunteers_outside_location_range():
    query = """
    WITH VolunteersApplied AS (
        SELECT 
            a.requestID, 
            v.volunteerID, 
            v.name, 
            v.email, 
            v.readiness
        FROM Application a
        JOIN Volunteer v ON a.volunteerID = v.volunteerID
        WHERE a.isValid = TRUE
    ),
    RequestLocations AS (
        SELECT 
            rl.requestID, 
            rl.cityID AS request_cityID
        FROM requestLocation rl
    ),
    VolunteerRanges AS (
        SELECT 
            vr.volunteerID, 
            vr.cityID AS volunteer_cityID
        FROM volunteerRange vr
    ),
    VolunteersOutOfRange AS (
        SELECT 
            va.requestID, 
            va.volunteerID, 
            va.name, 
            va.email, 
            va.readiness
        FROM VolunteersApplied va
        LEFT JOIN VolunteerRanges vr ON va.volunteerID = vr.volunteerID
        LEFT JOIN RequestLocations rl ON va.requestID = rl.requestID AND vr.volunteer_cityID = rl.request_cityID
        WHERE rl.requestID IS NULL
    )
    SELECT 
        requestID, 
        volunteerID, 
        name, 
        email, 
        readiness
    FROM VolunteersOutOfRange
    ORDER BY readiness DESC;
    """
    
    result_df = execute_query(query)
    print("Request IDs and volunteers who applied to them but not within the location range of request ordered by readiness to travel:")
    print(result_df)

list_volunteers_outside_location_range()

# Question 8
def list_skills_by_priority():
    query = """
    SELECT rs.name, r.priority
    FROM requestSkill rs
    NATURAL JOIN volunteerRequest r
    ORDER BY priority DESC;
    """
    
    result_df = execute_query(query)
    print("Skills based on priority:")
    print(result_df)

list_skills_by_priority()


# Question 9
# This provides an analysis of skill demand by calculating the number of requests each skill is associated with and the average number of volunteers needed 
# for those requests. The results are sorted in descending order of the number of requests and then by the average skill demand. This can be used to see
# what are the most demanded skills
def query_skill_demand():
    query = """
    SELECT
        s.name AS skill_name,
        COUNT(DISTINCT rs.requestID) AS num_requests,
        ROUND(AVG(rs.minimumNeed), 2) AS avg_skill_demand
    FROM skill s
    LEFT JOIN requestSkill rs ON s.name = rs.name
    GROUP BY s.name
    ORDER BY num_requests DESC, avg_skill_demand DESC;
    """
    result_df = execute_query(query)
    print("Skill Demand Analysis:")
    print(result_df)

query_skill_demand()

# Question 10
# This lists the top ten volunteers that have submitted the most requests, which can be used to reward the most active volunteers, in order to motivate them 
# to continue working.
def query_most_active_volunteers():
    query = """
    SELECT
        v.volunteerID AS volunteer_id,
        v.name AS volunteer_name,
        COUNT(a.applicationID) AS number_of_applications
    FROM volunteer v
    JOIN application a ON v.volunteerID = a.volunteerID
    GROUP BY v.volunteerID, v.name
    ORDER BY number_of_applications DESC
    LIMIT 10;
    """
    result_df = execute_query(query)
    print("Most active volunteers:")
    print(result_df)

query_most_active_volunteers()

# Question 11
# This lists requests that have less applications than needed amount of volunteers. This can be used to identify gaps in volunteer recruitment and 
# to take corrective actions, such as promoting these requests more actively or reassessing the requirements.
def query_unfulfilled_requests():
    query = """
    SELECT
        vr.requestID AS request_id,
        vr.title AS request_name,
        vr.volunteerNumber AS number_needed,
        COUNT(a.applicationID) AS number_of_applications
    FROM volunteerRequest vr
    LEFT JOIN application a ON vr.requestID = a.requestID
    GROUP BY vr.requestID, vr.title, vr.volunteerNumber
    HAVING COUNT(a.applicationID) < vr.volunteerNumber
    ORDER BY vr.requestID;
    """
    result_df = execute_query(query)
    print("Unfulfilled requests:")
    print(result_df)

query_unfulfilled_requests()

# Question 12
# This lists the volunteers who have never applied to any requests, which can clog up the system for no need. These people can either be given more incentive to work
# or be deleted from the system if they do not plan on submitting any requests.
def query_volunteers_without_applications():
    query = """
    SELECT
        v.volunteerID AS volunteer_id,
        v.name AS volunteer_name,
        v.email AS contact_info
    FROM Volunteer v
    LEFT JOIN Application a ON v.volunteerID = a.volunteerID
    WHERE a.applicationID IS NULL
    ORDER BY v.volunteerID;
    """
    result_df = execute_query(query)
    print("Volunteers without applications:")
    print(result_df)

query_volunteers_without_applications()
