-- phpMyAdmin SQL Dump
-- version 4.1.14
-- http://www.phpmyadmin.net
--
-- Host: 127.0.0.1
-- Generation Time: Jun 25, 2016 at 02:11 AM
-- Server version: 5.6.17
-- PHP Version: 5.5.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `lol`
--

-- --------------------------------------------------------

--
-- Table structure for table `follower`
--

CREATE TABLE IF NOT EXISTS `follower` (
  `followers_id` int(11) NOT NULL AUTO_INCREMENT,
  `entity_id` int(11) NOT NULL,
  `user_name` varchar(30) NOT NULL,
  PRIMARY KEY (`followers_id`),
  KEY `fk_entity_id` (`entity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `following`
--

CREATE TABLE IF NOT EXISTS `following` (
  `following_id` int(11) NOT NULL AUTO_INCREMENT,
  `entity_id` int(11) NOT NULL,
  `user_name` varchar(30) NOT NULL,
  PRIMARY KEY (`following_id`),
  KEY `fk_entity_id` (`entity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;

-- --------------------------------------------------------

--
-- Table structure for table `lol_entity`
--

CREATE TABLE IF NOT EXISTS `lol_entity` (
  `entity_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `summoner_name` varchar(140) NOT NULL,
  `level` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`entity_id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=253 ;

-- --------------------------------------------------------

--
-- Table structure for table `tweets`
--

CREATE TABLE IF NOT EXISTS `tweets` (
  `tweet_id` bigint(20) unsigned NOT NULL,
  `tweet_text` varchar(150) NOT NULL,
  `created_at` date NOT NULL,
  `twitter_id` bigint(20) unsigned NOT NULL,
  `retweet_count` int(10) unsigned NOT NULL DEFAULT '0',
  `in_reply_to_status_id` bigint(20) unsigned DEFAULT NULL,
  `in_reply_to_twitter_id` bigint(20) unsigned DEFAULT NULL,
  PRIMARY KEY (`tweet_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `twitter_entity`
--

CREATE TABLE IF NOT EXISTS `twitter_entity` (
  `entity_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_name` varchar(30) NOT NULL,
  `screen_name` varchar(30) DEFAULT NULL,
  `description` varchar(1000) DEFAULT NULL,
  `ign` varchar(30) DEFAULT NULL,
  `followers_count` int(11) DEFAULT NULL,
  `friends_count` int(11) DEFAULT NULL,
  `date_created` datetime NOT NULL,
  `tweet_count` int(11) DEFAULT NULL,
  `language` varchar(8) DEFAULT NULL,
  `last_post` datetime DEFAULT NULL,
  `twitter_id` bigint(20) NOT NULL,
  `highest_pulled_tweet_id` bigint(20) DEFAULT NULL,
  `smallest_pulled_tweet_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`entity_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=731897 ;

-- --------------------------------------------------------

--
-- Table structure for table `twitter_lol_resolution`
--

CREATE TABLE IF NOT EXISTS `twitter_lol_resolution` (
  `resolution_id` int(11) NOT NULL AUTO_INCREMENT,
  `twitter_entity_id` bigint(20) NOT NULL,
  `lol_entity_id` bigint(20) NOT NULL,
  `confidence_score` int(11) DEFAULT NULL,
  PRIMARY KEY (`resolution_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=219 ;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `follower`
--
ALTER TABLE `follower`
  ADD CONSTRAINT `follower_ibfk_1` FOREIGN KEY (`entity_id`) REFERENCES `twitter_entity` (`entity_id`);

--
-- Constraints for table `following`
--
ALTER TABLE `following`
  ADD CONSTRAINT `following_ibfk_1` FOREIGN KEY (`entity_id`) REFERENCES `twitter_entity` (`entity_id`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
