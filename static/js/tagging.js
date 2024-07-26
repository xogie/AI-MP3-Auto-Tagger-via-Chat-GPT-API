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

        var currentRow = 0;

        function tagNextRow() {
            if (currentRow >= rowsData.length) {
                showMessage('AI auto-tagging completed successfully.');
                return;
            }

            var row = table.row(currentRow).nodes().to$();
            row.addClass('processing-row'); // Add class to highlight row

            var fileData = {
                artist: rowsData[currentRow][1],
                title: rowsData[currentRow][2],
                genre: rowsData[currentRow][3],
                album: rowsData[currentRow][4],
                year: rowsData[currentRow][5],
                name: rowsData[currentRow][6],
                path: row.find('.row-select').data('path')
            };

            $.ajax({
                url: '/auto_tag',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify([fileData]),
                success: function(response) {
                    if (response.status === 'success') {
                        var updatedFile = response.updatedData[0];
                        table.row(currentRow).data([
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
