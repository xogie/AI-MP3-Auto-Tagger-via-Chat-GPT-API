document.addEventListener('DOMContentLoaded', function() {
    console.log("settingsmenu.js loaded"); // Debugging statement

    // Functionality to open/close settings menu
    var navbarToggler = document.getElementById('hamburger-menu');
    var settingsMenu = document.getElementById('settings-menu');
    var closeButton = document.querySelector('.close-button');
    var batchMenuIcon = document.getElementById('batch-menu-icon');
    var batchMenu = document.getElementById('batch-menu');
    var batchCloseButton = document.querySelector('.batch-close-button');

    navbarToggler.addEventListener('click', function() {
        settingsMenu.classList.toggle('open');
        loadSettings();
    });

    batchMenuIcon.addEventListener('click', function() {
        batchMenu.classList.toggle('open');
    });

    closeButton.addEventListener('click', function() {
        settingsMenu.classList.remove('open');
    });

    batchCloseButton.addEventListener('click', function() {
        batchMenu.classList.remove('open');
    });

    function showMessage(message) {
        $('#program-messages').text(message).addClass('show');
        setTimeout(function() {
            $('#program-messages').removeClass('show');
        }, 3000); // Hide message after 3 seconds
    }

    function loadSettings() {
        fetch('/settings')
            .then(response => response.json())
            .then(settings => {
                // Populate the settings form with the loaded settings
                document.getElementById('chat-gpt-api-key').value = settings.chat_gpt_api_key;
                document.getElementById('overwrite-existing-tags').checked = settings.overwrite_existing_tags;
                document.getElementById('condensed-genre').checked = settings.condensed_genre;
            })
            .catch(error => showMessage('Error loading program settings: ' + error));
    }

    document.getElementById('save-settings').addEventListener('click', function() {
        var settings = {
            chat_gpt_api_key: document.getElementById('chat-gpt-api-key').value,
            overwrite_existing_tags: document.getElementById('overwrite-existing-tags').checked,
            condensed_genre: document.getElementById('condensed-genre').checked
        };
        fetch('/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showMessage('Program settings saved successfully.');
                settingsMenu.classList.remove('open');
            } else {
                showMessage('Error saving program settings: ' + data.error);
            }
        })
        .catch(error => showMessage('Error saving program settings: ' + error));
    });
});
