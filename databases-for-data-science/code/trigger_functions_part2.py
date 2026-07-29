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

#Drop if function and trigger already existed
def drop_existing_update_trigger_and_function():
    drop_trigger_and_function_query = """
    DROP TRIGGER IF EXISTS trigger_update_volunteer_number ON requestSkill;
    DROP FUNCTION IF EXISTS update_volunteer_number;
    """
    execute_command(drop_trigger_and_function_query)
drop_existing_update_trigger_and_function()

# Create the function to update volunteer number
def create_update_volunteer_number_function():
    create_function_query = """
    CREATE OR REPLACE FUNCTION update_volunteer_number() RETURNS TRIGGER AS $$
    BEGIN
        UPDATE volunteerRequest
        SET volunteerNumber = (
            SELECT COALESCE(SUM(minimumNeed), 0)
            FROM requestSkill
            WHERE requestID = NEW.requestID
        )
        WHERE requestID = NEW.requestID;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """
    execute_command(create_function_query)
create_update_volunteer_number_function()

# Create the trigger to call the function after update on requestSkill
def create_update_volunteer_number_trigger():
    create_trigger_query = """
    CREATE TRIGGER trigger_update_volunteer_number
    AFTER UPDATE ON requestSkill
    FOR EACH ROW
    EXECUTE FUNCTION update_volunteer_number();
    """
    execute_command(create_trigger_query)
create_update_volunteer_number_trigger()

# Insert a new request skill (for testing)
def insert_request_skill():
    insert_query = """
    INSERT INTO requestSkill (requestSkillID, name, minimumNeed, value, requestID) 
    VALUES (1942, 'SqlAndPython', 3, 2, 1);
    """
    execute_command(insert_query)
insert_request_skill()

# Update the minimum need to trigger the update
def update_minimum_need():
    update_sql = "UPDATE requestSkill SET minimumNeed = 5 WHERE requestSkillID = 1942;" #modify to any minimumNeed and requestSkillID you prefer
    execute_command(update_sql)
update_minimum_need()

# Check the updated volunteer number
def check_volunteer_number():
    update_check_query = "SELECT volunteerNumber FROM volunteerRequest WHERE requestID = 1;"
    return execute_query(update_check_query)
volunteer_update_number = check_volunteer_number()
print(volunteer_update_number)

#Delete the added row
def delete_request_skill():
    delete_query = "DELETE FROM requestSkill WHERE requestSkillID = 1942;"
    execute_command(delete_query)
delete_request_skill()