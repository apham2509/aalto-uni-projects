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

# View 1. list the average number and age of volunteers that applied, 
# and the average number of volunteers needed for each beneficiary.
def create_beneficiary_stats_view():
    create_view_query = """
    CREATE VIEW BeneficiaryStats AS
    WITH VolunteerAge AS (
        SELECT
            v.volunteerID,
            v.birthdate,
            EXTRACT(YEAR FROM AGE(v.birthdate)) AS age
        FROM Volunteer v
    ),
    RequestVolunteerCounts AS (
        SELECT
            vr.beneficiaryID,
            COUNT(a.applicationID) AS volunteer_count,
            AVG(va.age) AS average_age
        FROM VolunteerRequest vr
        JOIN Application a ON vr.requestID = a.requestID
        JOIN VolunteerAge va ON a.volunteerID = va.volunteerID
        GROUP BY vr.beneficiaryID
    ),
    AverageVolunteersNeeded AS (
        SELECT
            vr.beneficiaryID,
            AVG(vr.volunteerNumber) AS average_volunteers_needed
        FROM VolunteerRequest vr
        GROUP BY vr.beneficiaryID
    )
    SELECT
        b.beneficiaryID,
        b.name AS beneficiary_name,
        COALESCE(rvc.volunteer_count, 0) AS average_volunteers_applied,
        COALESCE(rvc.average_age, 0) AS average_age_of_volunteers,
        COALESCE(avn.average_volunteers_needed, 0) AS average_volunteers_needed
    FROM Beneficiary b
    LEFT JOIN RequestVolunteerCounts rvc ON b.beneficiaryID = rvc.beneficiaryID
    LEFT JOIN AverageVolunteersNeeded avn ON b.beneficiaryID = avn.beneficiaryID;
    """
    
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(create_view_query)
        connection.commit()

        cursor.execute("""
        SELECT 
            beneficiaryID AS beneficiary_id,
            beneficiary_name,
            CAST(ROUND(average_volunteers_applied::NUMERIC, 2) AS FLOAT) AS volunteers_applied,
            CAST(ROUND(average_age_of_volunteers::NUMERIC, 2) AS FLOAT) AS age_volunteers,
            CAST(ROUND(average_volunteers_needed::NUMERIC, 2) AS FLOAT) AS volunteers_needed
        FROM 
            BeneficiaryStats;
        """)
        result = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        print("Error while creating/viewing BeneficiaryStats view:", error)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

create_beneficiary_stats_view()



#View 2. Calculates the total number of applications and skills for each volunteer, 
#as well as the average number of skills per application. By calculating the total number 
#of applications and skills for each volunteer, along with the average number of skills per application, 
#active and skilled volunteers can be identified and their level of participation increased.

def create_volunteer_performance_view():
    create_view_query = """
    CREATE VIEW VolunteerPerformance AS
    WITH VolunteerApplicationCounts AS (
        SELECT
            v.volunteerID,
            v.name,
            COUNT(a.applicationID) AS application_count
        FROM Volunteer v
        LEFT JOIN Application a ON v.volunteerID = a.volunteerID
        GROUP BY v.volunteerID
    ),
    VolunteerSkillCounts AS (
        SELECT
            v.volunteerID,
            COUNT(vs.volunteerSkillID) AS skill_count
        FROM Volunteer v
        LEFT JOIN VolunteerSkill vs ON v.volunteerID = vs.volunteerID
        GROUP BY v.volunteerID
    )
    SELECT
        vac.volunteerID,
        vac.name AS volunteer_name,
        COALESCE(vac.application_count, 0) AS application_count,
        COALESCE(vsc.skill_count, 0) AS skill_count,
        ROUND(COALESCE(vsc.skill_count::numeric / NULLIF(vac.application_count, 0), 0), 2) AS avg_skills_per_application
    FROM VolunteerApplicationCounts vac
    LEFT JOIN VolunteerSkillCounts vsc ON vac.volunteerID = vsc.volunteerID;
    """
    
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(create_view_query)
        connection.commit()
        print("VolunteerPerformance view created successfully")
    except (Exception, psycopg2.Error) as error:
        print("Error while creating view:", error)
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

create_volunteer_performance_view()
