<?php
declare(strict_types=1);

header('Content-Type: text/plain; charset=utf-8');

define('CLIENTS_FILE', __DIR__ . '/clients.json');
define('CONFIG_FILE', __DIR__ . '/server_config.json');

/* --- Helper functions --- */

function load_clients(): ?array {
    if (!file_exists(CLIENTS_FILE)) {
        $ok = @file_put_contents(CLIENTS_FILE, json_encode([], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), LOCK_EX);
        if ($ok === false) return null;
        return [];
    }

    $raw = @file_get_contents(CLIENTS_FILE);
    if ($raw === false) return null;

    $data = json_decode($raw, true);
    if (!is_array($data)) {
        $data = [];
        @file_put_contents(CLIENTS_FILE, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), LOCK_EX);
    }
    return $data;
}

function save_clients(array $clients): bool {
    $json = json_encode(array_values($clients), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    if ($json === false) return false;
    return file_put_contents(CLIENTS_FILE, $json, LOCK_EX) !== false;
}

function find_client_by_hash(string $hash, array $clients): ?array {
    foreach ($clients as $client) {
        if (($client['hash'] ?? '') === $hash) {
            return $client;
        }
    }
    return null;
}

function find_client_by_ipv4(string $ipv4, array $clients): ?array {
    foreach ($clients as $client) {
        if (($client['ipv4'] ?? '') === $ipv4) {
            return $client;
        }
    }
    return null;
}

function generate_random_sha256(): string {
    return hash('sha256', random_bytes(32));
}

function get_port(): string {
    if (!file_exists(CONFIG_FILE)) return 'unknown';
    $raw = @file_get_contents(CONFIG_FILE);
    if ($raw === false) return 'unknown';
    $config = json_decode($raw, true);
    if (!is_array($config) || !isset($config['port'])) return 'unknown';
    return (string)$config['port'];
}

/* --- Main Logic --- */

$iq = $_GET['iq'] ?? null;
if ($iq !== '169') {
    echo 'invalid';
    exit;
}

$clients = load_clients();
if ($clients === null) {
    http_response_code(500);
    echo 'error';
    exit;
}

$ipv4 = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$port = get_port();

// Hash mitgegeben → prüfen
if (!empty($_GET['hash'])) {
    $incomingHash = $_GET['hash'];
    $found = find_client_by_hash($incomingHash, $clients);
    echo ($found !== null)
        ? "{$incomingHash}:{$port}"
        : "null:{$port}";
    exit;
}

// Kein Hash mitgegeben → IP prüfen
$existing = find_client_by_ipv4($ipv4, $clients);
if ($existing !== null) {
    echo "{$existing['hash']}:{$port}";
    exit;
}

// Neue IP → neuen Hash anlegen
$newHash = generate_random_sha256();
$entry = [
    'ipv4' => $ipv4,
    'hash' => $newHash,
    'created_at' => gmdate('Y-m-d\TH:i:s\Z'),
];
$clients[] = $entry;

if (!save_clients($clients)) {
    http_response_code(500);
    echo "error:{$port}";
    exit;
}

echo "{$newHash}:{$port}";
exit;
