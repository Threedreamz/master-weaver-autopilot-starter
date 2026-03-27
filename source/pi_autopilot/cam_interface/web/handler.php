<?php
function getIPv4($iface = "wlan0") {
    $cmd = "ip -4 addr show " . escapeshellarg($iface) . " | awk '/inet/ {print $2}' | cut -d'/' -f1";
    return trim(shell_exec($cmd));
}
$eip = getIPv4("wlan0");
if ($eip == null||$eip == ""){
  $eip = getIPv4("eth0");
}

define('FLASK_BASE_URL', 'https://'.$eip.':5007'); // Flask-Server-Basisadresse

function send_to_flask(string $status, string $size, string $id, string $auftragId)
{
    
    $payload = json_encode([
        "status" => $status,
        "size" => $size,
        "id" => $id,
        "auftragsId" => $auftragId
    ]);

    $ch = curl_init(FLASK_BASE_URL . '/add_Auftrag');

    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($payload)
    ]);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
    $response = curl_exec($ch);
    $error = curl_error($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($error) {
        return ['error' => "Curl error: $error"];
    }

    if ($http_code !== 200) {
        return ['error' => "Server returned HTTP $http_code", 'response' => $response];
    }

    return json_decode($response, true);
}

/**
 * Fragt den aktuellen Auftrag vom Flask-Server (/getAuftrag) ab
 */
function get_auftrag_from_flask()
{
    $url = FLASK_BASE_URL . '/getAuftrag';

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
    $response = curl_exec($ch);
    $error = curl_error($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($error) {
        return ['error' => "Curl error: $error"];
    }

    if ($http_code !== 200) {
        return ['error' => "Server returned HTTP $http_code", 'response' => $response];
    }

    $decoded = json_decode($response, true);
    if ($decoded === null) {
        return ['error' => 'Invalid JSON response', 'raw' => $response];
    }

    return $decoded;
}
function move_to_defect()
{
    $url = FLASK_BASE_URL . '/moveToDefect';
    $payload = json_encode([]); // ← leerer JSON-Body

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($payload)
    ]);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
    $response = curl_exec($ch);
    $error = curl_error($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($error) {
        return ['error' => "Curl error: $error"];
    }

    if ($http_code !== 200) {
        return ['error' => "Server returned HTTP $http_code", 'response' => $response];
    }

    $decoded = json_decode($response, true);
    if ($decoded === null) {
        return ['error' => 'Invalid JSON response', 'raw' => $response];
    }

    return $decoded;
}
