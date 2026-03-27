<?php
header('Content-Type: application/json; charset=utf-8');

// ========== CONFIG ==========
require_once __DIR__ . '/handler.php';



define('FLASK_BASE_URL', 'https://'.$eip.':5007'); // Flask-Server-Basisadresse

// ========== FUNCTIONS ==========

/**
 * Sendet POST-Daten an den Flask-Server (/add_Auftrag)
 * 
 * Found in handler.php
 * 
 * 
 */


// ========== HANDLE REQUEST ==========

function handle_request()
{
    // --- START TASK ---
    if (isset($_GET['start']) && $_GET['start'] === 'true') {

        $objectId  = $_GET['objectId'] ?? null;
        $size      = $_GET['size'] ?? null;
        $auftragId = $_GET['auftragId'] ?? null;
        $status    = $_GET['status'] ?? 'queued';

        $missing = [];

        if (!$objectId) $missing[] = 'objectId';
        if (!$size) $missing[] = 'size';
        if (!$auftragId) $missing[] = 'auftragId';
        if (!$status) $missing[] = 'status';

        if (!empty($missing)) {
            http_response_code(400);
            echo json_encode([
                'error' => 'Missing parameters',
                'missing' => $missing
            ]);
            return;
        }

        try {
            $result = send_to_flask($status, $size, $objectId, $auftragId);

            echo json_encode(['flask_result' => $result]);
        } catch (Throwable $e) {
            http_response_code(500);
            echo json_encode([
                'error' => 'Flask communication failed',
                'message' => $e->getMessage()
            ]);
        }
        return;
    }

    // --- GET CURRENT AUFTRAG ---
    if (isset($_GET['getAuftrag']) && $_GET['getAuftrag'] === 'true') {
        try {
            $result = get_auftrag_from_flask();
            echo json_encode(['auftrag' => $result]);
        } catch (Throwable $e) {
            http_response_code(500);
            echo json_encode([
                'error' => 'Flask communication failed',
                'message' => $e->getMessage()
            ]);
        }
        return;
    }
    if (isset($_GET['moveToDefect']) && $_GET['moveToDefect'] === 'true') {
        try {
            $result = move_to_defect();
            echo json_encode(['result' => $result]);
        } catch (Throwable $e) {
            http_response_code(500);
            echo json_encode([
                'error' => 'Flask communication failed',
                'message' => $e->getMessage()
            ]);
        }
        return;
    }
    // --- FALLBACK ---
    http_response_code(405);
    echo json_encode(['error' => 'Unsupported request']);
}

// ========== MAIN ==========
handle_request();
