-- Part 1
-- create table for assigning volunteers
create table volunteerAssignment (
	assignmentID serial primary key,
	requestID int not null,
	volunteerID text not null,
	isAccepted boolean not null,
	foreign key ( requestID ) references volunteerRequest(requestID),
	foreign key (volunteerID) references volunteer(volunteerID)
);

select *
from volunteerAssignment

create or replace function assign_volunteers(request_id int)
returns void as $$
declare 
	volunteer_count int;
	skill_count int;
	skill_record record;
	volunteer_record record;
	min_volunteers int;
	reg_by_date date;

begin
	-- Get request details
	select registerByDate, volunteerNumber into reg_by_date, min_volunteers
	from volunteerRequest
	where requestID = request_id;

	--check if the register by date passed
	if reg_by_date < current_date then 
		raise notice 'Register by date has passed';
		return;
	end if;
	
	--assign volunteers based on skills and prioritize
	for skill_record in
		select * from requestSkill where requestID = request_id order by value desc
	loop
		select count(*) into skill_count
		from application a
		join volunteerSkill vs on a.volunteerID = vs.volunteerID
		where a.requestID = request_id and vs.name = skill_record.name and a.isValid = true;
	
		if skill_count < skill_record.minimumNeed then
			raise notice 'Not enough volunteer with skill % for request %',skill_record.name, request_id;
		end if;
		
		for volunteer_record in 
			select a.volunteerID
			from application a
			join volunteerSkill vs on a.volunteerID = vs.volunteerID
			where a.requestID = request_id and vs.name = skill_record.name and a.isValid = true 
			order by skill_record.value desc
		limit skill_record.minimumNeed
		loop
			insert into volunteerAssignment (requestID, volunteerID, isAccepted)
			values (request_id,volunteer_record.volunteerID,true);
			raise notice 'Assigned volunteer % with skill %', volunteer_record.volunteerID, skill_record.name;
		end loop;
		
	end loop;
	
	-- assign the rest of the volunteers
	select count(*) into volunteer_count 
	from application 
	where requestID = request_id and isValid = true;

	if volunteer_count < min_volunteers then
		raise notice 'not enough volunteers for request %, the register by date is not pass',request_id;
	end if;

	for volunteer_record in 
		select volunteerID from application where requestID = request_id and isValid = true
		except 
		select volunteerID from volunteerAssignment where requestID = request_id 
	loop
		insert into volunteerAssignment(requestID, volunteerID, isAccepted)
		values(request_id,volunteer_record.volunteerID, false);
		raise notice 'Assigned volunteer % without specific skill', volunteer_record.volunteerID;
	end loop;


exception
	when others then
		raise; 
	
end;
$$ language plpgsql;

-- the function that will output all of the requestID
CREATE OR REPLACE FUNCTION assign_all_volunteers()
RETURNS VOID AS $$
DECLARE
    request_record RECORD;

BEGIN
    FOR request_record IN
        SELECT requestID FROM volunteerRequest
    LOOP
        PERFORM assign_volunteers(request_record.requestID);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

select assign_all_volunteers()

select assign_volunteers(4);

select * from volunteerAssignment

--PartB
-- This transaction is used for when we want to assign one living within the requestLocation
create or replace function assign_volunteers_special(request_id int)
returns void as $$
declare 
	volunteer_count int;
	volunteer_record record;
	min_volunteers int;
	reg_by_date date;
	request_city record;
	
begin 
	-- Get request details
	select registerByDate, volunteerNumber into reg_by_date, min_volunteers
	from volunteerRequest
	where requestID = request_id;

	-- get request city
	select cityID into request_city
	from requestLocation
	where requestID = request_id;

	--check if the register by date passed
	if reg_by_date < current_date then 
		raise notice 'Register by date has passed';
		raise exception 'Cannot proceed as register by date has passed';
	end if;

	for volunteer_record in
		select a.volunteerID
		from application a
		join volunteerSkill vs1 on a.volunteerID = vs1.volunteerID and vs1.name = 'CommunicationAndMarketing'
		join volunteerSkill vs2 on a.volunteerID = vs1.volunteerID and vs1.name = 'PhotographyAndVideo'
		join volunteerRange vr on a.volunteerID = vr.volunteerID
		where a.requestID = request_id and vr.cityID = request_city.cityID and a.isValid = true
	loop
		insert into volunteerAssignment (requestID, volunteerID, isAccepted )
		values (request_id, volunteer_record.volunteerID, true);
		raise notice 'Assigned volunteer % with required skills in city %', volunteer_record.volunteerID, request_city.cityID;
    end loop;
   
   	select COUNT(*) into volunteer_count 
    from volunteerAssignment 
    where requestID = request_id;

    -- Check if the number of assigned volunteers meets the requirement
    if volunteer_count < min_volunteers  then 
        raise notice 'Not enough volunteers for request % in city %', request_id, request_city.cityID;
    end if;

exception
	when others then
		raise; 
	
end;
$$ LANGUAGE plpgsql;
		
select assign_volunteers_special(6);

select * from volunteerAssignment
