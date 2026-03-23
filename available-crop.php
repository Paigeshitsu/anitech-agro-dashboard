<?php
ob_start();
session_start();
require_once '../notifications_functions.php';
require_once '../translations.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'update_language') {
  $langName = $_POST['language'] ?? 'English';
  $_SESSION['language'] = $langName;
  $_SESSION['lang'] = ($langName === 'Tagalog') ? 'tl' : 'en';
  header("Location: " . $_SERVER['PHP_SELF']);
  exit();
}

// ===== CROP NAME TRANSLATIONS (PHP) =====
function getCropName($cropName) {
    $currentLang = $_SESSION['lang'] ?? 'en';
    
    $translations = [
        'Rice' => ['en' => 'Rice', 'tl' => 'Palay'],
        'Corn' => ['en' => 'Corn', 'tl' => 'Mais'],
        'Eggplant' => ['en' => 'Eggplant', 'tl' => 'Talong'],
        'Bitter Gourd' => ['en' => 'Bitter Gourd', 'tl' => 'Ampalaya'],
        'Tomato' => ['en' => 'Tomato', 'tl' => 'Kamatis'],
        'Sweet Potato' => ['en' => 'Sweet Potato', 'tl' => 'Kamote'],
        'Okra' => ['en' => 'Okra', 'tl' => 'Okra'],
        'Peanut' => ['en' => 'Peanut', 'tl' => 'Mani'],
        'Melon' => ['en' => 'Melon', 'tl' => 'Melon'],
        'Watermelon' => ['en' => 'Watermelon', 'tl' => 'Pakwan'],
        'Cucumber' => ['en' => 'Cucumber', 'tl' => 'Pipino'],
        'Carrot' => ['en' => 'Carrot', 'tl' => 'Karot'],
        'Chili' => ['en' => 'Chili', 'tl' => 'Siling Labuyo'],
        'Potato' => ['en' => 'Potato', 'tl' => 'Patatas'],
        'Cabbage' => ['en' => 'Cabbage', 'tl' => 'Repolyo'],
        'Onion' => ['en' => 'Onion', 'tl' => 'Sibuyas'],
        'Garlic' => ['en' => 'Garlic', 'tl' => 'Bawang'],
        'Squash' => ['en' => 'Squash', 'tl' => 'Kalabasa'],
        'Beans' => ['en' => 'Beans', 'tl' => 'Sitaw'],
    ];
    
    return $translations[$cropName][$currentLang] ?? $cropName;
}

$servername = "localhost";
$username = "root";
$password = "";
$dbname = "anitech";

