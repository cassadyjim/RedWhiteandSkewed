<?php
/**
 * Red White & Skewed - Voting API
 * PHP + SQLite backend for "I support this view" voting
 * 
 * Features:
 * - One vote per user per story (conservative OR liberal, not both)
 * - Can change vote on return visits
 * - Votes locked when story is archived
 * - Rate limiting to prevent abuse
 * - Fingerprint + IP-based duplicate detection
 * 
 * Place this file at: /api/vote.php on your One.com hosting
 * Create /api/ directory and ensure it's writable
 */

// CORS - Allow requests from your domain
$allowed_origins = [
    'https://redwhiteandskewed.com',
    'http://redwhiteandskewed.com',
    'https://www.redwhiteandskewed.com',
    'http://www.redwhiteandskewed.com'
];

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if (in_array($origin, $allowed_origins)) {
    header("Access-Control-Allow-Origin: $origin");
} else {
    header('Access-Control-Allow-Origin: https://redwhiteandskewed.com');
}

header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json');

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// ============================================
// DATABASE SETUP
// ============================================

$db_path = __DIR__ . '/votes.db';

function get_db() {
    global $db_path;
    
    $db = new SQLite3($db_path);
    $db->busyTimeout(5000);
    
    // Create tables if they don't exist
    $db->exec('
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id TEXT NOT NULL,
            vote TEXT NOT NULL CHECK(vote IN ("conservative", "liberal")),
            ip_hash TEXT NOT NULL,
            fingerprint TEXT,
            user_agent_hash TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(story_id, ip_hash)
        )
    ');
    
    // Track archived stories (votes locked)
    $db->exec('
        CREATE TABLE IF NOT EXISTS archived_stories (
            story_id TEXT PRIMARY KEY,
            archived_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ');
    
    // Rate limiting table
    $db->exec('
        CREATE TABLE IF NOT EXISTS rate_limits (
            ip_hash TEXT PRIMARY KEY,
            request_count INTEGER DEFAULT 0,
            first_request DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_request DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ');
    
    // Indexes for performance
    $db->exec('CREATE INDEX IF NOT EXISTS idx_story_id ON votes(story_id)');
    $db->exec('CREATE INDEX IF NOT EXISTS idx_ip_hash ON votes(ip_hash)');
    $db->exec('CREATE INDEX IF NOT EXISTS idx_fingerprint ON votes(fingerprint)');
    
    return $db;
}

// ============================================
// HELPER FUNCTIONS
// ============================================

function hash_ip($ip) {
    // Salt the hash for privacy
    return hash('sha256', $ip . 'rws_salt_2026_xK9mP2');
}

function hash_ua($ua) {
    return hash('sha256', $ua . 'rws_ua_salt');
}

function get_client_ip() {
    $ip = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
    
    // Check for forwarded IP (behind proxy/CDN)
    if (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        $forwarded = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
        $ip = trim($forwarded[0]);
    } elseif (!empty($_SERVER['HTTP_X_REAL_IP'])) {
        $ip = $_SERVER['HTTP_X_REAL_IP'];
    }
    
    return filter_var($ip, FILTER_VALIDATE_IP) ? $ip : '0.0.0.0';
}

function is_story_archived($db, $story_id) {
    $stmt = $db->prepare('SELECT 1 FROM archived_stories WHERE story_id = ?');
    $stmt->bindValue(1, $story_id, SQLITE3_TEXT);
    $result = $stmt->execute()->fetchArray();
    return $result !== false;
}

function check_rate_limit($db, $ip_hash) {
    // Allow max 30 requests per IP per hour, 100 per day
    $hourly_limit = 30;
    $daily_limit = 100;
    
    $stmt = $db->prepare('SELECT request_count, first_request, last_request FROM rate_limits WHERE ip_hash = ?');
    $stmt->bindValue(1, $ip_hash, SQLITE3_TEXT);
    $result = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
    
    if (!$result) {
        return true; // No record, allow
    }
    
    $first_request = strtotime($result['first_request']);
    $now = time();
    
    // Reset if first request was more than 24 hours ago
    if ($now - $first_request > 86400) {
        $db->exec("DELETE FROM rate_limits WHERE ip_hash = '$ip_hash'");
        return true;
    }
    
    // Check limits
    if ($result['request_count'] >= $daily_limit) {
        return false;
    }
    
    // Check hourly burst (crude but effective)
    $last_request = strtotime($result['last_request']);
    if ($now - $last_request < 3600 && $result['request_count'] >= $hourly_limit) {
        return false;
    }
    
    return true;
}

function update_rate_limit($db, $ip_hash) {
    $stmt = $db->prepare('
        INSERT INTO rate_limits (ip_hash, request_count, first_request, last_request)
        VALUES (?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(ip_hash) DO UPDATE SET
            request_count = request_count + 1,
            last_request = CURRENT_TIMESTAMP
    ');
    $stmt->bindValue(1, $ip_hash, SQLITE3_TEXT);
    $stmt->execute();
}

function get_user_vote($db, $story_id, $ip_hash, $fingerprint = null) {
    // Check by IP hash first
    $stmt = $db->prepare('SELECT vote FROM votes WHERE story_id = ? AND ip_hash = ?');
    $stmt->bindValue(1, $story_id, SQLITE3_TEXT);
    $stmt->bindValue(2, $ip_hash, SQLITE3_TEXT);
    $result = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
    
    if ($result) {
        return $result['vote'];
    }
    
    // Also check by fingerprint if provided
    if ($fingerprint) {
        $stmt = $db->prepare('SELECT vote FROM votes WHERE story_id = ? AND fingerprint = ?');
        $stmt->bindValue(1, $story_id, SQLITE3_TEXT);
        $stmt->bindValue(2, $fingerprint, SQLITE3_TEXT);
        $result = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
        
        if ($result) {
            return $result['vote'];
        }
    }
    
    return null;
}

function cast_vote($db, $story_id, $vote, $ip_hash, $fingerprint = null, $ua_hash = null) {
    // Use UPSERT to handle vote changes
    $stmt = $db->prepare('
        INSERT INTO votes (story_id, vote, ip_hash, fingerprint, user_agent_hash, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(story_id, ip_hash) DO UPDATE SET
            vote = excluded.vote,
            fingerprint = COALESCE(excluded.fingerprint, fingerprint),
            user_agent_hash = COALESCE(excluded.user_agent_hash, user_agent_hash),
            updated_at = CURRENT_TIMESTAMP
    ');
    $stmt->bindValue(1, $story_id, SQLITE3_TEXT);
    $stmt->bindValue(2, $vote, SQLITE3_TEXT);
    $stmt->bindValue(3, $ip_hash, SQLITE3_TEXT);
    $stmt->bindValue(4, $fingerprint, SQLITE3_TEXT);
    $stmt->bindValue(5, $ua_hash, SQLITE3_TEXT);
    
    return $stmt->execute();
}

function get_results($db, $story_id) {
    $stmt = $db->prepare('
        SELECT vote, COUNT(*) as count
        FROM votes
        WHERE story_id = ?
        GROUP BY vote
    ');
    $stmt->bindValue(1, $story_id, SQLITE3_TEXT);
    $result = $stmt->execute();
    
    $votes = ['conservative' => 0, 'liberal' => 0];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        if (isset($votes[$row['vote']])) {
            $votes[$row['vote']] = (int)$row['count'];
        }
    }
    
    $total = $votes['conservative'] + $votes['liberal'];
    
    return [
        'conservative' => $votes['conservative'],
        'liberal' => $votes['liberal'],
        'total' => $total,
        'conservative_percent' => $total > 0 ? round(($votes['conservative'] / $total) * 100) : 50,
        'liberal_percent' => $total > 0 ? round(($votes['liberal'] / $total) * 100) : 50
    ];
}

// ============================================
// ADMIN FUNCTIONS (for archiving stories)
// ============================================

function archive_story($db, $story_id, $admin_key) {
    // Simple admin key check (set this to something secure)
    $valid_key = 'rws_admin_2026_CHANGE_THIS';
    
    if ($admin_key !== $valid_key) {
        return false;
    }
    
    $stmt = $db->prepare('
        INSERT OR REPLACE INTO archived_stories (story_id, archived_at)
        VALUES (?, CURRENT_TIMESTAMP)
    ');
    $stmt->bindValue(1, $story_id, SQLITE3_TEXT);
    return $stmt->execute();
}

function unarchive_story($db, $story_id, $admin_key) {
    $valid_key = 'rws_admin_2026_CHANGE_THIS';
    
    if ($admin_key !== $valid_key) {
        return false;
    }
    
    $stmt = $db->prepare('DELETE FROM archived_stories WHERE story_id = ?');
    $stmt->bindValue(1, $story_id, SQLITE3_TEXT);
    return $stmt->execute();
}

// ============================================
// MAIN API LOGIC
// ============================================

try {
    $db = get_db();
    $ip = get_client_ip();
    $ip_hash = hash_ip($ip);
    $ua_hash = hash_ua($_SERVER['HTTP_USER_AGENT'] ?? '');
    
    $method = $_SERVER['REQUEST_METHOD'];
    
    // GET - Check vote status and get results
    if ($method === 'GET') {
        $story_id = $_GET['story_id'] ?? '';
        
        if (empty($story_id)) {
            throw new Exception('Missing story_id parameter');
        }
        
        // Sanitize story_id
        $story_id = preg_replace('/[^a-zA-Z0-9\-_]/', '', $story_id);
        
        $fingerprint = $_GET['fingerprint'] ?? null;
        $user_vote = get_user_vote($db, $story_id, $ip_hash, $fingerprint);
        $results = get_results($db, $story_id);
        $archived = is_story_archived($db, $story_id);
        
        echo json_encode([
            'success' => true,
            'user_vote' => $user_vote,
            'results' => $results,
            'archived' => $archived
        ]);
    }
    
    // POST - Cast or change vote
    elseif ($method === 'POST') {
        $input = json_decode(file_get_contents('php://input'), true);
        
        $story_id = $input['story_id'] ?? '';
        $vote = $input['vote'] ?? '';
        $fingerprint = $input['fingerprint'] ?? null;
        $admin_key = $input['admin_key'] ?? null;
        $action = $input['action'] ?? 'vote';
        
        // Handle admin actions
        if ($action === 'archive' && $admin_key) {
            if (archive_story($db, $story_id, $admin_key)) {
                echo json_encode(['success' => true, 'message' => 'Story archived']);
            } else {
                echo json_encode(['success' => false, 'error' => 'Invalid admin key']);
            }
            exit();
        }
        
        if ($action === 'unarchive' && $admin_key) {
            if (unarchive_story($db, $story_id, $admin_key)) {
                echo json_encode(['success' => true, 'message' => 'Story unarchived']);
            } else {
                echo json_encode(['success' => false, 'error' => 'Invalid admin key']);
            }
            exit();
        }
        
        // Validate vote input
        if (empty($story_id) || empty($vote)) {
            throw new Exception('Missing story_id or vote');
        }
        
        // Sanitize
        $story_id = preg_replace('/[^a-zA-Z0-9\-_]/', '', $story_id);
        
        if (!in_array($vote, ['conservative', 'liberal'])) {
            throw new Exception('Invalid vote value. Must be "conservative" or "liberal"');
        }
        
        // Check if story is archived
        if (is_story_archived($db, $story_id)) {
            $results = get_results($db, $story_id);
            echo json_encode([
                'success' => false,
                'error' => 'This story has been archived. Voting is closed.',
                'archived' => true,
                'results' => $results
            ]);
            exit();
        }
        
        // Check rate limit
        if (!check_rate_limit($db, $ip_hash)) {
            echo json_encode([
                'success' => false,
                'error' => 'Rate limit exceeded. Please try again later.',
                'rate_limited' => true
            ]);
            exit();
        }
        
        // Get current vote (if any) to determine if this is a change
        $current_vote = get_user_vote($db, $story_id, $ip_hash, $fingerprint);
        $is_change = ($current_vote !== null && $current_vote !== $vote);
        
        // Cast or update vote
        cast_vote($db, $story_id, $vote, $ip_hash, $fingerprint, $ua_hash);
        update_rate_limit($db, $ip_hash);
        
        $results = get_results($db, $story_id);
        
        echo json_encode([
            'success' => true,
            'user_vote' => $vote,
            'vote_changed' => $is_change,
            'previous_vote' => $current_vote,
            'results' => $results,
            'archived' => false
        ]);
    }
    
    else {
        throw new Exception('Invalid request method');
    }
    
} catch (Exception $e) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}
?>
