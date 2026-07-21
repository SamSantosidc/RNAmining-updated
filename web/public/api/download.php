<?php
require_once dirname(__DIR__, 2) . '/config.php';

$id = rnamining_job_id(isset($_GET['id']) ? $_GET['id'] : null);
$allowed = array('RNAmining.zip', 'predictions.txt', 'codings.txt', 'noncodings.txt');
$name = isset($_GET['file']) ? basename($_GET['file']) : '';
if (!$id || !in_array($name, $allowed, true) || $name !== $_GET['file']) {
    http_response_code(400);
    exit('Invalid download request.');
}
$file = rnamining_job_dir($id) . '/output/' . $name;
if (!is_file($file)) {
    http_response_code(404);
    exit('File not found.');
}
header('Content-Type: ' . ($name === 'RNAmining.zip' ? 'application/zip' : 'text/plain; charset=utf-8'));
header('Content-Disposition: attachment; filename="' . $name . '"');
header('Content-Length: ' . filesize($file));
readfile($file);