$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error) {
  die("Connection failed: " . $conn->connect_error);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {

  if (isset($_POST['action']) && $_POST['action'] === 'save_crop') {

    $cropName = $_POST['cropName'];
    $grade = $_POST['cropGrade'];
    $wholesalePrice = $_POST['wholesalePrice'];
    $retailPrice = $_POST['retailPrice'];
    $quantity = $_POST['cropQty'];
    $postedDate = $_POST['postedDate'];
    $availableUntil = $_POST['availableUntil'];
    $description = $_POST['cropDesc'];

    $status = "available"; // AUTO STATUS (since dropdown removed)

    $cropId = $_POST['cropId'] ?? null;

    if ($cropId) {
      $stmt = $conn->prepare("UPDATE crops SET crop_name=?, grade=?, wholesale_price=?, retail_price=?, quantity=?, harvest_date=?, available_until=?, description=?, status=? WHERE id=?");
      $stmt->bind_param("ssdddssssi", $cropName, $grade, $wholesalePrice, $retailPrice, $quantity, $postedDate, $availableUntil, $description, $status, $cropId);
    } else {
      $userId = $_SESSION['user_id'] ?? 1;
      $stmt = $conn->prepare("INSERT INTO crops (user_id, crop_name, grade, wholesale_price, retail_price, quantity, harvest_date, available_until, description, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
      $stmt->bind_param("issddsssss", $userId, $cropName, $grade, $wholesalePrice, $retailPrice, $quantity, $postedDate, $availableUntil, $description, $status);
    }

    if ($stmt->execute()) {
      ob_clean();
      echo json_encode(['success' => true]);
    } else {
      ob_clean();
      echo json_encode(['success' => false, 'error' => $stmt->error]);
    }
    $stmt->close();
    exit;
  }

  if (isset($_POST['action']) && $_POST['action'] === 'delete_crop') {
    $cropId = $_POST['cropId'];
    $stmt = $conn->prepare("DELETE FROM crops WHERE id=?");
    $stmt->bind_param("i", $cropId);

    if ($stmt->execute()) {
      ob_clean();
      echo json_encode(['success' => true]);
    } else {
      ob_clean();
      echo json_encode(['success' => false, 'error' => $stmt->error]);
    }
    $stmt->close();
    exit;
  }
}

// Fetch ALL crops (NO PAGINATION)
$search = $_GET['search'] ?? '';

$sql = "SELECT * FROM crops WHERE 1=1";
$params = [];
$types = "";

if (!empty($search)) {
  $sql .= " AND (crop_name LIKE ? OR description LIKE ?)";
  $searchTerm = "%" . $search . "%";
  $params[] = $searchTerm;
  $params[] = $searchTerm;
  $types .= "ss";
}

$sql .= " ORDER BY id DESC";

$stmt = $conn->prepare($sql);
if (!empty($params)) {
  $stmt->bind_param($types, ...$params);
}
$stmt->execute();
$result = $stmt->get_result();

$crops = [];
while ($row = $result->fetch_assoc()) {
  $row['posted_date'] = $row['harvest_date'];
  $crops[] = $row;
}
?>
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AniTech | <?= L("Available Crops") ?></title>

  <!-- FONT AWESOME -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Afacad:ital,wght@0,400..700;1,400..700&display=swap"
    rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>

  <style>
    /* reused CSS from previous file */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      font-family: "Segoe UI", Arial, sans-serif;
    }

    body {
      background: #f4f9f2;
      color: #333;
      overflow-x: hidden;
    }

    .container {
      display: flex;
      min-height: 100vh;
    }

    /* SIDEBAR */
    .sidebar {
      width: 250px;
      background: #2E4A3D;
      color: #fff;
      display: flex;
      flex-direction: column;
      padding: 20px;
    }

    .sidebar .logo {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-bottom: 40px;
    }

    .sidebar .logo .logo-img {
      width: 100px;
      height: auto;
    }

    .sidebar .logo h2 {
      font-family: 'Afacad', sans-serif;
      font-size: 30px;
      font-weight: 500;
      color: #4CAF50;
      letter-spacing: 1px;
      margin: 0;
      text-transform: uppercase;
    }

    .sidebar a {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px;
      color: #e6f5ea;
      text-decoration: none;
      border-radius: 8px;
      margin-bottom: 8px;
      transition: background 0.2s;
      cursor: pointer;
    }

    .sidebar a.active,
    .sidebar a:hover {
      background: #4CAF50;
    }

    .account {
      margin-top: auto;
      font-size: 14px;
      opacity: 0.8;
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* MAIN */
    .main {
      flex: 1;
      padding: 25px;
      background: #f4f9f2;
      height: 100vh;
      overflow-y: auto;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 25px;
      padding-bottom: 15px;
      border-bottom: 1px solid #b7d5b0;
    }

    .topbar h1 {
      font-size: 32px;
      font-weight: 700;
      color: #000;
      margin: 0;
    }

    .header-controls {
      display: flex;
      align-items: center;
      gap: 15px;
    }

    .icon-btn {
      background: none;
      border: none;
      font-size: 20px;
      color: #333;
      cursor: pointer;
      position: relative;
      padding: 8px;
      border-radius: 8px;
      transition: background 0.2s;
    }

    .icon-btn:hover {
      background: #e8f5e0;
    }

    .icon-btn .badge {
      position: absolute;
      top: -6px;
      right: -6px;
      background: #c94c4c;
      color: white;
      font-size: 10px;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
    }

    .profile-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      background: #fff;
      color: #333;
      padding: 8px 16px;
      border: 1px solid #b7d5b0;
      border-radius: 20px;
      cursor: pointer;
      font-weight: 500;
      transition: background 0.2s;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .profile-btn:hover {
      background: #f0f9eb;
    }

    .profile-btn .avatar {
      width: 30px;
      height: 30px;
      background: #4CAF50;
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: bold;
    }

    .profile-dropdown {
      position: relative;
    }

    .dropdown-menu {
      position: absolute;
      top: 100%;
      right: 0;
      background: white;
      border: none;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      min-width: 160px;
      z-index: 1000;
      display: none;
      margin-top: 8px;
      padding: 10px 0;
    }

    .dropdown-menu.show {
      display: block;
    }

    .dropdown-menu a {
      display: block;
      padding: 10px 20px;
      text-decoration: none;
      color: #333;
      transition: background 0.2s;
    }

    .dropdown-menu a:hover {
      background: #f0f9eb;
    }

    .content {
      padding: 25px;
    }

    .card {
      background: #ffffff;
      padding: 20px;
      border-radius: 14px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .card-header h2 {
      font-size: 20px;
      font-weight: 600;
      color: #2E4A3D;
      margin-bottom: 5px;
    }

    .card-header p {
      font-size: 14px;
      color: #555;
    }

    .filter-bar {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
      align-items: center;
      margin-top: 20px;
    }

    .filter-bar input {
      padding: 8px 14px;
      border: 1px solid #b7d5b0;
      border-radius: 20px;
      font-size: 14px;
      flex: 1;
      max-width: 300px;
      background: white;
    }

    .filter-bar select {
      padding: 8px 12px;
      border: 1px solid #b7d5b0;
      border-radius: 20px;
      font-size: 14px;
      background: white;
    }

    .btn-outline {
      background: transparent;
      border: 1px solid #4f7f5a;
      color: #4f7f5a;
      padding: 8px 16px;
      border-radius: 20px;
      cursor: pointer;
      font-weight: 500;
      font-size: 14px;
      transition: background 0.2s;
    }

    .btn-outline:hover {
      background: #4f7f5a;
      color: white;
    }

    .fab {
      background: #4f7f5a;
      color: #fff;
      font-family: Arial, sans-serif;
      font-size: 18px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
      border: none;
      padding: 12px 20px;
      border-radius: 50px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .fab:hover {
      background: #45a049;
      transform: translateY(-2px);
    }

    .crop-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      margin-top: 20px;
    }

    @media(max-width: 1200px) {
      .crop-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    @media(max-width: 768px) {
      .crop-grid {
        grid-template-columns: 1fr;
      }
    }

    .crop-card {
      background: #f0f9eb;
      padding: 20px;
      border-radius: 14px;
      box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1);
      border: 1px solid #b7d5b0;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      /* ===== HOVER EFFECT ===== */
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      cursor: default;
    }

    .crop-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
    }

    .crop-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 15px;
      gap: 15px;
    }

    .crop-header h4 {
      font-size: 18px;
      color: #2E4A3D;
      margin: 0;
      word-break: break-word;
      line-height: 1.3;
      display: flex;
      align-items: center;
      gap: 10px; /* Gap between icon and text */
      flex-wrap: wrap;
    }

    .crop-header .badge {
      background: #4f7f5a;
      color: #fff;
      font-size: 12px;
      padding: 2px 8px;
      border-radius: 10px;
    }

    .crop-header .price {
      font-size: 20px;
      font-weight: bold;
      color: #2E4A3D;
      white-space: nowrap;
    }

    .crop-details table {
      width: 100%;
      font-size: 14px;
      margin-bottom: 15px;
    }

    .crop-details td {
      padding: 4px 0;
      vertical-align: top;
    }

    .crop-details .label {
      font-weight: bold;
      width: 120px;
      color: #555;
    }

    .description {
      margin-bottom: 15px;
    }

    .description label {
      display: block;
      font-size: 12px;
      font-weight: bold;
      color: #2E4A3D;
      margin-bottom: 5px;
    }

    .description p {
      background: #fff;
      padding: 10px;
      border-radius: 8px;
      border: 1px solid #b7d5b0;
      font-size: 14px;
      color: #555;
      min-height: 40px;
      word-break: break-word;
    }

    .actions {
      display: flex;
      gap: 10px;
      justify-content: flex-end;
      align-items: center;
      padding-top: 10px;
      border-top: 1px solid #b7d5b0;
      flex-wrap: wrap;
    }

    .actions button {
      padding: 6px 12px;
      border: none;
      border-radius: 15px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
    }

    .actions .edit-btn {
      background: #4f7f5a;
      color: white;
    }

    .actions .remove-btn {
      background: #c94c4c;
      color: white;
    }

    /* ===== CROP ICON - TRANSPARENT LEAF ===== */
    .crop-icon {
      width: 40px;
      height: 40px;
      background: transparent;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .crop-icon img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }

    /* MODAL */
    .overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      display: none;
      justify-content: center;
      align-items: center;
      z-index: 1050;
    }

    div:where(.swal2-container) {
      z-index: 2050 !important;
    }

    .overlay.show {
      display: flex;
    }

    .modal {
      background: white;
      width: 520px;
      max-width: 95vw;
      padding: 25px;
      border-radius: 14px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
      position: relative;
      max-height: 90vh;
      overflow-y: auto;
    }

    .modal h3 {
      margin-bottom: 20px;
      color: #2E4A3D;
      text-align: center;
    }

    .modal .close {
      position: absolute;
      top: 15px;
      right: 15px;
      cursor: pointer;
      font-size: 18px;
      color: #888;
    }

    .modal form {
      display: flex;
      flex-direction: column;
      gap: 15px;
    }

    /* ===== FORM FIELD STYLING WITH LABELS ===== */
    .form-field {
      display: flex;
      flex-direction: column;
      gap: 5px;
    }

    .form-field label {
      font-size: 12px;
      font-weight: 600;
      color: #2E4A3D;
    }

    .form-field input,
    .form-field select,
    .form-field textarea {
      padding: 10px;
      border: 1px solid #b7d5b0;
      border-radius: 8px;
      font-size: 14px;
      background: #fafafa;
    }

    .form-field input:focus,
    .form-field select:focus,
    .form-field textarea:focus {
      outline: none;
      border-color: #4f7f5a;
      background: #fff;
    }

    .modal .btn-group {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 10px;
    }

    .modal .save-btn {
      background: #4f7f5a;
      color: white;
      padding: 10px 20px;
      border: none;
      border-radius: 20px;
      cursor: pointer;
      transition: background 0.2s, transform 0.2s;
    }
    .modal .save-btn:hover {
      background: #45a049;
      transform: translateY(-1px);
    }

    .modal .cancel-btn {
      background: white;
      border: 1px solid #ccc;
      padding: 10px 20px;
      border-radius: 20px;
      cursor: pointer;
      transition: background 0.2s, transform 0.2s;
    }
    .modal .cancel-btn:hover {
      background: #f5f5f5;
      transform: translateY(-1px);
    }

    /* NOTIFICATION-PANEL */
    .notification-panel {
      position: absolute;
      top: 100%;
      right: 0;
      background: white;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      min-width: 280px;
      z-index: 1000;
      display: none;
      margin-top: 8px;
      padding: 10px 0;
      max-height: 300px;
      overflow-y: auto;
    }

    .notification-item-unread {
      padding: 12px 20px;
      border-bottom: 1px solid #eee;
      font-size: 14px;
      color: #333;
      cursor: pointer;
      transition: background 0.2s;
    }

    .notification-item-unread:hover {
      background: #f9fdf8;
    }

    .notification-item-unread.read {
      opacity: 0.6;
      background: #f5f5f5;
    }

    .time {
      font-size: 12px;
      color: #777;
      display: block;
      margin-top: 4px;
    }

    /* Notification Utility Classes */
    .text-warning {
      color: #ff9800;
    }

    .text-info {
      color: #2196f3;
    }

    .text-success {
      color: #4caf50;
    }

    .text-danger {
      color: #f44336;
    }

    .text-primary {
      color: #2196f3;
    }
  </style>
