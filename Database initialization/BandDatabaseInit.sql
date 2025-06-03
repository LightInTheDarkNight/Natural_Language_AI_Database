CREATE DATABASE IF NOT EXISTS `band_rentals`;
USE `band_rentals`;
CREATE TABLE IF NOT EXISTS `student` (
  `id_num` int unsigned NOT NULL,
  `byu_id` varchar(45) NOT NULL,
  `byu_email` varchar(45) NOT NULL,
  `first_name` varchar(45) NOT NULL,
  `middle_names` varchar(45) DEFAULT NULL,
  `last_name` varchar(45) NOT NULL,
  `preferred_name` varchar(45) DEFAULT NULL,
  `section` enum('Piccolo','Clarinet','Alto Sax','Tenor Sax','Trumpet','French Horn','Trombone','Baritone','Tuba','Drumline','Color Guard') NOT NULL,
  `backup_email` varchar(45) DEFAULT NULL,
  `phone_number` char(13) DEFAULT NULL,
  PRIMARY KEY (`id_num`),
  UNIQUE KEY `student_id_UNIQUE` (`id_num`),
  UNIQUE KEY `byu_id_UNIQUE` (`byu_id`),
  UNIQUE KEY `byu_email_UNIQUE` (`byu_email`)
);
CREATE TABLE IF NOT EXISTS `uniform_piece` (
  `item_number` tinyint unsigned NOT NULL,
  `item_type` enum('jacket','blue pants','white pants') NOT NULL,
  `height_inches` int NOT NULL,
  `weight_lbs` int NOT NULL,
  `tuba` tinyint NOT NULL DEFAULT '0',
  `student_id` int unsigned DEFAULT NULL,
  PRIMARY KEY (`item_number`,`item_type`),
  KEY `uniform_renter` (`student_id`),
  CONSTRAINT `uniform_renter` FOREIGN KEY (`student_id`) REFERENCES `student` (`id_num`) ON UPDATE CASCADE
);
CREATE TABLE `parka` (
  `parka_num` tinyint unsigned NOT NULL,
  `size` enum('xs','s','m','l','xl','xxl') NOT NULL,
  `student_id` int unsigned DEFAULT NULL,
  PRIMARY KEY (`parka_num`),
  UNIQUE KEY `parka_num_UNIQUE` (`parka_num`),
  UNIQUE KEY `student_id_UNIQUE` (`student_id`),
  CONSTRAINT `parka_renting_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`id_num`) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE TABLE IF NOT EXISTS `shako` (
  `shako_num` tinyint unsigned NOT NULL,
  `size` enum('xs','s','m','l','xl') NOT NULL,
  `student_id` int unsigned DEFAULT NULL,
  PRIMARY KEY (`shako_num`),
  UNIQUE KEY `shako_num_UNIQUE` (`shako_num`),
  UNIQUE KEY `student_id_UNIQUE` (`student_id`),
  CONSTRAINT `renting_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`id_num`) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE VIEW `all_uniform_pieces` AS
    SELECT `uniform_piece`.`item_type` AS `item_type`,`uniform_piece`.`item_number` AS `item_number`,
           `uniform_piece`.`student_id` AS `student_id` FROM `uniform_piece`
    UNION
    SELECT 'shako' AS `item_type`,`shako`.`shako_num` AS `shako_num`,`shako`.`student_id` AS `student_id` FROM `shako`
    UNION
    SELECT 'parka' AS `item_type`,`parka`.`parka_num` AS `parka_num`,`parka`.`student_id` AS `student_id` FROM `parka`;

