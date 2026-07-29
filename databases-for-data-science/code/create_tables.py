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

def drop_tables():
    drop_commands = """
    DROP TABLE IF EXISTS Application CASCADE;
    DROP TABLE IF EXISTS RequestSkill CASCADE;
    DROP TABLE IF EXISTS RequestLocation CASCADE;
    DROP TABLE IF EXISTS VolunteerRequest CASCADE;
    DROP TABLE IF EXISTS VolunteerSkill CASCADE;
    DROP TABLE IF EXISTS VolunteerInterest CASCADE;
    DROP TABLE IF EXISTS VolunteerRange CASCADE;
    DROP TABLE IF EXISTS Volunteer CASCADE;
    DROP TABLE IF EXISTS Skill CASCADE;
    DROP TABLE IF EXISTS Interest CASCADE;
    DROP TABLE IF EXISTS City CASCADE;
    DROP TABLE IF EXISTS Beneficiary CASCADE;
    """
    try:
        commands = drop_commands.split(';')
        for command in commands:
            if command.strip():
                execute_non_query(command)
        print("Tables dropped successfully.")
    except Exception as error:
        print("Error while dropping tables:", error)

drop_tables()

def list_tables_and_columns():
    query = """
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """
    result_df = execute_query(query)
    print("Tables and Columns:")
    print(result_df)


def create_tables():
    create_commands = """
    CREATE TABLE City(
        cityID text primary key,
        name text not null,
        geolocation text not null
    );


    CREATE TABLE Beneficiary(
        beneficiaryID int primary key,
        name text not null,
        address text not null,
        cityID text not null,
        foreign key (cityID) REFERENCES City(cityID)
    );

    CREATE TABLE Volunteer(
        volunteerID text primary key,
        birthdate DATE not null,
        cityID text not null,
        name text not null,
        email text not null,
        address text not null,
        readiness int not null,
        foreign key (cityID) REFERENCES City(cityID)
    );

    CREATE TABLE volunteerRequest(
        requestID int primary key,
        title text not null,
        volunteerNumber int not null,
        priority int not null check(priority >= 0 AND priority <= 5),
        startDate DATE not null,
        endDate Date not null,
        registerByDate DATE not null,
        beneficiaryID int not null,
        foreign key (beneficiaryID) REFERENCES Beneficiary(beneficiaryID)
    );

    CREATE TABLE requestSkill(
        requestSkillID int primary key,
        name text not null,
        minimumNeed int not null,
        value int not null check(value >= 0 AND value <= 5),
        requestID int not null,
        foreign key (requestID) REFERENCES volunteerRequest(requestID)
    );

    CREATE TABLE requestLocation(
        requestLocationID int primary key,
        cityID text not null,
        requestID int not null,
        foreign key (cityID) REFERENCES City(cityID),
        foreign key (requestID) REFERENCES volunteerRequest(requestID)
    );

    CREATE TABLE Application(
        applicationID int primary key,
        time DATE not null,
        isValid BOOLEAN not null,
        requestID int not null,
        volunteerID text not null,
        foreign key (requestID) REFERENCES volunteerRequest(requestID),
        foreign key (volunteerID) REFERENCES Volunteer(volunteerID)
    );

    CREATE TABLE volunteerRange(
        volunteerID text not null,
        cityID text not null,
        foreign key (volunteerID) REFERENCES Volunteer(volunteerID),
        foreign key (cityID) REFERENCES City(cityID)
    );

    CREATE TABLE volunteerSkill(
        volunteerSkillID int primary key,
        name text not null,
        volunteerID text not null,
        foreign key (volunteerID) REFERENCES Volunteer(volunteerID)
    );

    CREATE TABLE skill(
        name text primary key,
        description text not null
    );

    CREATE TABLE volunteerInterest(
        volunteerInterestID int primary key,
        name text not null,
        volunteerID text not null,
        foreign key (volunteerID) REFERENCES Volunteer(volunteerID)
    );

    CREATE TABLE Interest(
        name text primary key
    );
    """

    try:
        commands = create_commands.split(';')
        for command in commands:
            if command.strip():
                execute_non_query(command)
        print("Tables created successfully.")
    except Exception as error:
        print("Error while creating tables:", error)

def test():
    query = """
    SELECT *
    FROM volunteerRequest
    """

    result_df = execute_query(query)
    print("The result is:")
    print(result_df)


drop_tables()

create_tables()

list_tables_and_columns()

test()