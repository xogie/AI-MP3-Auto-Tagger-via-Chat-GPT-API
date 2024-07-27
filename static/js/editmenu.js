$(document).ready(function() {
    $('#apply-edit').on('click', function() {
        var selectedRows = $('#mp3_table').DataTable().rows('.selected-row').data();
        var artist = $('#edit-artist').val();
        var year = $('#edit-year').val();
        var genre = $('#edit-genre').val();
        var album = $('#edit-album').val();
        var title = $('#edit-title').val();

        var filesToUpdate = [];

        selectedRows.each(function(value, index) {
            var rowNode = $('#mp3_table').DataTable().row(index).node();
            var checkbox = $(rowNode).find('.row-select');
            var filePath = checkbox.data('path');

            filesToUpdate.push({
                path: filePath,
                name: value[6],
                artist: artist || value[0],
                title: title || value[1],
                genre: genre || value[2],
                album: album || value[3],
                year: year || value[4]
            });

            value[0] = '<input type="checkbox" class="row-select" data-path="' + filePath + '">';
            value[1] = artist || value[1];
            value[2] = title || value[2];
            value[3] = genre || value[3];
            value[4] = album || value[4];
            value[5] = year || value[5];
        });

        $('#mp3_table').DataTable().rows('.selected-row').invalidate().draw(false);

        console.log("Data to be sent for update:", JSON.stringify(filesToUpdate, null, 2)); // Debugging line

        $.ajax({
            url: '/update_files',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(filesToUpdate),
            success: function(response) {
                $('#program-messages').text('Files updated successfully.');
            },
            error: function() {
                $('#program-messages').text('An error occurred while updating files.');
            }
        });
    });

    $('#propercase-tags').on('click', function() {
        $('#edit-artist').val(toProperCase($('#edit-artist').val()));
        $('#edit-year').val(toProperCase($('#edit-year').val()));
        $('#edit-genre').val(toProperCase($('#edit-genre').val()));
        $('#edit-album').val(toProperCase($('#edit-album').val()));
        $('#edit-title').val(toProperCase($('#edit-title').val()));

        $('#mp3_table').DataTable().rows('.selected-row').data().each(function(value, index) {
            value[0] = toProperCase(value[0]);
            value[1] = toProperCase(value[1]);
            value[2] = toProperCase(value[2]);
            value[3] = toProperCase(value[3]);
            value[4] = toProperCase(value[4]);
        });
        $('#mp3_table').DataTable().rows('.selected-row').invalidate().draw(false);
    });

    $('#propercase-filename').on('click', function() {
        $('#mp3_table').DataTable().rows('.selected-row').data().each(function(value, index) {
            var newFileName = toProperCase(value[6]);
            value[6] = newFileName;
        });
        $('#mp3_table').DataTable().rows('.selected-row').invalidate().draw(false);
    });

    $('#format-title').on('click', function() {
        var filesToUpdate = [];

        $('#mp3_table').DataTable().rows('.selected-row').data().each(function(value, index) {
            var rowNode = $('#mp3_table').DataTable().row(index).node();
            var checkbox = $(rowNode).find('.row-select');
            var filePath = checkbox.data('path');
            var newFileName = value[0] + ' - ' + value[1] + '.mp3';
            value[6] = newFileName;

            filesToUpdate.push({
                path: filePath,
                name: newFileName,
                artist: value[0],
                title: value[1],
                genre: value[2],
                album: value[3],
                year: value[4]
            });

            value[0] = '<input type="checkbox" class="row-select" data-path="' + filePath + '">';
        });

        $('#mp3_table').DataTable().rows('.selected-row').invalidate().draw(false);

        $.ajax({
            url: '/update_files',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(filesToUpdate),
            success: function(response) {
                $('#program-messages').text('Files updated successfully.');
            },
            error: function() {
                $('#program-messages').text('An error occurred while updating files.');
            }
        });
    });

    function toProperCase(str) {
        return str.replace(/\w\S*/g, function(txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    }
});
