<?php
require_once dirname(__DIR__, 2) . '/config.php';

$id = rnamining_job_id(isset($_POST['exec']) ? $_POST['exec'] : null);
if (!$id) {
    rnamining_json_error('Invalid execution ID.');
}
if (!isset($_FILES['fastaData']) || $_FILES['fastaData']['error'] !== UPLOAD_ERR_OK) {
    rnamining_json_error('The FASTA file was not uploaded.');
}
$file = $_FILES['fastaData'];
if ($file['size'] > 20 * 1024 * 1024) {
    rnamining_json_error('Uploaded file is too large. The file size limit is 20 MB.');
}
$extension = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
if (!in_array($extension, array('txt', 'fasta', 'fa'), true)) {
    rnamining_json_error('Please send a .txt, .fasta, or .fa file.');
}

$job = rnamining_job_dir($id);
foreach (array($job . '/input', $job . '/output', $job . '/logs') as $directory) {
    if (!is_dir($directory) && !mkdir($directory, 0755, true)) {
        rnamining_json_error('Unable to create the job directory.', 500);
    }
}
$destination = $job . '/input/sequences.fasta';
if (!move_uploaded_file($file['tmp_name'], $destination)) {
    rnamining_json_error('Could not store the uploaded file.', 500);
}
header('Content-Type: application/json');
echo json_encode(array('return' => 'success', 'job' => $id));

