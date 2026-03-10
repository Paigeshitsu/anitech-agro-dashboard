-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Mar 01, 2026 at 09:43 PM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `anitech`
--

-- --------------------------------------------------------

--
-- Table structure for table `activity_logs`
--

CREATE TABLE `activity_logs` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `activity` varchar(255) NOT NULL,
  `details` text DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `activity_logs`
--

INSERT INTO `activity_logs` (`id`, `user_id`, `activity`, `details`, `ip_address`, `created_at`) VALUES
(1, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 07:44:15'),
(2, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-06 07:44:25'),
(3, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 07:44:38'),
(4, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 07:53:51'),
(5, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-06 07:58:55'),
(6, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 07:59:01'),
(7, 9, 'Added Crop', 'Added new crop: Test Productsdfdssdfsdfsd', '::1', '2026-02-06 08:00:59'),
(8, 9, 'Added Crop', 'Added new crop: sdfsddfdf', '::1', '2026-02-06 08:16:38'),
(9, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 08:17:29'),
(10, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-06 08:43:09'),
(11, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 08:43:33'),
(12, 9, 'Added Crop', 'Added new crop: sdsdfsfs', '::1', '2026-02-06 08:43:53'),
(13, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 08:44:06'),
(14, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-06 08:44:18'),
(15, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 08:44:23'),
(16, 10, 'Made Offer', 'Made offer for sdsdfsfs: ₱54.00', '::1', '2026-02-06 08:44:34'),
(17, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 08:44:44'),
(18, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-06 08:44:58'),
(19, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 08:45:02'),
(20, 9, 'Accepted Offer', 'Accepted offer for sdsdfsfs from Test Buyer', '::1', '2026-02-06 08:45:14'),
(21, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 09:38:20'),
(22, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 14:39:11'),
(23, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 15:09:07'),
(24, 9, 'Updated Crop', 'Updated crop: sdsdfsfs', '::1', '2026-02-06 15:40:00'),
(25, 9, 'Updated Crop', 'Updated crop: sdfsddfdf', '::1', '2026-02-06 15:40:09'),
(26, 9, 'Updated Crop', 'Updated crop: sdfsddfdf', '::1', '2026-02-06 15:40:16'),
(27, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 16:24:20'),
(28, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-06 16:24:30'),
(29, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 16:24:35'),
(30, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-06 16:24:48'),
(31, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 16:24:54'),
(32, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 16:33:15'),
(33, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-06 23:31:42'),
(34, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-06 23:31:50'),
(35, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-06 23:31:57'),
(36, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-07 01:28:03'),
(37, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-07 01:28:21'),
(38, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-07 01:28:27'),
(39, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-07 02:03:32'),
(40, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-07 03:17:54'),
(41, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-11 06:03:52'),
(42, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-11 06:04:10'),
(43, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-11 06:04:15'),
(44, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-11 06:04:23'),
(45, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-11 06:04:28'),
(46, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-19 04:02:56'),
(47, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-19 05:00:47'),
(48, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-19 05:04:05'),
(49, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-19 05:04:18'),
(50, 6, 'Logged In', 'User logged in successfully', '::1', '2026-02-19 05:04:25'),
(51, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-19 05:08:14'),
(52, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-19 05:44:52'),
(53, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-19 05:51:24'),
(54, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-19 05:51:30'),
(55, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-19 05:51:44'),
(56, 9, 'Logged Out', 'User logged out successfully', '::1', '2026-02-19 06:33:16'),
(63, 16, 'Account Created', 'User registered as farmer', '::1', '2026-02-19 07:20:13'),
(64, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-20 13:27:36'),
(65, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-20 13:28:17'),
(67, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-21 08:28:38'),
(68, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-21 09:19:56'),
(69, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-21 09:20:01'),
(70, 9, 'Updated Crop', 'Updated crop: sdsdfsfs', '::1', '2026-02-21 09:20:18'),
(71, 9, 'Updated Crop', 'Updated crop: sdsdfsfs', '::1', '2026-02-21 09:25:22'),
(72, 9, 'Updated Crop', 'Updated crop: sdsdfsfs', '::1', '2026-02-21 09:25:29'),
(73, 9, 'Logged Out', 'User logged out successfully', '::1', '2026-02-21 09:28:18'),
(74, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-21 09:28:24'),
(75, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-21 09:42:11'),
(76, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-21 09:42:20'),
(77, 9, 'Logged Out', 'User logged out successfully', '::1', '2026-02-21 10:12:57'),
(78, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-21 10:13:03'),
(79, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-21 10:18:33'),
(80, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-21 10:18:39'),
(81, 11, 'Logged Out', 'User logged out successfully', '::1', '2026-02-21 10:18:50'),
(82, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-21 10:18:57'),
(83, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-21 10:22:33'),
(84, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-21 10:22:38'),
(85, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-21 10:26:24'),
(86, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-21 10:26:29'),
(87, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-21 10:26:53'),
(88, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-21 10:30:23'),
(89, 6, 'Logged In', 'User logged in successfully', '::1', '2026-02-21 10:30:29'),
(90, 6, 'Logged Out', 'User logged out successfully', '::1', '2026-02-21 12:24:19'),
(91, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-23 05:41:33'),
(92, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-23 05:48:57'),
(93, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-23 05:49:02'),
(94, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-23 05:53:26'),
(95, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-23 19:54:30'),
(96, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-23 19:58:14'),
(97, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-23 19:58:20'),
(98, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-23 20:00:40'),
(99, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-23 20:00:46'),
(100, 9, 'Logged Out', 'User logged out successfully', '::1', '2026-02-23 20:33:23'),
(101, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-23 20:33:40'),
(102, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-24 00:41:37'),
(103, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-24 07:13:10'),
(104, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-25 13:41:52'),
(105, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-25 13:42:46'),
(106, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-25 13:42:55'),
(107, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-25 13:43:02'),
(108, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-25 13:43:08'),
(109, 9, 'Logged Out', 'User logged out successfully', '::1', '2026-02-25 13:48:56'),
(110, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-25 13:49:01'),
(111, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-25 13:49:52'),
(112, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-25 13:49:57'),
(113, 9, 'Logged Out', 'User logged out successfully', '::1', '2026-02-25 13:50:47'),
(114, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-25 13:50:52'),
(115, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-25 15:10:35'),
(116, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-25 15:10:42'),
(117, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-25 15:17:38'),
(118, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-25 15:17:43'),
(119, 9, 'Logged Out', 'User logged out successfully', '::1', '2026-02-25 16:33:06'),
(120, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-25 16:33:15'),
(121, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-26 14:55:45'),
(122, 11, 'Logged Out', 'User logged out successfully', '::1', '2026-02-26 15:07:28'),
(123, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-26 15:07:35'),
(124, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-26 15:14:10'),
(125, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-26 15:20:34'),
(126, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-26 15:20:41'),
(127, 11, 'Logged Out', 'User logged out successfully', '::1', '2026-02-26 16:23:10'),
(128, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-26 16:23:17'),
(129, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 04:35:02'),
(130, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-27 04:55:43'),
(131, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 04:55:49'),
(132, 10, 'Logged Out', 'User logged out successfully', '::1', '2026-02-27 06:19:56'),
(133, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 06:20:05'),
(134, 11, 'Logged Out', 'User logged out successfully', '::1', '2026-02-27 06:20:46'),
(135, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 06:20:50'),
(136, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-27 06:22:12'),
(137, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 06:22:26'),
(138, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 07:11:31'),
(139, 11, 'Logged Out', 'User logged out successfully', '::1', '2026-02-27 07:11:53'),
(140, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 07:12:02'),
(141, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 07:13:11'),
(142, 11, 'Logged Out', 'User logged out successfully', '::1', '2026-02-27 07:42:59'),
(143, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 07:43:25'),
(144, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-27 07:49:11'),
(145, 11, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 07:49:18'),
(146, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 07:49:44'),
(147, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-27 08:19:22'),
(148, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 08:19:27'),
(149, 9, 'Logged Out', 'User logged out successfully', '::1', '2026-02-27 08:19:42'),
(150, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 08:19:53'),
(151, 8, 'Logged Out', 'User logged out successfully', '::1', '2026-02-27 08:19:59'),
(152, 9, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 08:20:03'),
(153, 9, 'Logged Out', 'User logged out successfully', '::1', '2026-02-27 08:33:15'),
(154, 10, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 08:33:21'),
(155, 8, 'Logged In', 'User logged in successfully', '::1', '2026-02-27 15:30:56'),
(156, 5, 'Logged In', 'User logged in successfully', '::1', '2026-02-28 00:42:35'),
(157, 8, 'Logged In', 'User logged in successfully', '::1', '2026-03-01 17:06:00');

-- --------------------------------------------------------

--
-- Table structure for table `admin_announcements`
--

CREATE TABLE `admin_announcements` (
  `id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `expiry_date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `buyer_offers`
--

CREATE TABLE `buyer_offers` (
  `id` int(11) NOT NULL,
  `buyer_name` varchar(100) NOT NULL,
  `contact_number` varchar(50) DEFAULT NULL,
  `crop_name` varchar(100) NOT NULL,
  `offer_price` decimal(10,2) NOT NULL,
  `status` enum('Pending','Accepted','Rejected') NOT NULL DEFAULT 'Pending',
  `date_offered` date NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `buyer_offers`
--

INSERT INTO `buyer_offers` (`id`, `buyer_name`, `contact_number`, `crop_name`, `offer_price`, `status`, `date_offered`) VALUES
(1, 'Legazpi Market', NULL, 'Eggplant', 40.00, 'Pending', '2025-04-12'),
(2, 'Tabaco Buyers', NULL, 'Rice', 60.00, 'Accepted', '2025-04-10'),
(3, 'Daraga Trading', NULL, 'Corn', 45.00, 'Pending', '2025-04-11'),
(7, 'Test Buyer', NULL, 'Test Productsdfds', 44.00, 'Pending', '2026-01-30'),
(8, 'Test Buyer', NULL, 'Test Productsdfds', 40.00, 'Pending', '2026-01-31'),
(11, 'Test Buyer', NULL, 'Chili', 144.00, 'Pending', '2026-02-01'),
(12, 'Test Buyer', NULL, 'sdsdfsfs', 54.00, 'Accepted', '2026-02-06');

-- --------------------------------------------------------

--
-- Table structure for table `crops`
--

CREATE TABLE `crops` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `crop_name` varchar(100) NOT NULL,
  `grade` varchar(50) DEFAULT NULL,
  `price` decimal(10,2) NOT NULL,
  `wholesale_price` decimal(10,2) DEFAULT 0.00,
  `retail_price` decimal(10,2) DEFAULT 0.00,
  `quantity` decimal(10,2) NOT NULL,
  `harvest_date` date NOT NULL,
  `available_until` date NOT NULL,
  `description` text DEFAULT NULL,
  `image` varchar(255) DEFAULT NULL,
  `status` enum('available','reserved','sold') NOT NULL DEFAULT 'available',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `crops`
--

INSERT INTO `crops` (`id`, `user_id`, `crop_name`, `grade`, `price`, `wholesale_price`, `retail_price`, `quantity`, `harvest_date`, `available_until`, `description`, `image`, `status`, `created_at`) VALUES
(1, 2, 'Rice', 'Grade A', 50.00, 50.00, 50.00, 1000.00, '2026-04-15', '2025-05-15', 'Premium fancy rice', NULL, 'available', '2026-01-26 05:51:42'),
(2, 2, 'Corn', 'Sweet Yellow', 35.00, 35.00, 35.00, 500.00, '2026-04-20', '2025-05-20', 'Sweet yellow corn', NULL, 'available', '2026-01-26 05:51:42'),
(3, 2, 'Eggplant', 'Long Purple', 60.00, 60.00, 60.00, 200.00, '2026-04-10', '2025-04-30', 'Fresh long purple eggplant', NULL, 'available', '2026-01-26 05:51:42'),
(4, 2, 'Tomato', 'Roma', 70.00, 70.00, 70.00, 300.00, '2026-04-12', '2025-04-25', 'Ripe red tomatoes', NULL, 'available', '2026-01-26 05:51:42'),
(5, 2, 'Bitter Gourd', 'Native', 85.00, 85.00, 85.00, 150.00, '2026-04-18', '2025-05-01', 'Fresh bitter gourd', NULL, 'available', '2026-01-26 05:51:42'),
(6, 2, 'Watermelon', 'Sweet Red', 45.00, 45.00, 45.00, 400.00, '2026-05-01', '2025-05-15', 'Juicy sweet watermelon', NULL, 'available', '2026-01-26 05:51:42'),
(7, 2, 'Peanut', 'Native', 90.00, 90.00, 90.00, 250.00, '2026-04-25', '2025-06-01', 'Dried raw peanuts', NULL, 'available', '2026-01-26 05:51:42'),
(8, 2, 'Chili', 'Siling Labuyo', 150.00, 150.00, 150.00, 50.00, '2026-04-05', '2025-04-20', 'Spicy hot chili', NULL, 'available', '2026-01-26 05:51:42'),
(9, 2, 'Okra', 'Smooth Green', 55.00, 55.00, 55.00, 180.00, '2026-04-14', '2025-04-28', 'Tender okra pods', NULL, 'available', '2026-01-26 05:51:42'),
(10, 2, 'Melon', 'Honeydew', 50.00, 50.00, 50.00, 300.00, '2026-05-05', '2025-05-20', 'Sweet honeydew melon', NULL, 'available', '2026-01-26 05:51:42'),
(11, 2, 'Sweet Potato', 'VSP6', 40.00, 40.00, 40.00, 600.00, '2026-04-22', '2025-05-30', 'Orange fleshy sweet potato', NULL, 'available', '2026-01-26 05:51:42'),
(12, 2, 'Carrot', 'Imperator', 100.00, 100.00, 100.00, 120.00, '2026-04-08', '2025-04-30', 'Crunchy orange carrots', NULL, 'available', '2026-01-26 05:51:42'),
(13, 2, 'Cucumber', 'Green Slicer', 30.00, 30.00, 30.00, 200.00, '2026-04-16', '2025-04-30', 'Crisp fresh cucumber', NULL, 'available', '2026-01-26 05:51:42'),
(14, 2, 'Rice', 'Sinandomeng', 48.00, 48.00, 48.00, 1200.00, '2026-04-18', '2025-05-20', 'Local commercial rice', NULL, 'available', '2026-01-26 05:51:42'),
(15, 2, 'Corn', 'White Corn', 32.00, 32.00, 32.00, 450.00, '2026-04-22', '2025-05-25', 'Lagkitan white corn', NULL, 'available', '2026-01-26 05:51:42'),
(16, 2, 'Eggplant', 'Round Green', 58.00, 58.00, 58.00, 180.00, '2026-04-15', '2025-05-05', 'Round green variety', NULL, 'available', '2026-01-26 05:51:42'),
(17, 2, 'Tomato', 'Cherry', 120.00, 120.00, 120.00, 50.00, '2026-04-20', '2025-05-01', 'Sweet cherry tomatoes', NULL, 'available', '2026-01-26 05:51:42'),
(18, 2, 'Bitter Gourd', 'Hybrid', 90.00, 90.00, 90.00, 100.00, '2026-04-25', '2025-05-10', 'Large hybrid ampalaya', NULL, 'available', '2026-01-26 05:51:42'),
(19, 2, 'Watermelon', 'Yellow Flesh', 55.00, 55.00, 55.00, 300.00, '2026-05-10', '2025-05-25', 'Unique yellow watermelon', NULL, 'available', '2026-01-26 05:51:42'),
(20, 2, 'Peanut', 'Adobo Style', 110.00, 110.00, 110.00, 100.00, '2026-05-01', '2025-06-01', 'Processed cooked peanuts', NULL, 'available', '2026-01-26 05:51:42'),
(21, 2, 'Chili', 'Red Bell', 200.00, 200.00, 200.00, 40.00, '2026-04-10', '2025-04-30', 'Sweet red bell pepper', NULL, 'available', '2026-01-26 05:51:42'),
(22, 2, 'Okra', 'Red Burgundy', 60.00, 60.00, 60.00, 150.00, '2026-04-18', '2025-05-02', 'Red variety okra', NULL, 'available', '2026-01-26 05:51:42'),
(23, 2, 'Melon', 'Cantaloupe', 55.00, 55.00, 55.00, 350.00, '2026-05-10', '2025-05-25', 'Fragrant cantaloupe', NULL, 'available', '2026-01-26 05:51:42'),
(24, 2, 'Sweet Potato', 'Purple', 45.00, 45.00, 45.00, 500.00, '2026-04-25', '2025-06-01', 'Purple yam ube type', NULL, 'available', '2026-01-26 05:51:42'),
(25, 2, 'Carrot', 'Nantes', 110.00, 110.00, 110.00, 100.00, '2026-04-12', '2025-05-01', 'Sweet nantes carrot', NULL, 'available', '2026-01-26 05:51:42'),
(26, 2, 'Cucumber', 'Pickling', 35.00, 35.00, 35.00, 150.00, '2026-04-20', '2025-05-10', 'Small pickling cucumber', NULL, 'available', '2026-01-26 05:51:42'),
(27, 2, 'Rice', 'Brown Rice', 65.00, 65.00, 65.00, 800.00, '2026-04-25', '2025-06-01', 'Healthy organic brown rice', NULL, 'available', '2026-01-26 05:51:42'),
(28, 2, 'Corn', 'Purple Corn', 40.00, 40.00, 40.00, 300.00, '2026-04-28', '2025-05-28', 'Antioxidant rich corn', NULL, 'available', '2026-01-26 05:51:42'),
(29, 2, 'Eggplant', 'Striped', 62.00, 62.00, 62.00, 150.00, '2026-04-18', '2025-05-10', 'Caiden striped eggplant', NULL, 'available', '2026-01-26 05:51:42'),
(30, 2, 'Tomato', 'Beefsteak', 80.00, 80.00, 80.00, 200.00, '2026-04-22', '2025-05-05', 'Large slicing tomatoes', NULL, 'available', '2026-01-26 05:51:42'),
(31, 2, 'Bitter Gourd', 'Indian', 95.00, 95.00, 95.00, 80.00, '2026-04-30', '2025-05-15', 'Spiky indian karela', NULL, 'available', '2026-01-26 05:51:42'),
(32, 2, 'Watermelon', 'Seedless', 60.00, 60.00, 60.00, 350.00, '2026-05-15', '2025-05-30', 'Premium seedless watermelon', NULL, 'available', '2026-01-26 05:51:42'),
(33, 2, 'Rice', 'Jasmine', 55.00, 55.00, 55.00, 900.00, '2026-04-20', '2025-05-25', 'Aromatic jasmine rice', NULL, 'available', '2026-01-26 05:51:42'),
(34, 2, 'Corn', 'Japanese Sweet', 45.00, 45.00, 45.00, 400.00, '2026-04-25', '2025-05-25', 'Super sweet corn', NULL, 'available', '2026-01-26 05:51:42'),
(35, 2, 'Eggplant', 'White', 65.00, 65.00, 65.00, 100.00, '2026-04-20', '2025-05-15', 'Pure white eggplant', NULL, 'available', '2026-01-26 05:51:42'),
(36, 2, 'Tomato', 'Yellow Pear', 90.00, 90.00, 90.00, 80.00, '2026-04-25', '2025-05-10', 'Small yellow tomatoes', NULL, 'available', '2026-01-26 05:51:42'),
(37, 2, 'Bitter Gourd', 'White', 100.00, 100.00, 100.00, 50.00, '2026-05-01', '2025-05-20', 'Rare white ampalaya', NULL, 'available', '2026-01-26 05:51:42'),
(38, 2, 'Watermelon', 'Sugar Baby', 40.00, 40.00, 40.00, 500.00, '2026-05-10', '2025-06-01', 'Small round watermelon', NULL, 'available', '2026-01-26 05:51:42'),
(39, 2, 'Rice', 'Dinorado', 52.00, 52.00, 52.00, 1100.00, '2026-04-18', '2025-05-20', 'Soft dinorado rice', NULL, 'available', '2026-01-26 05:51:42'),
(40, 2, 'Corn', 'Waxy Corn', 30.00, 30.00, 30.00, 600.00, '2026-04-22', '2025-05-20', 'Chewy waxy corn', NULL, 'available', '2026-01-26 05:51:42'),
(41, 2, 'Eggplant', 'Thai', 70.00, 70.00, 70.00, 120.00, '2026-04-25', '2025-05-15', 'Small round thai eggplant', NULL, 'available', '2026-01-26 05:51:42'),
(42, 2, 'Tomato', 'Green', 50.00, 50.00, 50.00, 150.00, '2026-04-20', '2025-05-05', 'Unripe green tomatoes', NULL, 'available', '2026-01-26 05:51:42'),
(43, 2, 'Peanut', 'Boiled', 80.00, 80.00, 80.00, 300.00, '2026-04-28', '2025-05-15', 'Freshly boiled peanuts', NULL, 'available', '2026-01-26 05:51:42'),
(44, 2, 'Chili', 'Habanero', 250.00, 250.00, 250.00, 30.00, '2026-04-15', '2025-05-01', 'Extremely hot chili', NULL, 'available', '2026-01-26 05:51:42'),
(45, 2, 'Okra', 'Star of David', 65.00, 65.00, 65.00, 100.00, '2026-04-20', '2025-05-10', 'Thick heirloom okra', NULL, 'available', '2026-01-26 05:51:42'),
(46, 2, 'Melon', 'Canary', 60.00, 60.00, 60.00, 250.00, '2026-05-15', '2025-05-30', 'Bright yellow melon', NULL, 'available', '2026-01-26 05:51:42'),
(47, 2, 'Sweet Potato', 'White', 38.00, 38.00, 38.00, 700.00, '2026-04-25', '2025-06-01', 'Dry white variety', NULL, 'available', '2026-01-26 05:51:42'),
(48, 2, 'Carrot', 'Baby', 120.00, 120.00, 120.00, 80.00, '2026-04-15', '2025-05-01', 'Peeled baby carrots', NULL, 'available', '2026-01-26 05:51:42'),
(49, 2, 'Cucumber', 'English', 45.00, 45.00, 45.00, 180.00, '2026-04-22', '2025-05-10', 'Long english cucumber', NULL, 'available', '2026-01-26 05:51:42'),
(50, 2, 'Rice', 'Black Rice', 70.00, 70.00, 70.00, 500.00, '2026-04-28', '2025-06-01', 'Superfood black rice', NULL, 'available', '2026-01-26 05:51:42'),
(53, 8, 'Test Productsdfds', 'B', 45.00, 45.00, 45.00, 45.00, '2026-01-27', '2026-02-05', 'rew', NULL, 'available', '2026-01-27 11:03:39'),
(54, 8, 'Test Product', '3', 999.00, 999.00, 999.00, 120.00, '2026-03-06', '2026-03-20', 'asda', NULL, 'available', '2026-02-01 16:42:23'),
(55, 9, 'Test Productsdfdssdfsdfsd', '11', 14.00, 14.00, 14.00, 56.00, '2026-02-06', '2026-02-20', 'dfds', NULL, 'reserved', '2026-02-06 08:00:59'),
(56, 9, 'sdfsddfdf', 'A', 6.00, 6.00, 6.00, 64.00, '2026-02-06', '2026-02-26', '4', NULL, 'sold', '2026-02-06 08:16:38'),
(57, 9, 'sdsdfsfs', '45', 56.00, 56.00, 56.00, 555.00, '2026-02-06', '2026-03-14', 'dfds', NULL, 'sold', '2026-02-06 08:43:53');

-- --------------------------------------------------------

--
-- Table structure for table `market_prices`
--

CREATE TABLE `market_prices` (
  `id` int(11) NOT NULL,
  `crop_name` varchar(100) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `trend` enum('rising','falling','stable') NOT NULL DEFAULT 'stable',
  `recorded_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `type` varchar(50) DEFAULT 'info',
  `title` varchar(255) NOT NULL,
  `message` text DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `message`, `is_read`, `created_at`) VALUES
(1, 1, 'info', 'New User Registration', 'A new farmer has registered.', 0, '2026-02-01 18:02:31'),
(2, 1, 'warning', 'System Update', 'System maintenance scheduled for tonight.', 0, '2026-02-01 18:02:31'),
(3, 2, 'success', 'Offer Received', 'Buyer Legazpi Market made an offer on your Rice.', 0, '2026-02-01 18:02:31'),
(4, 2, 'warning', 'Weather Alert', 'Heavy rain expected tomorrow.', 0, '2026-02-01 18:02:31'),
(5, 3, 'info', 'Distribution Pending', 'New schedule request pending approval.', 0, '2026-02-01 18:02:31'),
(6, 4, 'success', 'Offer Received', 'Buyer Legazpi Market made an offer on your Rice.', 0, '2026-02-01 18:02:31'),
(7, 4, 'warning', 'Weather Alert', 'Heavy rain expected tomorrow.', 0, '2026-02-01 18:02:31'),
(8, 5, 'info', 'New User Registration', 'A new farmer has registered.', 0, '2026-02-01 18:02:31'),
(9, 5, 'warning', 'System Update', 'System maintenance scheduled for tonight.', 0, '2026-02-01 18:02:31'),
(10, 6, 'success', 'Offer Received', 'Buyer Legazpi Market made an offer on your Rice.', 1, '2026-02-01 18:02:31'),
(11, 6, 'warning', 'Weather Alert', 'Heavy rain expected tomorrow.', 1, '2026-02-01 18:02:31'),
(12, 8, 'info', 'New User Registration', 'A new farmer has registered.', 1, '2026-02-01 18:02:31'),
(13, 8, 'warning', 'System Update', 'System maintenance scheduled for tonight.', 1, '2026-02-01 18:02:31'),
(14, 9, 'success', 'Offer Received', 'Buyer Legazpi Market made an offer on your Rice.', 1, '2026-02-01 18:02:31'),
(15, 9, 'warning', 'Weather Alert', 'Heavy rain expected tomorrow.', 1, '2026-02-01 18:02:31'),
(16, 1, 'info', 'New Crop Added', 'Farmer Test Farmer2 added a new crop: sdsdfsfs', 0, '2026-02-06 08:43:53'),
(17, 5, 'info', 'New Crop Added', 'Farmer Test Farmer2 added a new crop: sdsdfsfs', 0, '2026-02-06 08:43:53'),
(18, 8, 'info', 'New Crop Added', 'Farmer Test Farmer2 added a new crop: sdsdfsfs', 1, '2026-02-06 08:43:53'),
(19, 3, 'info', 'New Crop Added', 'Farmer Test Farmer2 added a new crop: sdsdfsfs', 0, '2026-02-06 08:43:53'),
(20, 11, 'info', 'New Crop Added', 'Farmer Test Farmer2 added a new crop: sdsdfsfs', 0, '2026-02-06 08:43:53'),
(21, 9, 'success', 'Offer Received', 'Buyer Test Buyer made an offer on your sdsdfsfs: ₱54.00', 0, '2026-02-06 08:44:34'),
(22, 10, 'success', 'Offer Accepted', 'Farmer Test Farmer2 accepted your offer for sdsdfsfs!', 1, '2026-02-06 08:45:14'),
(23, 1, 'success', 'Product Bought', 'Farmer Test Farmer2 sold sdsdfsfs to Test Buyer for ₱54.00', 0, '2026-02-06 08:45:14'),
(24, 5, 'success', 'Product Bought', 'Farmer Test Farmer2 sold sdsdfsfs to Test Buyer for ₱54.00', 0, '2026-02-06 08:45:14'),
(25, 8, 'success', 'Product Bought', 'Farmer Test Farmer2 sold sdsdfsfs to Test Buyer for ₱54.00', 0, '2026-02-06 08:45:14'),
(26, 3, 'success', 'Product Bought', 'Farmer Test Farmer2 sold sdsdfsfs to Test Buyer for ₱54.00', 0, '2026-02-06 08:45:14'),
(27, 11, 'success', 'Product Bought', 'Farmer Test Farmer2 sold sdsdfsfs to Test Buyer for ₱54.00', 0, '2026-02-06 08:45:14'),
(28, 2, 'weather', 'Weather Alert', 'Weather Alert for Calamba: Please check the forecast module for upcoming conditions.', 0, '2026-02-19 04:16:17'),
(29, 4, 'weather', 'Weather Alert', 'Weather Alert for Calamba: Please check the forecast module for upcoming conditions.', 0, '2026-02-19 04:16:17'),
(30, 6, 'weather', 'Weather Alert', 'Weather Alert for Calamba: Please check the forecast module for upcoming conditions.', 1, '2026-02-19 04:16:17'),
(31, 9, 'weather', 'Weather Alert', 'Weather Alert for Calamba: Please check the forecast module for upcoming conditions.', 0, '2026-02-19 04:16:17'),
(32, 1, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 06:33:43'),
(33, 5, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 06:33:43'),
(34, 8, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 06:33:43'),
(35, 1, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 06:47:03'),
(36, 5, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 06:47:03'),
(37, 8, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 06:47:03'),
(38, 1, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 07:02:42'),
(39, 5, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 07:02:42'),
(40, 8, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 07:02:42'),
(41, 1, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 07:10:52'),
(42, 5, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 07:10:52'),
(43, 8, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 07:10:52'),
(44, 1, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 07:20:13'),
(45, 5, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 07:20:13'),
(46, 8, 'info', 'New User Registration', 'A new farmer named Saitama has registered.', 0, '2026-02-19 07:20:13'),
(47, 1, 'info', 'New User Registration', 'A new farmer named Test 123 has registered.', 0, '2026-02-20 13:28:36'),
(48, 5, 'info', 'New User Registration', 'A new farmer named Test 123 has registered.', 0, '2026-02-20 13:28:36'),
(49, 8, 'info', 'New User Registration', 'A new farmer named Test 123 has registered.', 0, '2026-02-20 13:28:36');

-- --------------------------------------------------------

--
-- Table structure for table `otp_tokens`
--

CREATE TABLE `otp_tokens` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `otp_code` varchar(6) NOT NULL,
  `expires_at` datetime NOT NULL,
  `used` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `otp_tokens`
--

INSERT INTO `otp_tokens` (`id`, `user_id`, `otp_code`, `expires_at`, `used`, `created_at`) VALUES
(4, 15, '400592', '2026-02-19 15:15:52', 0, '2026-02-19 07:10:52'),
(5, 16, '984002', '2026-02-19 15:25:13', 1, '2026-02-19 07:20:13'),
(6, 17, '718307', '2026-02-20 21:33:36', 0, '2026-02-20 13:28:36');

-- --------------------------------------------------------

--
-- Table structure for table `schedule_distribution`
--

CREATE TABLE `schedule_distribution` (
  `id` int(11) NOT NULL,
  `distribution_type` varchar(255) NOT NULL,
  `quantity` varchar(50) NOT NULL,
  `recipient` varchar(255) NOT NULL,
  `status` enum('Accepted','Pending','Rejected') DEFAULT 'Pending',
  `officer` varchar(255) DEFAULT NULL,
  `distribution_date` date NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `schedule_distribution`
--

INSERT INTO `schedule_distribution` (`id`, `distribution_type`, `quantity`, `recipient`, `status`, `officer`, `distribution_date`, `created_at`) VALUES
(1, 'test', '1', '1', 'Pending', NULL, '2026-01-31', '2026-01-30 14:19:40'),
(2, 'asd', '4', '4', 'Accepted', NULL, '2026-02-07', '2026-01-30 14:23:32'),
(3, 'asdadasd', '56', '69', 'Pending', NULL, '2026-02-07', '2026-01-30 15:44:03'),
(4, 'csdw', '8', 'sd', 'Pending', NULL, '2026-01-09', '2026-01-31 06:37:39'),
(5, 'dsfsdfscscs', '4', '69', 'Pending', NULL, '2026-02-14', '2026-02-01 17:12:06'),
(6, 'Seeds', '50', 'John Doe', 'Accepted', 'Officer Jayson', '2026-04-12', '2026-03-01 18:47:45');

-- --------------------------------------------------------

--
-- Table structure for table `translations_cache`
--

CREATE TABLE `translations_cache` (
  `id` int(11) NOT NULL,
  `source_text` text DEFAULT NULL,
  `source_lang` varchar(5) DEFAULT NULL,
  `target_lang` varchar(5) DEFAULT NULL,
  `translated_text` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `translations_cache`
--

INSERT INTO `translations_cache` (`id`, `source_text`, `source_lang`, `target_lang`, `translated_text`) VALUES
(1, 'Farmer Dashboard', 'en', 'fil', 'Dashboard ng Magsasaka'),
(2, 'Settings', 'en', 'fil', 'Mga Setting'),
(3, 'Language', 'en', 'fil', 'Wika'),
(4, 'Log out?', 'en', 'fil', 'Mag-log out?'),
(5, 'Log out', 'en', 'fil', 'Email Address *'),
(6, 'Overview', 'en', 'fil', 'Pangkalahatang-ideya'),
(7, 'Weather Forecast', 'en', 'fil', 'Taya ng Panahon'),
(8, 'Crop Management', 'en', 'fil', 'Pamamahala ng Pananim'),
(9, 'Available Crops', 'en', 'fil', 'Magagamit na mga pananim'),
(10, 'Market Prices', 'en', 'fil', 'Mga Presyo sa Market'),
(11, 'Schedule Distribution', 'en', 'fil', 'Iskedyul ng Pamamahagi'),
(12, 'Buyer Offers', 'en', 'fil', 'Mga Alok ng Mamimili'),
(13, 'Activity Log', 'en', 'fil', 'Talaan ng Aktibidad'),
(14, 'Market Price', 'en', 'fil', 'Presyo sa merkado'),
(15, 'Farmer | AniTech', 'en', 'fil', 'Magsasaka | AniTech'),
(16, 'Logout', 'en', 'fil', 'Email Address *'),
(17, 'English', 'en', 'fil', 'Ingles'),
(18, 'Save Changes', 'en', 'fil', 'I-save ang Mga Pagbabago'),
(19, 'Edit Name', 'en', 'fil', 'I-edit ang Pangalan'),
(20, 'Full Name', 'en', 'fil', 'Buong Pangalan'),
(21, 'Update Name', 'en', 'fil', 'I-update ang Pangalan'),
(22, 'Current Password', 'en', 'fil', 'Kasalukuyang Password'),
(23, 'New Password', 'en', 'fil', 'Username Password'),
(24, 'Confirm New Password', 'en', 'fil', 'Login Password'),
(25, 'Update Password', 'en', 'fil', 'I-update ang password'),
(26, 'All Trends', 'en', 'fil', 'Lahat ng Mga Trend'),
(27, 'Bitter Gourd', 'en', 'fil', 'Mapait na Gourd'),
(28, 'Carrot', 'en', 'fil', 'Karot'),
(29, 'Cucumber', 'en', 'fil', 'Pipino'),
(30, 'Eggplant', 'en', 'fil', 'Talong'),
(31, 'Peanut', 'en', 'fil', 'Mani'),
(32, 'Rice', 'en', 'fil', 'Bigas'),
(33, 'Sweet Potato', 'en', 'fil', 'Kamote'),
(34, 'Tomato', 'en', 'fil', 'Kamatis'),
(35, 'Watermelon', 'en', 'fil', 'Pakwan'),
(36, 'Weather', 'en', 'fil', 'Panahon'),
(37, 'Crop Prediction', 'en', 'fil', 'Hula ng Pag-crop'),
(38, 'Seasonal', 'en', 'fil', 'Pana-panahong'),
(39, 'Demand', 'en', 'fil', 'Kahilingan'),
(40, 'Search...', 'en', 'fil', 'Paghahanap...'),
(41, 'Loading...', 'en', 'fil', 'Naglo-load...'),
(42, 'Grade', 'en', 'fil', 'Grado'),
(43, 'Value', 'en', 'fil', 'Halaga'),
(44, 'Harvest', 'en', 'fil', 'Pag-aani'),
(45, 'Latest addition to the inventory.', 'en', 'fil', 'Pinakabagong karagdagan sa imbentaryo.'),
(46, 'Scheduling Distribution', 'en', 'fil', 'Pag-iiskedyul ng Pamamahagi'),
(47, 'Type', 'en', 'fil', 'Uri'),
(48, 'Status', 'en', 'fil', 'Katayuan'),
(49, 'Date', 'en', 'fil', 'Petsa'),
(50, 'Pending', 'en', 'fil', 'Nakabinbin'),
(51, 'Accepted', 'en', 'fil', 'Tinanggap'),
(52, 'Buyer', 'en', 'fil', 'Mamimili'),
(53, 'Offer', 'en', 'fil', 'Mag-alok'),
(54, 'Saved Successfully', 'en', 'fil', 'Matagumpay na nai-save'),
(55, 'No notifications', 'en', 'fil', 'Walang mga abiso'),
(56, 'Mark all as read', 'en', 'fil', 'Markahan ang lahat bilang nabasa'),
(57, 'January', 'en', 'fil', 'Enero'),
(58, 'February', 'en', 'fil', 'Pebrero'),
(59, 'March', 'en', 'fil', 'Marso'),
(60, 'April', 'en', 'fil', 'Abril'),
(61, 'May', 'en', 'fil', 'Mayo'),
(62, 'June', 'en', 'fil', 'Hunyo'),
(63, 'July', 'en', 'fil', 'Hulyo'),
(64, 'August', 'en', 'fil', 'Agosto'),
(65, 'September', 'en', 'fil', 'Setyembre'),
(66, 'October', 'en', 'fil', 'Oktubre'),
(67, 'November', 'en', 'fil', 'Nobyembre'),
(68, 'December', 'en', 'fil', 'Disyembre'),
(69, 'Not Set', 'en', 'fil', 'Hindi Itinakda'),
(70, 'Invalid Date', 'en', 'fil', 'Hindi wastong petsa'),
(71, 'Click for details', 'en', 'fil', 'Mag-click para sa mga detalye'),
(72, 'Previous Month', 'en', 'fil', 'Nakaraang Buwan'),
(73, 'Next Month', 'en', 'fil', 'Susunod na buwan'),
(74, 'Sun', 'en', 'fil', 'Araw'),
(75, 'Mon', 'en', 'fil', 'Lunes'),
(76, 'Wed', 'en', 'fil', 'Miyerkules'),
(77, 'Fri', 'en', 'fil', 'Biyernes'),
(78, 'Sat', 'en', 'fil', 'Umupo'),
(79, 'Planting', 'en', 'fil', 'Pagtatanim'),
(80, 'High Demand', 'en', 'fil', 'Mataas na Demand'),
(81, 'AniTech | Weather Forecast', 'en', 'fil', 'AniTech | Taya ng Panahon'),
(82, 'Real-time condition for your crops.', 'en', 'fil', 'Real-time na kondisyon para sa iyong mga pananim.'),
(83, 'Loading weather data...', 'en', 'fil', 'Paglo-load ng data ng panahon ...'),
(84, 'Weather Impact Analysis', 'en', 'fil', 'Pagsusuri sa Epekto ng Panahon'),
(85, 'How current forecasts may affect your crops', 'en', 'fil', 'Paano Maaaring Makaapekto ang Kasalukuyang Mga Pagtataya sa Iyong Mga Pananim'),
(86, 'Moderate Rain Expected', 'en', 'fil', 'Inaasahan ang katamtamang pag-ulan'),
(87, 'Wednesday to Thursday', 'en', 'fil', 'Miyerkules hanggang Huwebes'),
(88, 'Impact on Rice Crops:', 'en', 'fil', 'Epekto sa mga pananim ng palay:'),
(89, 'Increased water levels will benefit current growth stage', 'en', 'fil', 'Ang pagtaas ng antas ng tubig ay makikinabang sa kasalukuyang yugto ng paglago'),
(90, 'Postpone fertilizer application until Friday', 'en', 'fil', 'Ipagpaliban ang aplikasyon ng pataba hanggang Biyernes'),
(91, 'Monitor for potential pest activity after rain', 'en', 'fil', 'Subaybayan ang mga potensyal na aktibidad ng peste pagkatapos ng ulan'),
(92, 'Optimal Growth Conditions', 'en', 'fil', 'Pinakamainam na Kondisyon ng Paglago'),
(93, 'Friday to Sunday', 'en', 'fil', 'Biyernes hanggang Linggo'),
(94, 'Recommended Actions:', 'en', 'fil', 'Mga Inirerekomendang Pagkilos:'),
(95, 'Schedule fertilizer application for Friday afternoon', 'en', 'fil', 'Mag-iskedyul ng aplikasyon ng pataba para sa Biyernes ng hapon'),
(96, 'Ideal conditions for foliar spraying on Saturday', 'en', 'fil', 'Perpektong kondisyon para sa pag-spray ng foliar sa Sabado'),
(97, 'Check irrigation system before weekend', 'en', 'fil', 'Suriin ang sistema ng patubig bago ang katapusan ng linggo'),
(98, 'Profile opened!', 'en', 'fil', 'Binuksan ang profile!'),
(99, 'Settings opened!', 'en', 'fil', 'Binuksan ang mga setting!'),
(100, 'Are you sure you want to log out?', 'en', 'fil', 'Sigurado ka bang gusto mong mag-log out?'),
(101, 'Logged out successfully!', 'en', 'fil', 'Matagumpay na naka-log out!'),
(102, 'Action completed!', 'en', 'fil', 'Nakumpleto ang pagkilos!'),
(103, 'Clear sky', 'en', 'fil', 'Maliwanag na kalangitan'),
(104, 'Mainly clear', 'en', 'fil', 'Higit sa lahat malinaw'),
(105, 'Partly cloudy', 'en', 'fil', 'Bahagyang maulap'),
(106, 'Overcast', 'en', 'fil', 'Maulap'),
(107, 'Fog', 'en', 'fil', 'Hamog'),
(108, 'Depositing rime fog', 'en', 'fil', 'Pagdedeposito ng rime fog'),
(109, 'Light drizzle', 'en', 'fil', 'Banayad na pag-ulan'),
(110, 'Moderate drizzle', 'en', 'fil', 'Katamtamang pag-ulan'),
(111, 'Dense drizzle', 'en', 'fil', 'Siksik na pag-ulan'),
(112, 'Slight rain', 'en', 'fil', 'Bahagyang ulan'),
(113, 'Moderate rain', 'en', 'fil', 'Katamtamang ulan'),
(114, 'Heavy rain', 'en', 'fil', 'Malakas na ulan'),
(115, 'Slight snow', 'en', 'fil', 'Bahagyang niyebe'),
(116, 'Moderate snow', 'en', 'fil', 'Katamtamang niyebe'),
(117, 'Heavy snow', 'en', 'fil', 'Mabigat na niyebe'),
(118, 'Snow grains', 'en', 'fil', 'Mga butil ng niyebe'),
(119, 'Slight rain showers', 'en', 'fil', 'Bahagyang pag-ulan'),
(120, 'Moderate rain showers', 'en', 'fil', 'Katamtamang pag-ulan'),
(121, 'Violent rain showers', 'en', 'fil', 'Marahas na pag-ulan'),
(122, 'Thunderstorm', 'en', 'fil', 'Bagyo'),
(123, 'Thunderstorm with slight hail', 'en', 'fil', 'Bagyo na may bahagyang yelo'),
(124, 'Thunderstorm with heavy hail', 'en', 'fil', 'Bagyo na may malakas na yelo'),
(125, 'Failed to load weather data. Please try again later.', 'en', 'fil', 'Nabigo akong mag-load ng data ng panahon. Mangyaring subukang muli mamaya.'),
(126, 'Unknown', 'en', 'fil', 'Hindi kilala'),
(127, 'Precipitation Probability', 'en', 'fil', 'Posibilidad ng pag-ulan'),
(128, '% Match', 'en', 'fil', '% Tugma'),
(129, 'Trending Down', 'en', 'fil', 'Pagte-trend pababa'),
(130, 'Stable', 'en', 'fil', 'Matatag'),
(131, 'No recommendations found.', 'en', 'fil', 'Walang natagpuan na mga rekomendasyon.'),
(132, 'Failed to load recommendations.', 'en', 'fil', 'Nabigo akong mag-load ng mga rekomendasyon.'),
(133, 'Failed to load forecast', 'en', 'fil', 'Nabigong mag-load ng forecast'),
(134, 'Temperature', 'en', 'fil', 'Temperatura'),
(135, 'Humidity', 'en', 'fil', 'Kahalumigmigan'),
(136, 'Price', 'en', 'fil', 'Presyo'),
(137, 'Name', 'en', 'fil', 'Pangalan'),
(138, 'Contact no.', 'en', 'fil', 'Email Address *'),
(139, 'Reg. Date', 'en', 'fil', 'Reg. Petsa'),
(140, 'Account Type', 'en', 'fil', 'Uri ng Account'),
(141, 'Language preference saved!', 'en', 'fil', 'Nai-save ang kagustuhan sa wika!'),
(142, 'Administrator', 'en', 'fil', 'Tagapangasiwa'),
(143, 'Joined', 'en', 'fil', 'Sumali'),
(144, 'Edit Profile', 'en', 'fil', 'I-edit ang Profile'),
(145, 'Min. 6 characters', 'en', 'fil', 'Min. 6 character'),
(146, 'Repeat new password', 'en', 'fil', 'Password'),
(147, 'Language Preference', 'en', 'fil', 'Kagustuhan sa Wika'),
(148, 'Agri-Extension Offer', 'en', 'fil', 'Alok ng Agri-Extension'),
(149, 'New offer for Chili from Test Buyer at ₱144.00', 'en', 'fil', 'Bagong alok para sa Chili mula sa Test Buyer sa halagang ₱144.00'),
(150, 'New offer for Test Productsdfds from Test Buyer at ₱40.00', 'en', 'fil', 'Bagong alok para sa Mga Produkto ng Pagsubokdfds mula sa Mamimili ng Pagsubok sa ₱ 40.00'),
(151, 'New offer for Test Productsdfds from Test Buyer at ₱44.00', 'en', 'fil', 'Bagong alok para sa Mga Produkto ng Pagsubokdfds mula sa Mamimili ng Pagsubok sa ₱ 44.00'),
(152, 'Live market data will be updated soon.', 'en', 'fil', 'Ang live na data ng merkado ay maa-update sa lalong madaling panahon.'),
(153, 'No available crops at the moment.', 'en', 'fil', 'Walang magagamit na mga pananim sa ngayon.'),
(154, 'No data available', 'en', 'fil', 'Walang magagamit na data'),
(155, 'Crop Details', 'en', 'fil', 'Mga Detalye ng Pag-crop'),
(156, 'Quantity', 'en', 'fil', 'Dami'),
(157, 'Wholesale Price', 'en', 'fil', 'Pakyawan Presyo'),
(158, 'Retail Price', 'en', 'fil', 'Presyo ng Tingi'),
(159, 'Harvest Date', 'en', 'fil', 'Petsa ng Pag-aani'),
(160, 'Available Until', 'en', 'fil', 'Magagamit hanggang sa'),
(161, 'Description', 'en', 'fil', 'Paglalarawan'),
(162, 'Close', 'en', 'fil', 'Isara'),
(163, 'SOLD', 'en', 'fil', 'IBINEBENTA'),
(164, 'RESERVED', 'en', 'fil', 'NAKARESERBA'),
(165, 'AVAILABLE', 'en', 'fil', 'MAGAGAMIT'),
(166, 'Farmer', 'en', 'fil', 'Magsasaka'),
(167, 'Open Calendar', 'en', 'fil', 'Buksan ang Kalendaryo'),
(168, 'Notifications', 'en', 'fil', 'Mga abiso'),
(169, 'Temperature Trend (Next 7 Days)', 'en', 'fil', 'Trend ng Temperatura (Susunod na 7 Araw)'),
(170, 'Current Location', 'en', 'fil', 'Kasalukuyang Lokasyon'),
(171, 'Temperature (°C)', 'en', 'fil', 'Temperatura (° C)'),
(172, 'Humidity (%)', 'en', 'fil', 'Kahalumigmigan (%)'),
(173, 'No new notifications', 'en', 'fil', 'Walang mga bagong abiso'),
(174, 'Prediction for optimal crops this season', 'en', 'fil', 'Hula para sa pinakamainam na pananim ngayong panahon'),
(175, 'Seasonal Crops', 'en', 'fil', 'Mga pana-panahong pananim'),
(176, 'High Demand Crops', 'en', 'fil', 'Mataas na Demand na Mga Pananim'),
(177, 'Search crops...', 'en', 'fil', 'Hanapin ang mga pananim ...'),
(178, 'Refresh', 'en', 'fil', 'I-refresh'),
(179, 'Generating recommendations...', 'en', 'fil', 'Pagbuo ng mga rekomendasyon ...'),
(180, 'Prediction API failed', 'en', 'fil', 'Nabigo ang API ng hula'),
(181, 'High', 'en', 'fil', 'Mataas'),
(182, 'Medium', 'en', 'fil', 'Katamtaman'),
(183, 'Best Season :', 'en', 'fil', 'Pinakamahusay na Panahon :'),
(184, 'Profit Potential :', 'en', 'fil', 'Potensyal na Kita:'),
(185, 'Water Need :', 'en', 'fil', 'Pangangailangan ng Tubig :'),
(186, 'Suitability (Demand)', 'en', 'fil', 'Kaangkupan (Demand)'),
(187, 'Est. Price', 'en', 'fil', 'Est. Presyo'),
(188, 'Error loading predictions. Ensure ML Service is running.', 'en', 'fil', 'Error sa paglo-load ng mga hula. Tiyaking tumatakbo ang ML Service.'),
(189, 'Manage crops listed and ready for sale.', 'en', 'fil', 'Pamahalaan ang mga pananim na nakalista at handa nang ibenta.'),
(190, 'Search by crop name or description...', 'en', 'fil', 'Hanapin ayon sa pangalan o paglalarawan ng crop ...'),
(191, 'All Status', 'en', 'fil', 'Lahat ng Katayuan'),
(192, 'Apply', 'en', 'fil', 'Mag-aplay'),
(193, 'Add New Crop', 'en', 'fil', 'Magdagdag ng Bagong Crop'),
(194, 'Price (Wholesale)', 'en', 'fil', 'Presyo (Pakyawan)'),
(195, 'Qty Available', 'en', 'fil', 'Magagamit ang Qty'),
(196, 'Edit', 'en', 'fil', 'Baguhin'),
(197, 'Remove', 'en', 'fil', 'Alisin'),
(198, 'Black Rice', 'en', 'fil', 'Itim na Bigas'),
(199, 'Baby', 'en', 'fil', 'Sanggol'),
(200, 'Crop Name', 'en', 'fil', 'Pangalan ng Pag-crop'),
(201, 'Grade (e.g., Grade A)', 'en', 'fil', 'Grade (hal., Grade A)'),
(202, 'Quantity (kg)', 'en', 'fil', 'Dami (kg)'),
(203, 'Cancel', 'en', 'fil', 'Kanselahin'),
(204, 'Save Crop', 'en', 'fil', 'I-save ang Pag-crop'),
(205, 'Edit Crop', 'en', 'fil', 'I-edit ang I-crop'),
(206, 'Success', 'en', 'fil', 'Tagumpay'),
(207, 'Crop saved successfully!', 'en', 'fil', 'Matagumpay na nai-save ang ani!'),
(208, 'Failed to save', 'en', 'fil', 'Nabigo na i-save'),
(209, 'Are you sure?', 'en', 'fil', 'Sigurado ka ba?'),
(210, 'You won\'t be able to revert this!', 'en', 'fil', 'Hindi mo ito maibabalik pa!'),
(211, 'Yes, delete it!', 'en', 'fil', 'Oo, tanggalin ito!'),
(212, 'Deleted!', 'en', 'fil', 'Tinanggal!'),
(213, 'Crop has been deleted.', 'en', 'fil', 'Tinanggal na ang crop.'),
(214, 'Failed to delete.', 'en', 'fil', 'Nabigo na tanggalin.'),
(215, 'Price Trackings', 'en', 'fil', 'Mga Pagsubaybay sa Presyo'),
(216, 'Rising Prices', 'en', 'fil', 'Pagtaas ng Mga Presyo'),
(217, 'Falling Prices', 'en', 'fil', 'Bumabagsak na Presyo'),
(218, 'Stable Prices', 'en', 'fil', 'Matatag na Mga Presyo'),
(219, 'Fetching latest market trends...', 'en', 'fil', 'Kunin ang Pinakabagong Mga Trend sa Market ...'),
(220, 'Market prices updated!', 'en', 'fil', 'Na-update ang mga presyo sa merkado!'),
(221, 'Failed to load market data. Ensure ML Service is running.', 'en', 'fil', 'Nabigo na i-load ang data ng merkado. Tiyaking tumatakbo ang ML Service.'),
(222, 'Forecast:', 'en', 'fil', 'Pagtataya:'),
(223, 'Last Updated', 'en', 'fil', 'Huling na-update'),
(224, 'Details', 'en', 'fil', 'Mga Detalye'),
(225, 'Current Price', 'en', 'fil', 'Kasalukuyang Presyo'),
(226, 'Forecast Price (Next Week)', 'en', 'fil', 'Pagtataya ng presyo (sa susunod na linggo)'),
(227, 'Price Comparison', 'en', 'fil', 'Paghahambing ng Presyo'),
(228, 'View All', 'en', 'fil', 'Tingnan ang Lahat'),
(229, 'Scheduling', 'en', 'fil', 'Pag-iiskedyul'),
(230, 'View recent activities and updates from users.', 'en', 'fil', 'Tingnan ang mga kamakailang aktibidad at update mula sa mga gumagamit.'),
(231, 'Search by user, role, activity...', 'en', 'fil', 'Paghahanap ayon sa gumagamit, tungkulin, aktibidad ...'),
(232, 'All Time', 'en', 'fil', 'Lahat ng Oras'),
(233, 'Today', 'en', 'fil', 'Ngayong araw'),
(234, 'User Name', 'en', 'fil', 'Username'),
(235, 'Role', 'en', 'fil', 'Tungkulin'),
(236, 'Activity', 'en', 'fil', 'Aktibidad'),
(237, 'Date & Time', 'en', 'fil', 'Petsa at Oras'),
(238, 'Agri-Extension Officer', 'en', 'fil', 'Opisyal ng Agri-Extension'),
(239, 'Logged In', 'en', 'fil', 'Email Address *'),
(240, 'User logged in successfully', 'en', 'fil', 'Matagumpay na naka-log in ang user'),
(241, 'Logged Out', 'en', 'fil', 'Email Address *'),
(242, 'User logged out successfully', 'en', 'fil', 'Matagumpay na nag-log out ang user'),
(243, 'Updated Crop', 'en', 'fil', 'Nai-update na Pag-crop'),
(244, 'Updated crop: sdsdfsfs', 'en', 'fil', 'Nai-update na crop: sdsdfsfs'),
(245, 'Account Created', 'en', 'fil', 'Nilikha ang Account'),
(246, 'User registered as farmer', 'en', 'fil', 'Tagagamit na nakarehistro bilang magsasaka'),
(247, 'Updated crop: sdfsddfdf', 'en', 'fil', 'Nai-update na crop: sdfsddfdf'),
(248, 'Accepted Offer', 'en', 'fil', 'Email Address *'),
(249, 'Accepted offer for sdsdfsfs from Test Buyer', 'en', 'fil', 'Tinanggap ang alok para sa sdsdfsfs mula sa Test Buyer'),
(250, 'Made Offer', 'en', 'fil', 'Nag-aalok'),
(251, 'Made offer for sdsdfsfs: ₱54.00', 'en', 'fil', 'Ginawa alok para sa sdsdfsfs: ₱54.00'),
(252, 'Added Crop', 'en', 'fil', 'Idinagdag ang pag-crop'),
(253, 'Added new crop: sdsdfsfs', 'en', 'fil', 'Idinagdag ang bagong crop: sdsdfsfs'),
(254, 'Added new crop: sdfsddfdf', 'en', 'fil', 'Idinagdag ang bagong crop: sdfsddfdf'),
(255, 'Added new crop: Test Productsdfdssdfsdfsd', 'en', 'fil', 'Idinagdag ang bagong crop: Mga Produkto ng Pagsubokdfddsssdfsdfsd'),
(256, 'Activity Details', 'en', 'fil', 'Mga Detalye ng Aktibidad'),
(257, 'User:', 'en', 'fil', 'Gumagamit:'),
(258, 'Role:', 'en', 'fil', 'Tungkulin:'),
(259, 'Activity:', 'en', 'fil', 'Aktibidad:'),
(260, 'Date & Time:', 'en', 'fil', 'Petsa at Oras:'),
(261, 'Details:', 'en', 'fil', 'Mga Detalye:'),
(262, 'Secretary', 'en', 'fil', 'Kalihim'),
(263, 'View Schedule Distribution', 'en', 'fil', 'Tingnan ang Pamamahagi ng Iskedyul'),
(264, 'View Activity Log', 'en', 'fil', 'Tingnan ang Talaan ng Aktibidad'),
(265, 'Manage and track distribution of farm supplies.', 'en', 'fil', 'Pamahalaan at subaybayan ang pamamahagi ng mga suplay ng sakahan.'),
(266, 'Distribution Type', 'en', 'fil', 'Uri ng Pamamahagi'),
(267, 'Received', 'en', 'fil', 'Natanggap'),
(268, 'Action', 'en', 'fil', 'Aksyon'),
(269, 'Received/Recipient', 'en', 'fil', 'Natanggap/Tatanggap'),
(270, 'Rejected', 'en', 'fil', 'Tinanggihan'),
(271, 'Save', 'en', 'fil', 'I-save'),
(272, 'No description provided.', 'en', 'fil', 'Walang ibinigay na paglalarawan.'),
(273, 'Best time for planting rice and corn.', 'en', 'fil', 'Pinakamainam na oras para sa pagtatanim ng palay at mais.'),
(274, 'Crop Status: ', 'en', 'fil', 'Katayuan ng Pag-crop: '),
(275, 'Posted Date', 'en', 'fil', 'Petsa ng Nai-post');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `carrier` varchar(50) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `account_type` enum('admin','secretary','farmer','buyer') NOT NULL DEFAULT 'farmer',
  `is_verified` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `language` varchar(10) DEFAULT 'English'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `phone`, `carrier`, `password`, `account_type`, `is_verified`, `created_at`, `language`) VALUES
(1, 'Admin User', 'admin@anitech.com', NULL, NULL, '$2y$10$2Wb/BB3PmSj4qTSzKM1L1.3HEJLncMIBCqCuYDKniGvXGOA6kx7/2', 'admin', 1, '2026-01-14 06:17:37', 'English'),
(2, 'Jesus Blancaflor', 'jesusblancaflor@gmail.com', NULL, NULL, '$2y$10$2Wb/BB3PmSj4qTSzKM1L1.3HEJLncMIBCqCuYDKniGvXGOA6kx7/2', 'farmer', 1, '2026-01-14 06:17:37', 'English'),
(3, 'Jeremie', 'jeremie@gmail.com', NULL, NULL, '$2y$10$D9Hr2Y1AeBGrjbfN48cRb.O6upLQiJDQs5PgJqdNQWSiVo11GFXpW', 'secretary', 1, '2026-01-14 06:20:03', 'English'),
(4, 'Test Farmer', 'test@test.com', NULL, NULL, '$2y$10$b9EK.GN9lBnkF./sHEepnOj9CnZaN1H172BTTkMtCp3OItQjxK9B6', 'farmer', 1, '2026-01-14 08:23:02', 'English'),
(5, 'Test User', 'test@gmail.com', NULL, NULL, '$2y$10$joGcARxPqjsXTZJR4ltZCu/aX2bYObg13PngnWKid3mCR/96UrWLO', 'admin', 1, '2026-01-23 10:56:18', 'English'),
(6, 'Test User', 'testf@gmail.com', NULL, NULL, '$2y$10$57JSaZNy/Jf0OzBAeNfd.OWAvgPfVt9Ot7a8Sxe4gz.iv3D/XPB4e', 'farmer', 1, '2026-01-23 10:56:49', 'English'),
(8, 'Test Adminssssss', 'testa@gmail.com', NULL, NULL, '$2y$10$YqNI0/LB5Fj9b48AfvPuzu.UTfVCNFD0JgyHNnsMMW4E5DhtIvoGS', 'admin', 1, '2026-01-26 06:00:03', 'English'),
(9, 'Test Farmer2', 'testf2@gmail.com', NULL, NULL, '$2y$10$Fer4.eOOM2U1IfKAuC0FEe.ptBKXN25Z8w5mvJEHOZT.CNFj8.Nnm', 'farmer', 1, '2026-01-30 15:45:53', 'English'),
(10, 'Test Buyer', 'testb@gmail.com', NULL, NULL, '$2y$10$BACK/Yd46/FuDOMEAtB.8.lWO2G7hTnzeBOsTvHCVO0C.GT4pvVq6', 'buyer', 1, '2026-01-30 15:48:45', 'English'),
(11, 'Agri Officer', 'testo@gmail.com', NULL, NULL, '$2y$10$eZoCC.akD5pRz3rYPI/1J..agyvbhNpAvdqMI4/ijkcvWUDC4BAjm', 'secretary', 1, '2026-02-06 06:20:10', 'English'),
(16, 'Saitama', 'jaysonreales0@gmail.com', NULL, NULL, '$2y$10$n0g4VsFlNBDde95R3AqrpeckX5AOg6gINrvvgNdhSGhHoxFz0J99S', 'farmer', 1, '2026-02-19 07:20:13', 'English');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `admin_announcements`
--
ALTER TABLE `admin_announcements`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `buyer_offers`
--
ALTER TABLE `buyer_offers`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `crops`
--
ALTER TABLE `crops`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `market_prices`
--
ALTER TABLE `market_prices`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `otp_tokens`
--
ALTER TABLE `otp_tokens`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `schedule_distribution`
--
ALTER TABLE `schedule_distribution`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `translations_cache`
--
ALTER TABLE `translations_cache`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_translation` (`source_text`(255),`source_lang`,`target_lang`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `activity_logs`
--
ALTER TABLE `activity_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=158;

--
-- AUTO_INCREMENT for table `admin_announcements`
--
ALTER TABLE `admin_announcements`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `buyer_offers`
--
ALTER TABLE `buyer_offers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `crops`
--
ALTER TABLE `crops`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=58;

--
-- AUTO_INCREMENT for table `market_prices`
--
ALTER TABLE `market_prices`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=50;

--
-- AUTO_INCREMENT for table `otp_tokens`
--
ALTER TABLE `otp_tokens`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `schedule_distribution`
--
ALTER TABLE `schedule_distribution`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `translations_cache`
--
ALTER TABLE `translations_cache`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=276;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD CONSTRAINT `activity_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `crops`
--
ALTER TABLE `crops`
  ADD CONSTRAINT `crops_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
