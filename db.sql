DROP DATABASE IF EXISTS `progressApp`;

CREATE DATABASE IF NOT EXISTS `progressApp`;

USE `progressApp`;

CREATE TABLE IF NOT EXISTS progressApp.users (
	userId INT auto_increment NOT NULL,
	email varchar(100) NOT NULL,
	password varchar(100) NOT NULL,
	isAdmin BOOL DEFAULT FALSE NOT NULL,
	CONSTRAINT users_PK PRIMARY KEY (userId),
	CONSTRAINT pw_not_null CHECK (LENGTH(password)>4)
);

CREATE TABLE IF NOT EXISTS progressApp.categories (
	categoryId INT NOT NULL AUTO_INCREMENT,
	categoryName varchar(100) DEFAULT "General" NOT NULL,
	userId INT NOT NULL,
	CONSTRAINT categories_PK PRIMARY KEY (categoryId),
	CONSTRAINT categories_FK FOREIGN KEY (userId) REFERENCES progressApp.users(userId)
);

CREATE TABLE IF NOT EXISTS progressApp.notes (
	userId INT NOT NULL,
	noteId INT auto_increment NOT NULL,
	noteData TEXT NULL,
	categoryId INT NOT NULL,
	`timeStamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
	modified BOOL DEFAULT FALSE NOT NULL,
	CONSTRAINT notes_PK PRIMARY KEY (noteId),
	CONSTRAINT notes_FK FOREIGN KEY (userId) REFERENCES progressApp.users(userId),
	CONSTRAINT notes_FK_2 FOREIGN KEY (categoryId) REFERENCES progressApp.categories(categoryId)
);

CREATE TABLE IF NOT EXISTS progressApp.logs (
	userId INT NOT NULL,
	`timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`action` ENUM('login', 'logout', 'modify', 'add', 'remove', 'signUp') NOT NULL,
	logId INT auto_increment NOT NULL,
	noteId INT,
	CONSTRAINT logs_PK PRIMARY KEY (logId)
);

