<?php
/* Paths are explicit configuration so the document root never controls job storage. */
define('RNAMINING_RUNTIME_DIR', getenv('RNAMINING_RUNTIME_DIR') ?: dirname(__DIR__) . '/runtime');
define('RNAMINING_PROJECT_DIR', getenv('RNAMINING_PROJECT_DIR') ?: dirname(__DIR__));
define('RNAMINING_PYTHON', getenv('RNAMINING_PYTHON') ?: 'python3');

function rnamining_job_id($value) {
    return is_string($value) && preg_match('/^[a-f0-9]{32}$/D', $value) ? $value : null;
}

function rnamining_job_dir($id) {
    return RNAMINING_RUNTIME_DIR . '/jobs/' . $id;
}

function rnamining_json_error($message, $status = 400) {
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode(array('error' => $message));
    exit;
}

