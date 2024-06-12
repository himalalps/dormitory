DROP FUNCTION IF EXISTS countRoom;
DELIMITER //
CREATE FUNCTION countRoom(dorm_id Integer) RETURNS Integer
READS SQL DATA
BEGIN
    DECLARE count Integer;
    SELECT COUNT(*) INTO count FROM Room WHERE Room.dorm_id = dorm_id;
    RETURN count;
END //
DELIMITER ;

DROP FUNCTION IF EXISTS countResident;
DELIMITER //
CREATE FUNCTION countResident(dorm_id Integer) RETURNS Integer
READS SQL DATA
BEGIN
    DECLARE count Integer;
    SELECT SUM(spaces) - SUM(residents) INTO count FROM Room WHERE Room.dorm_id = dorm_id;
    RETURN count;
END //
DELIMITER ;

DROP TRIGGER IF EXISTS afterStudentInsert;
DELIMITER //
CREATE TRIGGER afterStudentInsert AFTER INSERT ON Student
FOR EACH ROW
BEGIN
    UPDATE Room SET residents = residents + 1 WHERE Room.id = NEW.room_id;
    UPDATE Dorm, Room SET left_residents = countResident(Dorm.id) WHERE Dorm.id = Room.dorm_id AND Room.id = NEW.room_id;
END //
DELIMITER ;

DROP TRIGGER IF EXISTS afterStudentUpdate;
DELIMITER //
CREATE TRIGGER afterStudentUpdate AFTER UPDATE ON Student
FOR EACH ROW
BEGIN
    IF OLD.room_id <> NEW.room_id THEN
        UPDATE Room SET residents = residents + 1 WHERE Room.id = NEW.room_id;
        UPDATE Room SET residents = residents - 1 WHERE Room.id = OLD.room_id;
    END IF;
END //
DELIMITER ;

DROP TRIGGER IF EXISTS afterStudentDelete;
DELIMITER //
CREATE TRIGGER afterStudentDelete AFTER DELETE ON Student
FOR EACH ROW
BEGIN
    UPDATE Room SET residents = residents - 1 WHERE Room.id = OLD.room_id;
    UPDATE Dorm, Room SET left_residents = countResident(Dorm.id) WHERE Dorm.id = Room.dorm_id AND Room.id = OLD.room_id;
END //
DELIMITER ;

DROP TRIGGER IF EXISTS afterRoomInsert;
DELIMITER //
CREATE TRIGGER afterRoomInsert AFTER INSERT ON Room
FOR EACH ROW
BEGIN
    UPDATE Dorm SET rooms = countRoom(NEW.dorm_id) WHERE Dorm.id = NEW.dorm_id;
    UPDATE Dorm SET left_residents = countResident(NEW.dorm_id) WHERE Dorm.id = NEW.dorm_id;
END //
DELIMITER ;

DROP TRIGGER IF EXISTS afterRoomUpdate;
DELIMITER //
CREATE TRIGGER afterRoomUpdate AFTER UPDATE ON Room
FOR EACH ROW
BEGIN
    UPDATE Dorm SET rooms = countRoom(NEW.dorm_id) WHERE Dorm.id = NEW.dorm_id;
    UPDATE Dorm SET left_residents = countResident(NEW.dorm_id) WHERE Dorm.id = NEW.dorm_id;   
END //
DELIMITER ;

DROP TRIGGER IF EXISTS afterRoomDelete;
DELIMITER //
CREATE TRIGGER afterRoomDelete AFTER DELETE ON Room
FOR EACH ROW
BEGIN
    UPDATE Dorm SET rooms = countRoom(OLD.dorm_id) WHERE Dorm.id = OLD.dorm_id;
    UPDATE Dorm SET left_residents = countResident(OLD.dorm_id) WHERE Dorm.id = OLD.dorm_id;
END //
DELIMITER ;
