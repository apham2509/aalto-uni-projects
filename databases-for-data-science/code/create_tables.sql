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