</head>

<body>
  <?php include_once __DIR__ . '/../includes/loading_overlay.php'; ?>
  <div class="container">
    <!-- SIDEBAR -->
    <div class="sidebar">
      <div class="logo">
        <img src="../assets/logo.png" alt="AniTech Logo" class="logo-img">
        <h2>ANITECH</h2>
      </div>
      <a href="overview.php"><i class="fa fa-house"></i> <?= L("Overview") ?></a>
      <a href="weather-forecast.php"><i class="fa fa-cloud-sun"></i> <?= L("Weather Forecast") ?></a>
      <a href="crop-management.php"><i class="fa fa-seedling"></i> <?= L("Crop Management") ?></a>
      <a href="available-crop.php" class="active"><i class="fa fa-wheat-awn"></i> <?= L("Available Crops") ?></a>
      <a href="market-prices.php"><i class="fa fa-chart-line"></i> <?= L("Market Prices") ?></a>
      <a href="schedule-distribution.php"><i class="fa fa-calendar-days"></i> <?= L("Schedule Distribution") ?></a>
      <a href="buyer-offer.php"><i class="fa fa-tags"></i> <?= L("Buyer Offers") ?></a>
      <a href="activity-log.php"><i class="fa fa-clock-rotate-left"></i> <?= L("Activity Log") ?></a>

      <div class="account"><?= L("Admin") ?> | AniTech</div>
    </div>

    <!-- MAIN -->
    <div class="main">
      <div class="topbar">
        <h1><?= L("Admin Dashboard") ?></h1>
        <div class="header-controls">
          <div class="header-controls">
            <button class="icon-btn" title="<?= L("Open Calendar") ?>" id="openCalendarBtn">
              <i class="fa-regular fa-calendar"></i>
            </button>

            <!-- Notifications -->
            <div style="position: relative;" id="notificationContainer">
              <button class="icon-btn" title="<?= L("Notifications") ?>" id="notificationBtn">
                <i class="fa-regular fa-bell"></i>
                <span class="badge"
                  style="<?= ($unreadCount ?? 0) > 0 ? '' : 'display: none;' ?>"><?= $unreadCount ?? 0 ?></span>
              </button>
              <div class="notification-panel" id="notificationPanel">
                <div style="text-align: center; padding: 20px;"><i class="fas fa-spinner fa-spin"></i>
                  <?= L("Loading...") ?></div>
              </div>
            </div>
            <div class="profile-dropdown" id="profileDropdown" onclick="toggleProfile()">
              <div class="profile-btn">
                <div class="avatar">AT</div>
                <span><?= htmlspecialchars($_SESSION['user_name'] ?? 'User') ?></span>
                <span class="dropdown-arrow">▼</span>
              </div>
              <div class="dropdown-menu" id="dropdownMenu">
                <a href="profile.php"><?= L("Account") ?></a>

                <!-- Language Dropdown -->
                <div style="padding: 10px 20px;">
                  <div style="font-weight: 600; font-size: 14px; color: #333; margin-bottom: 8px;">
                    <?= L("Language") ?>
                  </div>
                  <form action="" method="POST" id="langForm" style="margin: 0; padding: 0;">
                    <input type="hidden" name="action" value="update_language">
                    <label
                      style="display: flex; align-items: center; gap: 8px; font-size: 14px; color: #555; cursor: pointer; margin-bottom: 5px;">
                      <input type="radio" name="language" value="English"
                        onchange="document.getElementById('langForm').submit();" <?= ($_SESSION['language'] ?? 'English') === 'English' ? 'checked' : '' ?>>
                      <?= L("English") ?>
                    </label>
                    <label
                      style="display: flex; align-items: center; gap: 8px; font-size: 14px; color: #555; cursor: pointer;">
                      <input type="radio" name="language" value="Tagalog"
                        onchange="document.getElementById('langForm').submit();" <?= ($_SESSION['language'] ?? 'English') === 'Tagalog' ? 'checked' : '' ?>>
                      <?= L("Tagalog") ?>
                    </label>
                  </form>
                </div>
                <hr style="border:none; border-top: 1px solid #eee; margin: 5px 0;">
                <a href="#" onclick="logout()"><?= L("Logout") ?></a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="content">
        <div class="card">
          <div class="card-header">
            <h2><?= L("Available Crops") ?></h2>
            <p><?= L("Manage crops listed and ready for sale.") ?></p>
          </div>

          <div class="filter-bar">
            <input type="text" id="searchInput"
              placeholder="<?= L("Search by crop name or description...") ?>"
              value="<?php echo htmlspecialchars($search); ?>">

            <button class="btn-outline" onclick="applyFilters()">
              <i class="fa fa-filter"></i> <?= L("Apply") ?>
            </button>

            <button class="btn-outline" onclick="refreshFilters()">
              <i class="fa fa-rotate-right"></i> <?= L("Refresh") ?>
            </button>

            <div style="flex: 1;"></div>

            <button class="fab" onclick="openModal()">
              <i class="fa fa-plus"></i> <?= L("Add New Crop") ?>
            </button>
          </div>

          <!-- GRID -->
          <div class="crop-grid">
            <?php if (empty($crops)): ?>
              <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #777;">
                <?= L("No crops available right now. Check back later!") ?>
              </div>
            <?php else: ?>
              <?php foreach ($crops as $crop): 
                $translatedCropName = getCropName($crop['crop_name']);
              ?>
                <div class="crop-card" data-original-name="<?php echo htmlspecialchars($crop['crop_name']); ?>">
                  <div>
                    <div class="crop-header">
                      <h4>
                        <!-- Leaf Icon -->
                        <div class="crop-icon">
                          <img src="../assets/leaf-icon.svg" alt="Crop Icon" onerror="this.src='../assets/leaf-icon.png'">
                        </div>
                        <span><?php echo htmlspecialchars($translatedCropName); ?></span>
                        <span class="badge"><?= L($crop['grade']) ?></span>
                      </h4>
                      <div class="price">₱<?php echo number_format($crop['retail_price'], 2); ?></div>
                    </div>

                    <div class="crop-details">
                      <table>
                        <tr>
                          <td class="label"><?= L("Price (Wholesale)") ?></td>
                          <td>₱<?php echo number_format($crop['wholesale_price'], 2); ?></td>
                        </tr>
                        <tr>
                          <td class="label"><?= L("Qty Available") ?></td>
                          <td><?php echo number_format($crop['quantity']); ?> <?= L("kg") ?></td>
                        </tr>
                        <tr>
                          <td class="label"><?= L("Posted Date") ?></td>
                          <td><?php echo date('M d, Y', strtotime($crop['posted_date'])); ?></td>
                        </tr>
                      </table>
                    </div>

                    <div class="description">
                      <label><?= L("Description") ?></label>
                      <p><?php echo htmlspecialchars($crop['description'] ?? 'No description provided.'); ?></p>
                    </div>
                  </div>

                  <div class="actions">
                    <button class="edit-btn" onclick='openModal(<?php echo json_encode($crop); ?>)'>
                      <i class="fa fa-edit"></i> <?= L("Edit") ?>
                    </button>
                    <button class="remove-btn" onclick="deleteCrop(<?php echo $crop['id']; ?>)">
                      <i class="fa fa-trash"></i> <?= L("Remove") ?>
                    </button>
                  </div>
                </div>
              <?php endforeach; ?>
            <?php endif; ?>
          </div>

        </div>
      </div>
    </div>
  </div>

  <!-- MODAL -->
  <div class="overlay" id="overlay" onclick="closeModal()">
    <div class="modal" onclick="event.stopPropagation()">
      <div class="close" onclick="closeModal()">✖</div>
      <h3 id="modalTitle"><?= L("Add New Crop") ?></h3>
      <form id="cropForm">
        <input type="hidden" name="action" value="save_crop">
        <input type="hidden" id="cropId" name="cropId">

        <!-- Crop Name -->
        <div class="form-field">
          <label for="cropName"><?= L("Crop Name") ?></label>
          <input type="text" id="cropName" name="cropName" placeholder="<?= L("Enter crop name") ?>" required>
        </div>

        <!-- Grade -->
        <div class="form-field">
          <label for="cropGrade"><?= L("Grade") ?></label>
          <input type="text" id="cropGrade" name="cropGrade" placeholder="<?= L("e.g., Grade A, Premium") ?>" required>
        </div>

        <!-- Prices & Quantity -->
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
          <div class="form-field">
            <label for="wholesalePrice"><?= L("Wholesale Price (₱/kg)") ?></label>
            <input type="number" id="wholesalePrice" name="wholesalePrice" placeholder="0.00" step="0.01" required>
          </div>
          <div class="form-field">
            <label for="retailPrice"><?= L("Retail Price (₱/kg)") ?></label>
            <input type="number" id="retailPrice" name="retailPrice" placeholder="0.00" step="0.01" required>
          </div>
          <div class="form-field" style="grid-column:1/-1;">
            <label for="cropQty"><?= L("Quantity Available (kg)") ?></label>
            <input type="number" id="cropQty" name="cropQty" placeholder="0" required>
          </div>
        </div>

        <!-- Dates -->
        <div style="display:flex; gap:10px;">
          <div style="flex:1" class="form-field">
            <label for="postedDate"><?= L("Posted Date") ?></label>
            <input type="date" id="postedDate" name="postedDate" required>
          </div>
          <div style="flex:1" class="form-field">
            <label for="availableUntil"><?= L("Available Until") ?></label>
            <input type="date" id="availableUntil" name="availableUntil" required>
          </div>
        </div>

        <!-- Description -->
        <div class="form-field">
          <label for="cropDesc"><?= L("Description") ?></label>
          <textarea id="cropDesc" name="cropDesc" placeholder="<?= L("Enter crop description") ?>" rows="3" required></textarea>
        </div>
      
        <div class="btn-group">
          <button type="button" class="cancel-btn" onclick="closeModal()"><?= L("Cancel") ?></button>
          <button type="submit" class="save-btn"><?= L("Save Crop") ?></button>
        </div>
      </form>
    </div>
  </div>

  <script>
    function toggleProfile() {
      document.getElementById('dropdownMenu').classList.toggle('show');
    }

    function logout() {
      if (confirm(window.dashboardTranslations?.logoutConfirm || "Are you sure you want to log out?")) {
        window.location.href = '../logout.php';
      }
    }

    function openModal(crop = null) {
      document.getElementById('overlay').classList.add('show');
      const modalTitle = document.getElementById('modalTitle');
      const cropForm = document.getElementById('cropForm');

      if (crop) {
        modalTitle.textContent = "<?= L('Edit Crop') ?>";
        document.getElementById('cropId').value = crop.id;
        document.getElementById('cropName').value = crop.crop_name;
        document.getElementById('cropGrade').value = crop.grade;
        document.getElementById('wholesalePrice').value = crop.wholesale_price;
        document.getElementById('retailPrice').value = crop.retail_price;
        document.getElementById('cropQty').value = crop.quantity;
        document.getElementById('postedDate').value = crop.posted_date;
        document.getElementById('availableUntil').value = crop.available_until;
        document.getElementById('cropDesc').value = crop.description;
      } else {
        modalTitle.textContent = "<?= L('Add New Crop') ?>";
        cropForm.reset();
        document.getElementById('cropId').value = "";
      }
    }

    function closeModal() {
      document.getElementById('overlay').classList.remove('show');
    }

    function editCrop(crop) {
      openModal(crop);
    }

    // AJAX SUBMIT
    document.getElementById('cropForm').addEventListener('submit', function (e) {
      e.preventDefault();
      const formData = new FormData(this);

      fetch('available-crop.php', {
        method: 'POST',
        body: formData
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            closeModal();
            Swal.fire("<?= L('Success') ?>", "<?= L('Crop saved successfully!') ?>", 'success')
              .then(() => location.reload());
          } else {
            Swal.fire("<?= L('Error') ?>", data.error || "<?= L('Failed to save') ?>", 'error');
          }
        })
        .catch(err => console.error(err));
    });

    function deleteCrop(id) {
      Swal.fire({
        title: "<?= L('Are you sure?') ?>",
        text: "<?= L("You won't be able to revert this!") ?>",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: "<?= L('Yes, delete it!') ?>"
      }).then((result) => {
        if (result.isConfirmed) {
          const formData = new FormData();
          formData.append('action', 'delete_crop');
          formData.append('cropId', id);

          fetch('available-crop.php', {
            method: 'POST',
            body: formData
          })
            .then(res => res.json())
            .then(data => {
              if (data.success) {
                Swal.fire("<?= L('Deleted!') ?>", "<?= L('Crop has been deleted.') ?>", 'success')
                  .then(() => location.reload());
              } else {
                Swal.fire("<?= L('Error') ?>", "<?= L('Failed to delete.') ?>", 'error');
              }
            });
        }
      })
    }

    function applyFilters() {
      const search = document.getElementById('searchInput').value;
      window.location.href = `available-crop.php?search=${encodeURIComponent(search)}`
    }

    function refreshFilters() {
      document.getElementById('searchInput').value = "";
      window.location.href = "available-crop.php";
    }

    document.getElementById('searchInput').addEventListener('keypress', function (e) {
      if (e.key === 'Enter') {
        applyFilters();
      }
    });

    // ===== CROP NAME TRANSLATION (JavaScript) =====
    function getCropName(cropName) {
      const currentLang = '<?= $_SESSION['lang'] ?? 'en' ?>';
      
      const translations = {
        'Rice': { 'en': 'Rice', 'tl': 'Palay' },
        'Corn': { 'en': 'Corn', 'tl': 'Mais' },
        'Eggplant': { 'en': 'Eggplant', 'tl': 'Talong' },
        'Bitter Gourd': { 'en': 'Bitter Gourd', 'tl': 'Ampalaya' },
        'Tomato': { 'en': 'Tomato', 'tl': 'Kamatis' },
        'Sweet Potato': { 'en': 'Sweet Potato', 'tl': 'Kamote' },
        'Okra': { 'en': 'Okra', 'tl': 'Okra' },
        'Peanut': { 'en': 'Peanut', 'tl': 'Mani' },
        'Melon': { 'en': 'Melon', 'tl': 'Melon' },
        'Watermelon': { 'en': 'Watermelon', 'tl': 'Pakwan' },
        'Cucumber': { 'en': 'Cucumber', 'tl': 'Pipino' },
        'Carrot': { 'en': 'Carrot', 'tl': 'Karot' },
        'Chili': { 'en': 'Chili', 'tl': 'Siling Labuyo' },
        'Potato': { 'en': 'Potato', 'tl': 'Patatas' },
        'Cabbage': { 'en': 'Cabbage', 'tl': 'Repolyo' },
        'Onion': { 'en': 'Onion', 'tl': 'Sibuyas' },
        'Garlic': { 'en': 'Garlic', 'tl': 'Bawang' },
        'Squash': { 'en': 'Squash', 'tl': 'Kalabasa' },
        'Beans': { 'en': 'Beans', 'tl': 'Sitaw' }
      };
      
      return translations[cropName] ? translations[cropName][currentLang] : cropName;
    }
  </script>

  <!-- Include Centralized Calendar Component -->
  <?php include_once __DIR__ . '/includes/calendar.php'; ?>

  <?php include_once '../includes/js_translations.php'; ?>
  <script src="../assets/js/notifications.js?v=1.1"></script>
</body>

</html>