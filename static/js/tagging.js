document.addEventListener('DOMContentLoaded', function() {
    var aiAutoTagButton = document.getElementById('ai-auto-tag');
    var batchMenu = document.getElementById('batch-menu');

    aiAutoTagButton.addEventListener('click', function() {
        // Close the batch menu
        batchMenu.classList.remove('open');

        // Show message that tagging process has started
        showMessage('AI auto-tagging process started.');

        // Process the table for automatic retagging
        var table = $('#mp3_table').DataTable();
        var rowsData = table.rows().data().toArray();

        var filesToTag = [];

        rowsData.forEach(function(row, index) {
            var fileData = {
                artist: row[1],
                title: row[2],
                genre: row[3],
                album: row[4],
                year: row[5],
                name: row[6],
                path: table.row(index).nodes().to$().find('.row-select').data('path')
            };

            // Check if any field is missing
            if (!fileData.artist || !fileData.title || !fileData.genre || !fileData.album || !fileData.year) {
                filesToTag.push(fileData);
            }
        });

        if (filesToTag.length === 0) {
            showMessage('No files with missing metadata for auto-tagging.');
            return;
        }

        var currentRow = 0;

        function tagNextRow() {
            if (currentRow >= filesToTag.length) {
                showMessage('AI auto-tagging completed successfully.');
                return;
            }

            var fileData = filesToTag[currentRow];
            var row = table.row(function(idx, data, node) {
                return data[6] === fileData.name;
            }).nodes().to$();
            row.addClass('processing-row'); // Add class to highlight row

            $.ajax({
                url: '/auto_tag',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify([fileData]),
                success: function(response) {
                    if (response.status === 'success') {
                        var updatedFile = response.updatedData[0];
                        table.row(function(idx, data, node) {
                            return data[6] === updatedFile.name;
                        }).data([
                            '<input type="checkbox" class="row-select" data-path="' + updatedFile.path + '">',
                            updatedFile.artist,
                            updatedFile.title,
                            updatedFile.genre,
                            updatedFile.album,
                            updatedFile.year,
                            updatedFile.name
                        ]).draw(false);
                        showMessage('Processed: ' + updatedFile.name);

                        row.removeClass('processing-row'); // Remove highlight class
                        row.addClass('processed-row'); // Optionally, add another class for processed row
                    } else {
                        showMessage('Error during AI auto-tagging: ' + response.error);
                        row.removeClass('processing-row'); // Remove highlight class in case of error
                    }
                    currentRow++;
                    tagNextRow();
                },
                error: function() {
                    showMessage('An error occurred during AI auto-tagging.');
                    row.removeClass('processing-row'); // Remove highlight class in case of error
                    currentRow++;
                    tagNextRow();
                }
            });
        }

        tagNextRow();
    });
});
