<?php
if (isset($_GET['file'])) {
    $file = urldecode($_GET['file']); // Decode the URL-encoded file path
    if (file_exists($file)) {
        if (unlink($file)) {
            echo "success";
        } else {
            echo "error";
        }
    } else {
        echo "file does not exist";
    }
} else {
    echo "no file specified";
}
?>
