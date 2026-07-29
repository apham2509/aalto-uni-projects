import pandas as pd
import psycopg2
import re

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

def execute_command(command):
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(command)
        connection.commit()
    except (Exception, psycopg2.Error) as error:
        print("Error while executing command", error)
    finally:
        if connection:
            cursor.close()
            connection.close()


def fetch_data():
    # Add the new column
    add_column_command = "ALTER TABLE volunteerRequest ADD COLUMN IF NOT EXISTS title_request TEXT;"
    execute_command(add_column_command)

    # Update the new column with formatted title
    update_column_command = """
    UPDATE volunteerRequest 
    SET title_request = INITCAP(REGEXP_REPLACE(title, 'needed|\\(.*\\)', '', 'gi'));
    """
    execute_command(update_column_command)

    queries = {
        "city": "SELECT * FROM City",
        "volunteer": "SELECT * FROM Volunteer",
        "beneficiary": "SELECT * FROM Beneficiary",
        "volunteer_request": "SELECT * FROM volunteerRequest",
        "request_skill": "SELECT * FROM requestSkill",
        "request_location": "SELECT * FROM requestLocation",
        "application": "SELECT * FROM Application",
        "volunteer_skill": "SELECT * FROM volunteerSkill",
        "skill": "SELECT * FROM skill",
        "interest": "SELECT * FROM Interest",
        "volunteer_interest": "SELECT * FROM volunteerInterest",
        "volunteer_range": "SELECT * FROM volunteerRange"
    }

    data_frames = {name: execute_query(query) for name, query in queries.items()}
    return data_frames
