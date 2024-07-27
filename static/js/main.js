$(document).ready(function() {
    var table = $('#mp3_table').DataTable({
        dom: 'Rlfrtip',
        colReorder: {
            allowReorder: true
        },
        responsive: true,
        paging: false,
        searching: true,
        info: false,
        colVis: {
            buttonText: "Columns"
        },
        retrieve: true
    });

    var intervalId;
    var directoryButtonInProgress = false;

    $('#directory-button').on('click', function() {
        if (!directoryButtonInProgress) {
            console.log("Directory button clicked");
            directoryButtonInProgress = true;
            selectAndLoadDirectory().always(function() {
                directoryButtonInProgress = false;
            });
        }
    });

    window.showMessage = function(message) {
        $('#program-messages').text(message).addClass('show');
        setTimeout(function() {
            $('#program-messages').removeClass('show');
        }, 3000); // Hide message after 3 seconds
    };

    function selectAndLoadDirectory() {
        return $.ajax({
            url: '/select_directory',
            type: 'GET',
            success: function(data) {
                console.log("Directory selected: " + data.directory);
                $('#directory-path').val(data.directory);

                if ($.fn.DataTable.isDataTable('#mp3_table')) {
                    table.clear().draw();
                }

                $.ajax({
                    url: '/load_directory',
                    type: 'POST',
                    data: { directory: data.directory },
                    beforeSend: function() {
                        $('#progress').css('width', '0%');
                        showMessage('Loading files...');
                        intervalId = setInterval(updateProgress, 1000);
                    },
                    success: function(data) {
                        clearInterval(intervalId);
                        table.clear();
                        data.forEach(function(file) {
                            table.row.add([
                                '<input type="checkbox" class="row-select" data-path="' + file.path + '">',
                                file.artist || '',
                                file.title || '',
                                file.genre || '',
                                file.album || '',
                                file.year || '',
                                file.name
                            ]).draw();
                        });
                        showMessage('Files loaded successfully.');
                    },
                    error: function() {
                        clearInterval(intervalId);
                        showMessage('An error occurred while loading files.');
                    }
                });
            },
            error: function() {
                showMessage('An error occurred while selecting the directory.');
            }
        });
    }

    function updateProgress() {
        $.get('/progress', function(data) {
            $('#progress').css('width', data.progress + '%');
            if (data.progress >= 100) {
                clearInterval(intervalId);
            }
        });
    }

    $('#select-all').on('click', function() {
        var rows = table.rows().nodes();
        $('input[type="checkbox"]', rows).prop('checked', this.checked).closest('tr').toggleClass('selected-row', this.checked);
        if (this.checked) {
            $('#edit-menu').addClass('open');
        } else {
            $('#edit-menu').removeClass('open');
        }
    });

    $('#mp3_table tbody').on('change', '.row-select', function() {
        $(this).closest('tr').toggleClass('selected-row');
        var anyChecked = $('.row-select:checked').length > 0;
        if (anyChecked) {
            $('#edit-menu').addClass('open');
            if ($('.row-select:checked').length === 1) {
                var selectedRow = $('.row-select:checked').closest('tr');
                $('#edit-artist').val(selectedRow.find('td').eq(1).text());
                $('#edit-title').val(selectedRow.find('td').eq(2).text());
                $('#edit-genre').val(selectedRow.find('td').eq(3).text());
                $('#edit-album').val(selectedRow.find('td').eq(4).text());
                $('#edit-year').val(selectedRow.find('td').eq(5).text());
            } else {
                $('#edit-artist').val('');
                $('#edit-title').val('');
                $('#edit-genre').val('');
                $('#edit-album').val('');
                $('#edit-year').val('');
            }
        } else {
            $('#edit-menu').removeClass('open');
        }
    });

    $('#apply-edit').on('click', function() {
        var selectedRows = table.rows('.selected-row').data();
        var artist = $('#edit-artist').val() || '';
        var year = $('#edit-year').val() || '';
        var genre = $('#edit-genre').val() || '';
        var album = $('#edit-album').val() || '';
        var title = $('#edit-title').val() || '';

        var filesToUpdate = [];

        selectedRows.each(function(value, index) {
            var rowNode = table.row(index).node();
            var filePath = $(rowNode).find('.row-select').data('path');

            if (artist) value[1] = artist;
            if (title) value[2] = title;
            if (genre) value[3] = genre;
            if (album) value[4] = album;
            if (year) value[5] = year;

            filesToUpdate.push({
                path: filePath,
                name: value[6],
                artist: value[1] || '',
                title: value[2] || '',
                genre: value[3] || '',
                album: value[4] || '',
                year: value[5] || ''
            });
        });

        table.rows('.selected-row').invalidate().draw(false);

        console.log("Data to be sent for update:", filesToUpdate);

        $.ajax({
            url: '/update_files',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(filesToUpdate),
            success: function(response) {
                showMessage('Files updated successfully.');
            },
            error: function() {
                showMessage('An error occurred while updating files.');
            }
        });
    });

    function handleCellEdit(cell) {
        var originalValue = cell.text();
        var columnIndex = cell.index();

        if (columnIndex === 3) { // Genre column
            var genreDropdown = '<select class="genre-dropdown">' +
                '<option value="Rock">Rock</option>' +
                '<option value="Pop">Pop</option>' +
                '<option value="Jazz">Jazz</option>' +
                '<option value="Country">Country</option>' +
                '<option value="Classical">Classical</option>' +
                '<option value="Hip-Hop">Hip-Hop</option>' +
                '<option value="Dance">Dance</option>' +
                '<option value="Other">Other</option>' +
                '</select>';

            cell.html(genreDropdown);
            cell.find('select').val(originalValue).focus().blur(function() {
                var newValue = $(this).val();
                cell.html(newValue);
                var rowData = table.row(cell.closest('tr')).data();
                rowData[columnIndex] = newValue;
                table.row(cell.closest('tr')).data(rowData).draw();
                updateFile(rowData);
            }).change(function() {
                $(this).blur();
            });
        } else if (columnIndex === 5) { // Year column
            cell.html('<input type="number" value="' + originalValue + '" min="1900" max="2100">');
            cell.find('input').focus().blur(function() {
                var newValue = $(this).val();
                cell.html(newValue);
                var rowData = table.row(cell.closest('tr')).data();
                rowData[columnIndex] = newValue;
                table.row(cell.closest('tr')).data(rowData).draw();
                updateFile(rowData);
            }).keypress(function(event) {
                if (event.which == 13) {
                    $(this).blur();
                }
            });
        } else {
            cell.html('<input type="text" value="' + originalValue + '">');
            cell.find('input').focus().blur(function() {
                var newValue = $(this).val();
                cell.html(newValue);
                var rowData = table.row(cell.closest('tr')).data();
                rowData[columnIndex] = newValue;
                table.row(cell.closest('tr')).data(rowData).draw();
                updateFile(rowData);
            }).keypress(function(event) {
                if (event.which == 13) {
                    $(this).blur();
                }
            });
        }
    }

    $('#mp3_table tbody').on('click', 'td', function() {
        var cell = $(this);
        if (cell.index() !== 0 && cell.index() !== 6) {
            handleCellEdit(cell);
        }
    });

    $('#mp3_table tbody').on('dblclick', 'td:nth-child(7)', function() {
        var filePath = $(this).siblings().find('.row-select').data('path');
        var artist = $(this).siblings().eq(1).text();
        var title = $(this).siblings().eq(2).text();

        if (filePath) {
            var audioPlayer = document.getElementById('audio-player');
            var audioSource = document.getElementById('audio-source');
            audioSource.src = '/audio/' + encodeURIComponent(filePath);
            audioPlayer.load();
            audioPlayer.play();
            showMessage('Playing: ' + artist + ' - ' + title);
        }
    });

    function updateFile(rowData) {
        var filePath = $(rowData[0]).data('path'); // Correctly extract the file path from checkbox data
        var fileData = {
            path: filePath,
            artist: rowData[1],
            title: rowData[2],
            genre: rowData[3],
            album: rowData[4],
            year: rowData[5],
            name: rowData[6]
        };

        console.log("Updating file:", fileData);

        $.ajax({
            url: '/update_files',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify([fileData]),
            success: function(response) {
                showMessage('File updated successfully.');
            },
            error: function() {
                showMessage('An error occurred while updating the file.');
            }
        });
    }

    $.contextMenu({
        selector: '#mp3_table tbody tr',
        callback: function(key, options) {
            var data = table.row(this).data();
            var filePath = $(this).find('.row-select').data('path');
            if (key === 'delete') {
                var encodedFilePath = encodeURIComponent(filePath.replace(/\\/g, '/'));  // Replace backslashes with forward slashes and encode the path
                var deleteUrl = '/deletefile?file=' + encodedFilePath;

                $.ajax({
                    url: deleteUrl,
                    type: 'GET',
                    success: function(response) {
                        if (response.status === "success") {
                            table.row(options.$trigger).remove().draw();
                            showMessage('File deleted successfully.');
                        } else {
                            showMessage('An error occurred while deleting the file.');
                        }
                    },
                    error: function() {
                        showMessage('An error occurred while deleting the file.');
                    }
                });
            }
        },
        items: {
            "delete": {name: "Delete", icon: "delete"}
        }
    });
});
