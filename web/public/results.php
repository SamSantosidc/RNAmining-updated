<?php
require_once dirname(__DIR__) . '/config.php';
$id = rnamining_job_id(isset($_GET['id']) ? $_GET['id'] : null);
if (!$id) { http_response_code(400); exit('Invalid job ID.'); }
$predictionFile = rnamining_job_dir($id) . '/output/predictions.txt';
if (!is_file($predictionFile)) { http_response_code(404); exit('Results not found.'); }
$rows = array();
foreach (file($predictionFile, FILE_IGNORE_NEW_LINES) as $line) {
    $columns = explode("\t", $line);
    if (count($columns) >= 3) { $rows[] = $columns; }
}
?>
<!DOCTYPE html><html><head>
<?php include(dirname(__DIR__) . '/templates/head.php'); ?>
<link rel="stylesheet" href="/assets/css/jquery_dataTables.min.css">
<script src="/assets/js/jquery_dataTables.min.js"></script>
<title>Results - RNAmining</title></head><body>
<?php include(dirname(__DIR__) . '/templates/navbar.php'); ?>
<div class="text-center container" style="padding-top:100px"><h2>Results</h2>
<?php foreach (array('RNAmining.zip' => 'Download All Files', 'codings.txt' => 'Download Coding Sequences', 'noncodings.txt' => 'Download Non-coding Sequences') as $file => $label): ?>
<a href="/api/download.php?id=<?= htmlspecialchars($id) ?>&amp;file=<?= urlencode($file) ?>"><button class="btn btn-primary" style="margin-bottom:20px"><?= htmlspecialchars($label) ?></button></a><br>
<?php endforeach; ?>
<table id="table_id" class="display"><thead><tr><th>Sequence ID</th><th>Coding Potential Classification</th><th>Classification Probability</th></tr></thead><tbody>
<?php foreach ($rows as $row): ?><tr><td><?= htmlspecialchars($row[0]) ?></td><td><?= htmlspecialchars($row[1]) ?></td><td><?= htmlspecialchars($row[2]) ?></td></tr><?php endforeach; ?>
</tbody></table></div><footer><?php include(dirname(__DIR__) . '/templates/footer.php'); ?></footer>
<script>$(document).ready(function(){ $('#table_id').DataTable(); });</script></body></html>