CREATE TABLE IF NOT EXISTS progressApp.subscription (
	userID INT NOT NULL,
	subscription_type ENUM('beta', 'student', 'basic', 'premium') DEFAULT 'beta' NOT NULL,
	transaction_id INT,
	subscription_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
	validity INT,
	CONSTRAINT subscriptions_FK FOREIGN KEY (userId) REFERENCES progressApp.users(userId),
	CONSTRAINT transaction_check CHECK(transaction_id > 0)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_0900_ai_ci;

CREATE INDEX users_userId_IDX ON progressApp.users(userId,email);

CREATE INDEX notes_ids_IDX ON progressApp.notes(userId, noteId);

CREATE INDEX logs_IDX ON progressApp.logs(userId, `timestamp`);

CREATE INDEX categories_IDX ON progressApp.categories(userId);

CREATE USER IF NOT EXISTS 'noteAdmin'@'localhost' IDENTIFIED BY 'noteAdminPWRDBPassword';
GRANT ALL PRIVILEGES ON progressApp.* TO 'noteAdmin'@'localhost';
FLUSH PRIVILEGES;
SET PASSWORD FOR 'noteAdmin'@'localhost' = 'noteAdminPRWDBPassword';

CREATE USER IF NOT EXISTS 'noteGuest'@'localhost' IDENTIFIED BY 'noteGuestPWRDBPassword';
GRANT SELECT ON progressApp.notes TO 'noteGuest'@'localhost';
GRANT SELECT ON progressApp.categories TO 'noteGuest'@'localhost';
FLUSH PRIVILEGES;
SET PASSWORD FOR 'noteGuest'@'localhost' = 'noteGuestPWRDBPassword';

CREATE USER IF NOT EXISTS 'noteAnalyst'@'localhost' IDENTIFIED BY 'noteAanalystPWRDBPassword';
GRANT SELECT ON progressApp.logs TO 'noteAnalyst'@'localhost';
GRANT SELECT ON progressApp.subscription TO 'noteAnalyst'@'localhost';
GRANT SELECT ON progressApp.categories TO 'noteAnalyst'@'localhost';
GRANT SELECT (`noteId`, `userId`, `categoryId`, `timeStamp`, `modified`) ON progressApp.notes TO 'noteAnalyst'@'localhost';
FLUSH PRIVILEGES;
SET PASSWORD FOR 'noteAnalyst'@'localhost' = 'noteAnalystPWRDBPassword';

/* PROCEDURE TO CHECK LOG IN CREDENTIALS THE APP*/
DROP PROCEDURE IF EXISTS login_proc;
DELIMITER $$
CREATE PROCEDURE login_procedure(IN email VARCHAR(100), IN password VARCHAR(100))
BEGIN
	set @email = email;
	set @password = password;
	set @stmt = "SELECT email, password, userId, isAdmin FROM users WHERE email=? AND password=?";
	PREPARE stmt FROM @stmt;
	EXECUTE stmt USING @email, @password;
	DEALLOCATE PREPARE stmt;
END;
$$
DELIMITER ;

/* PROCEDURE TO RETRIEVE THE CATEGORIES*/
DROP PROCEDURE IF EXISTS get_categories;
DELIMITER $$
CREATE PROCEDURE get_categories(IN userId INT)
BEGIN
	set @userId=userId;
	set @stmt = 'SELECT categoryName, categoryId FROM categories WHERE userId = ?';
	PREPARE stmt FROM @stmt;
	EXECUTE stmt USING @userId;
	DEALLOCATE PREPARE stmt;
END;
$$
DELIMITER ;

/* PROCEDURE TO INSERT NEW CATEGORIES*/
DROP PROCEDURE IF EXISTS insert_category;
DELIMITER $$
CREATE PROCEDURE insert_category(IN userId INT, IN cat VARCHAR(100))
BEGIN
	set @userId=userId;
	set @cat=cat;
	set @stmt = 'INSERT INTO categories (userId, categoryName) VALUES (?, ?)';
	PREPARE stmt FROM @stmt;
	EXECUTE stmt USING @userId, @cat;
	DEALLOCATE PREPARE stmt;
END;
$$
DELIMITER ;

/* VIEW TO JOIN NOTES TABLE WITH CATEGORIES TABLE*/
DROP VIEW IF EXISTS cat_note_join;
CREATE VIEW cat_note_join AS  
SELECT n.noteData, c.categoryName, date_format(n.`timeStamp` , '%Y-%m-%d') as format_date, n.userId, n.noteId, n.modified
FROM notes AS n 
LEFT JOIN categories AS c 
ON n.categoryId=c.categoryId 
ORDER BY n.`timeStamp` DESC;

/* PROCEDURE TO GET NOTES DATA*/
DROP PROCEDURE IF EXISTS notes_procedure;
DELIMITER $$
CREATE PROCEDURE notes_procedure(IN userId INT)
BEGIN
	set @userId = userId;
	set @stmt = "SELECT noteData, categoryName, format_date, noteId, modified FROM cat_note_join WHERE userId=?;";
	PREPARE stmt FROM @stmt;
	EXECUTE stmt USING @userId;
	DEALLOCATE PREPARE stmt;
END;
$$
DELIMITER ;

/* TRIGGER THAT UPDATES THE LOGS AND SUBSCRIPTION WHEN NEW USER IS CREATED */
DROP TRIGGER IF EXISTS subscription_after_insert;
DELIMITER %%
CREATE TRIGGER subscription_after_insert
AFTER INSERT 
ON users
FOR EACH ROW 
BEGIN
INSERT INTO subscription(userID, validity)
VALUES (NEW.userId, FLOOR(RAND()*(12+1)));
INSERT INTO logs(userId, action)
VALUES(NEW.userId, 'signUp');
INSERT INTO categories(userId)
VALUES(NEW.userId);
END
%%
DELIMITER ;

/* TRIGGER THAT UPDATES THE MODIFIED WHEN THERE IS A MODIFICATION AND ADDS IT TO LOGS */
DROP TRIGGER IF EXISTS modify_after_update;
DELIMITER $$
CREATE TRIGGER modify_after_update
BEFORE UPDATE 
ON notes
FOR EACH ROW 
BEGIN
IF NEW.noteData <> OLD.noteData THEN SET NEW.modified=TRUE;
END IF ; 
INSERT INTO logs(userId, action, noteId)
VALUES(OLD.userId, 'modify', OLD.noteId);
END
$$
DELIMITER ;

/* TRIGGER THAT LOGS WHEN THE USER ADDS A NEW NOTE */
DROP TRIGGER IF EXISTS notes_after
DELIMITER $$
CREATE TRIGGER note_after_insert
AFTER INSERT
ON notes
FOR EACH ROW 
BEGIN
INSERT INTO logs(userId, action, noteId) VALUES(NEW.userId, 'add', NEW.noteID);
END
$$
DELIMITER ;

INSERT INTO users(email, password, isAdmin) VALUES ('admin@admin.com', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', TRUE);







