SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `movie` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `original_title` VARCHAR(255),
    `overview` TEXT,
    `tagline` VARCHAR(500),
    `release_date` VARCHAR(50),
    `runtime` INT,
    `status` VARCHAR(50),
    `poster_path` VARCHAR(255),
    `backdrop_path` VARCHAR(255),
    `trailer_key` VARCHAR(100),
    `trailer_site` VARCHAR(50),
    `vote_average` DOUBLE DEFAULT 0.0,
    `vote_count` INT DEFAULT 0,
    `imdb_id` VARCHAR(50),
    `imdb_rating` DOUBLE DEFAULT 0.0,
    `imdb_votes` INT DEFAULT 0,
    `tmdb_id` BIGINT,
    `original_language` VARCHAR(20),
    `origin_country` VARCHAR(50),
    `budget` BIGINT DEFAULT 0,
    `revenue` BIGINT DEFAULT 0,
    `adult` BOOLEAN DEFAULT FALSE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;