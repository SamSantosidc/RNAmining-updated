<?php
require_once dirname(__DIR__, 2) . '/config.php';

$id = rnamining_job_id(isset($_POST['exec']) ? $_POST['exec'] : null);
if (!$id) {
    rnamining_json_error('Invalid execution ID.');
}
$organism = isset($_POST['organismslist']) ? $_POST['organismslist'] : '';
$models = glob(RNAMINING_PROJECT_DIR . '/models/coding_prediction/*.pkl');
$allowed = array_map(function ($path) { return pathinfo($path, PATHINFO_FILENAME); }, $models ?: array());
if (!in_array($organism, $allowed, true)) {
    rnamining_json_error('Invalid organism.');
}
$job = rnamining_job_dir($id);
$input = $job . '/input/sequences.fasta';
$output = $job . '/output';
$logs = $job . '/logs';
if (!is_file($input)) {
    rnamining_json_error('Uploaded FASTA file is missing.', 404);
}
if (!is_dir($output)) { mkdir($output, 0755, true); }
if (!is_dir($logs)) { mkdir($logs, 0755, true); }

$command = array(
    RNAMINING_PYTHON, '-m', 'rnamining.cli', 'predict',
    '--input', $input, '--organism', $organism, '--output', $output,
    '--models', RNAMINING_PROJECT_DIR . '/models/coding_prediction'
);
$escaped = implode(' ', array_map('escapeshellarg', $command));
$environment = 'PYTHONPATH=' . escapeshellarg(RNAMINING_PROJECT_DIR . '/src') . ' ';
exec($environment . $escaped . ' > ' . escapeshellarg($logs . '/stdout.log') . ' 2> ' . escapeshellarg($logs . '/stderr.log'), $ignored, $status);
if ($status !== 0 || !is_file($output . '/predictions.txt')) {
    $message = is_file($logs . '/stderr.log') ? trim(file_get_contents($logs . '/stderr.log')) : 'Prediction failed.';
    rnamining_json_error($message ?: 'Prediction failed.', 500);
}

$archive = new ZipArchive();
if ($archive->open($output . '/RNAmining.zip', ZipArchive::CREATE | ZipArchive::OVERWRITE) === true) {
    foreach (array('predictions.txt', 'codings.txt', 'noncodings.txt') as $name) {
        $archive->addFile($output . '/' . $name, $name);
    }
    $archive->close();
}
header('Content-Type: application/json');
echo json_encode(array('return' => 'success'));

