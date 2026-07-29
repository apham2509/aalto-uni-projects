import os
import pandas as pd
import psycopg2
import traceback
import numpy as np

basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Function to establish database connection
def get_db_connection():
    return psycopg2.connect(
        database="group_12_2024",
        user="group_12_2024",
        password="73JKSEnw6YJZ",
        host="dbcourse.cs.aalto.fi",
        port="5432"
    )

# Function to execute non-query SQL commands (like CREATE, ALTER, INSERT)
def execute_non_query(query, data=None):
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        if data:
            cursor.executemany(query, data)
        else:
            cursor.execute(query)
        connection.commit()
        print("Executed successfully:", query)
    except (Exception, psycopg2.Error) as error:
        print("Error while executing non-query", error)
        traceback.print_exc()
    finally:
        if connection:
            cursor.close()
            connection.close()

def preview_table(table_name, row_count=5):
    connection = None
    try:
        connection = get_db_connection()
        query = f"SELECT * FROM {table_name} LIMIT {row_count}"
        df = pd.read_sql_query(query, connection)
        print(f"Preview of table {table_name}:")
        display(df.head())
    except (Exception, psycopg2.Error) as error:
        print(f"Error while fetching data from table {table_name}", error)
        traceback.print_exc()
    finally:
        if connection:
            connection.close()

# Load data from all sheets in the Excel file
data_dir = os.path.join(basepath, 'data')
excel_file_path = os.path.join(data_dir, 'data.xlsx')
sheets = pd.read_excel(excel_file_path, sheet_name=None)
print("Sheet names:")
for sheet_name in sheets.keys():
    print(sheet_name)

# Function to add auto-incremented primary keys and prepare data for insertion
def prepare_data_for_insertion(sheet_name, table_name, df):
    # Rename columns as necessary
    if sheet_name in column_renames:
        df.rename(columns=column_renames[sheet_name], inplace=True)

    # Add primary key columns with auto-increment values
    if table_name in ['volunteerSkill', 'volunteerInterest', 'requestSkill', 'requestLocation']:
        if table_name == 'volunteerSkill':
            df.insert(0, 'volunteerSkillID', range(1, len(df) + 1))
        elif table_name == 'volunteerInterest':
            df.insert(0, 'volunteerInterestID', range(1, len(df) + 1))
        elif table_name == 'requestSkill':
            df.insert(0, 'requestSkillID', range(1, len(df) + 1))
        elif table_name == 'requestLocation':
            df.insert(0, 'requestLocationID', range(1, len(df) + 1))

    # Convert data types to avoid compatibility issues
    df = df.applymap(lambda x: int(x) if isinstance(x, (np.int64, np.int32)) else x)
    df = df.astype(object).where(pd.notnull(df), None)  # Handle NaNs by converting them to None
    return df

# Define a mapping of sheet names to table names (adjust this as needed)
sheet_to_table_mapping = {
    'city': 'city',
    'volunteer': 'volunteer',
    'volunteer_range': 'volunteerRange',
    'skill': 'skill',
    'skill_assignment': 'volunteerSkill',
    'interest': 'interest',
    'interest_assignment': 'volunteerInterest',
    'beneficiary': 'beneficiary',
    'request': 'volunteerRequest',
    'request_skill': 'requestSkill',
    'request_location': 'requestLocation',
    'volunteer_application': 'application'
}

# Rename columns if necessary to match the table schema
column_renames = {
    'city': {'id': 'cityID', 'name': 'name', 'geolocation': 'geolocation'},
    'beneficiary': {'id': 'beneficiaryID', 'name': 'name', 'address': 'address', 'city_id': 'cityID'},
    'volunteer': {'id': 'volunteerID', 'birthdate': 'birthdate', 'city_id': 'cityID', 'name': 'name', 'email': 'email', 'address': 'address', 'travel_readiness': 'readiness'},
    'volunteer_range': {'volunteer_id': 'volunteerID', 'city_id': 'cityID'},
    'skill': {'name': 'name', 'description': 'description'},
    'skill_assignment': {'volunteer_id': 'volunteerID', 'skill_name': 'name'},
    'interest': {'name': 'name'},
    'interest_assignment': {'interest_name': 'name', 'volunteer_id': 'volunteerID'},
    'request': {'id': 'requestID', 'title': 'title', 'beneficiary_id': 'beneficiaryID', 'number_of_volunteers': 'volunteerNumber', 'priority_value': 'priority', 'start_date': 'startDate', 'end_date': 'endDate', 'register_by_date': 'registerByDate'},
    'request_skill': {'request_id': 'requestID', 'skill_name': 'name', 'min_need': 'minimumNeed', 'value': 'value'},
    'request_location': {'request_id': 'requestID', 'city_id': 'cityID'},
    'volunteer_application': {'id': 'applicationID', 'request_id': 'requestID', 'volunteer_id': 'volunteerID', 'modified': 'time', 'is_valid': 'isValid'}
}

# Prepare data for insertion
prepared_data = {}
for sheet_name, df in sheets.items():
    if sheet_name in sheet_to_table_mapping:
        table_name = sheet_to_table_mapping[sheet_name]
        prepared_data[table_name] = prepare_data_for_insertion(sheet_name, table_name, df)
    else:
        print(f"Sheet {sheet_name} does not have a corresponding table mapping.")

# Insert data into the database
for table_name, df in prepared_data.items():
    columns = ', '.join(df.columns)
    values = ', '.join(['%s'] * len(df.columns))
    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
    data = [tuple(x) for x in df.to_numpy()]
    execute_non_query(insert_query, data)

# Preview each table one by one
for table_name in sheet_to_table_mapping.values():
    preview_table(table_name)