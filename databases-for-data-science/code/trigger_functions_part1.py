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
def drop_existing_trigger_and_function():
    drop_trigger_query = "DROP TRIGGER IF EXISTS check_volunteerID_trigger ON Volunteer;"
    execute_command(drop_trigger_query)

    drop_function_query = """
    DROP FUNCTION IF EXISTS validate_volunteerID CASCADE;
    DROP FUNCTION IF EXISTS calculate_control_character CASCADE;
    """
    execute_command(drop_function_query)
drop_existing_trigger_and_function()

#Create a function defined to create the trigger
def create_calculate_control_character_function():
    create_function_query = """
    CREATE OR REPLACE FUNCTION calculate_control_character(input_string TEXT) RETURNS CHAR AS $$
    DECLARE
        date_part TEXT;
        individual_part TEXT;
        combined_number BIGINT;
        remainder INTEGER;
        control_char CHAR;
    BEGIN
        date_part := SUBSTRING(input_string FROM 1 FOR 6);
        individual_part := SUBSTRING(input_string FROM 8 FOR 3);
        combined_number := CAST(date_part || individual_part AS BIGINT);
        remainder := combined_number % 31;
        control_char := SUBSTRING('0123456789ABCDEFHJKLMNPRSTUVWXY', remainder + 1, 1);
        RETURN control_char;
    END;
    $$ LANGUAGE plpgsql;
    """
    execute_command(create_function_query)
create_calculate_control_character_function()

#Create a function defined to create the trigger
def create_validate_volunteerID_function():
    create_trigger_function_query = """
    CREATE OR REPLACE FUNCTION validate_volunteerID() RETURNS TRIGGER AS $$
    DECLARE
        control_char CHAR;
    BEGIN
        control_char := calculate_control_character(NEW.volunteerID);
        IF control_char <> SUBSTRING(NEW.volunteerID FROM 11 FOR 1) THEN
            RAISE EXCEPTION 'Invalid control character in volunteerID %', NEW.volunteerID;
        END IF;
        IF LENGTH(NEW.volunteerID) <> 11 THEN
            RAISE EXCEPTION 'Invalid length for volunteerID %', NEW.volunteerID;
        END IF;
        IF SUBSTRING(NEW.volunteerID FROM 7 FOR 1) NOT IN ('+', '-', 'A', 'B', 'C', 'D', 'E', 'F', 'X', 'Y', 'W', 'V', 'U') THEN
            RAISE EXCEPTION 'Invalid separator character in volunteerID %', NEW.volunteerID;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """
    execute_command(create_trigger_function_query)
create_validate_volunteerID_function()

#Create the trigger to check volunteer ID
def create_volunteerID_trigger():
    create_trigger_query = """
    CREATE TRIGGER check_volunteerID_trigger
    BEFORE INSERT OR UPDATE ON Volunteer
    FOR EACH ROW
    EXECUTE FUNCTION validate_volunteerID();
    """
    execute_command(create_trigger_query)
create_volunteerID_trigger()

#Insert valid and invalid inputs to test the trigger
def insert_test_volunteer():
    test_valid_insert_query = """
    INSERT INTO Volunteer (volunteerID, birthdate, cityID, name, email, address, readiness) 
    VALUES ('150600A905P', '1990-01-01', '834', 'Eemeli Halminen', 'eemeli.halminen@example.com', 'Ruusulankatu 5', 1203);
    """
    test_invalid_insert_query = """
    INSERT INTO Volunteer (volunteerID, birthdate, cityID, name, email, address, readiness) 
    VALUES ('15060A905X', '1990-01-01', '72', 'Rafal Doe', 'rafal.doe@example.com', 'Otaakari 18', 329);
    """
    execute_command(test_valid_insert_query)
    execute_command(test_invalid_insert_query)

insert_test_volunteer()

#Show the added valid row
def fetch_volunteer(volunteer_id):
    fetch_query = f"SELECT * FROM Volunteer WHERE volunteerID = '{volunteer_id}';"
    return execute_query(fetch_query)
valid_row_df = fetch_volunteer('150600A905P')
print(valid_row_df)

#Delete the added row 
def delete_volunteer(volunteer_id):
    delete_query = f"DELETE FROM Volunteer WHERE volunteerID = '{volunteer_id}';"
    execute_command(delete_query)
delete_volunteer('150600A905P')