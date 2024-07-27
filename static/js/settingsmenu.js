document.addEventListener('DOMContentLoaded', function() {
    console.log("settingsmenu.js loaded"); // Debugging statement

    // Functionality to open/close settings menu
    var navbarToggler = document.getElementById('hamburger-menu');
    var settingsMenu = document.getElementById('settings-menu');
    var closeButton = document.querySelector('.close-button');
    var batchMenuIcon = document.getElementById('batch-menu-icon');
    var batchMenu = document.getElementById('batch-menu');
    var batchCloseButton = document.querySelector('.batch-close-button');

    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            if (settingsMenu) {
                settingsMenu.classList.toggle('open');
                loadSettings();
            }
        });
    }

    if (batchMenuIcon) {
        batchMenuIcon.addEventListener('click', function() {
            if (batchMenu) {
                batchMenu.classList.toggle('open');
            }
        });
    }

    if (closeButton) {
        closeButton.addEventListener('click', function() {
            if (settingsMenu) {
                settingsMenu.classList.remove('open');
            }
        });
    }

    if (batchCloseButton) {
        batchCloseButton.addEventListener('click', function() {
            if (batchMenu) {
                batchMenu.classList.remove('open');
            }
        });
    }

    function showMessage(message) {
        $('#program-messages').text(message).addClass('show');
        setTimeout(function() {
            $('#program-messages').removeClass('show');
        }, 3000); // Hide message after 3 seconds
    }

    function loadSettings() {
        fetch('/settings')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(settings => {
                // Populate the settings form with the loaded settings
                var apiKeyElement = document.getElementById('chat-gpt-api-key');
                var overwriteTagsElement = document.getElementById('overwrite-existing-tags');

                if (apiKeyElement) apiKeyElement.value = settings.chat_gpt_api_key;
                if (overwriteTagsElement) overwriteTagsElement.checked = settings.overwrite_existing_tags;
            })
            .catch(error => showMessage('Error loading program settings: ' + error));
    }

    var saveSettingsButton = document.getElementById('save-settings');
    if (saveSettingsButton) {
        saveSettingsButton.addEventListener('click', function() {
            var settings = {
                chat_gpt_api_key: document.getElementById('chat-gpt-api-key') ? document.getElementById('chat-gpt-api-key').value : '',
                overwrite_existing_tags: document.getElementById('overwrite-existing-tags') ? document.getElementById('overwrite-existing-tags').checked : false
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
                    if (settingsMenu) {
                        settingsMenu.classList.remove('open');
                    }
                } else {
                    showMessage('Error saving program settings: ' + data.error);
                }
            })
            .catch(error => showMessage('Error saving program settings: ' + error));
        });
    }
});
