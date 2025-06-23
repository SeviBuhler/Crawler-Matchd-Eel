const dayNames = {
    'Mon': 'Montag',
    'Tue': 'Dienstag',
    'Wed': 'Mittwoch',
    'Thu': 'Donnerstag',
    'Fri': 'Freitag',
    'Sat': 'Samstag',
    'Sun': 'Sonntag'
};

// Disable the "Changes you made may not be saved" dialog
window.onbeforeunload = null;

function showAlert(message) {
    const alertModal = document.createElement("div");
    alertModal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 2000;  /* Higher z-index to be on top */
    `;
    alertModal.innerHTML = `
        <div class="custom-modal">
            <h3>Hinweis</h3>
            <p>${message}</p>
            <div class="modal-actions">
               <button id="alert-ok">OK</button>
           </div>
       </div>
    `;
    document.body.appendChild(alertModal);

    // Close function 
    const closeAlert = () => {
        alertModal.remove();
    };

    // Click handler for the entire modal area
    alertModal.addEventListener('click', (event) => {
        if (event.target === alertModal) {
            closeAlert();
        }
    });

    // Add button click handler
    document.getElementById('alert-ok').addEventListener('click', closeAlert);

    // Global keyboard handler for just this modal
    const keyHandler = (event) => {
        if (event.key === 'Enter' || event.key === 'Escape') {
            event.preventDefault();
            closeAlert();
            document.removeEventListener('keydown', keyHandler);
        }
    };
    document.addEventListener('keydown', keyHandler);
}


function showConfirm(message, callback) {
    const confirmModal = document.createElement("div");
    confirmModal.innerHTML = `
        <div class="custom-modal-overlay">
            <div class="custom-modal">
                <h3>Bestätigung</h3>
                <p>${message}</p>
                <div class="modal-actions">
                    <button onclick="confirmAction(this, ${callback})">Ja</button>
                    <button onclick="this.closest('.custom-modal-overlay').remove()" class="secondary">Nein</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(confirmModal);

    document.getElementById('confirm-yes').addEventListener('click', async () => {
        confirmModal.remove();
        await callback();
    });
}


// Tab switching
function switchTab(tabId) {
    document.querySelectorAll(".tab-content").forEach((content) => {
        content.classList.remove("active");
    });
    document.querySelectorAll(".tab").forEach((tab) => {
        tab.classList.remove("active");
    });
    document.getElementById(tabId).classList.add("active");
    document.querySelector(`button[onclick="switchTab('${tabId}')"]`).classList.add("active");
}

function saveKeywordToHistory(keyword) {
    // get the current history from local storage
    let keywordHistory = JSON.parse(localStorage.getItem('keywordHistory')) || [];
    // remove duplicates
    keywordHistory = keywordHistory.filter(k => k !== keyword);
    // add the new keyword to the beginning of the array
    keywordHistory.unshift(keyword);
    // Limit the history to the last 5 keywords
    keywordHistory = keywordHistory.slice(0, 10);
    // save the updated history to local storage
    localStorage.setItem('keywordHistory', JSON.stringify(keywordHistory));
}

function setupKeywordAutocomplete() {
    // get the keyword history
    const keywordHistory = JSON.parse(localStorage.getItem('keywordHistory')) || [];

    // create or uodate the autocomplete list
    let datalist = document.getElementById('keyword-suggestions');
    if (!datalist) {
        datalist = document.createElement('datalist');
        datalist.id = 'keyword-suggestions';
        document.body.appendChild(datalist);
    } else {
        datalist.innerHTML = '';
    }

    // add options to the datalist
    keywordHistory.forEach(keyword => {
        const option = document.createElement('option');
        option.value = keyword;
        datalist.appendChild(option);
    });

    // connect the datalist to the input field
    const keywordInput = [
        document.getElementById('new-keyword'),
        document.getElementById('popup-new-keyword')
    ];

    keywordInput.forEach(input => {
        if (input) {
            input.setAttribute('list', 'keyword-suggestions');
        }
    })
}

// Keyword handling
function addKeywordOnEnter(event) {
    if (event.key === "Enter") {
        const input = document.getElementById("new-keyword");
        const keyword = input.value.trim();
        if (keyword) {
            const keywordsDiv = document.querySelector(".keywords");
            const newKeyword = document.createElement("span");
            newKeyword.className = "keyword";
            newKeyword.innerHTML = `${keyword} <span class="remove" onclick="this.parentElement.remove()">×</span>`;
            keywordsDiv.insertBefore(newKeyword, input.parentElement);
            input.value = "";
            saveKeywordToHistory(keyword); // Save the keyword to history
        }
    }
}

function addKeyword() {
    const keywordInput = document.getElementById('popup-new-keyword');
    const keyword = keywordInput.value.trim();
    if (keyword) {
        const keywordsDiv = document.getElementById('popup-keywords');
        const newKeyword = document.createElement('span');
        newKeyword.className = 'keyword';
        newKeyword.innerHTML = `${keyword} <span class="remove" onclick="this.parentElement.remove()">×</span>`;
        keywordsDiv.appendChild(newKeyword);
        keywordInput.value = '';
        saveKeywordToHistory(keyword); // Save the keyword to history
    }
}

// Manual crawling
async function startManualCrawl() {
    const url = document.getElementById("url").value;
    const keywords = Array.from(document.querySelectorAll(".keyword")).map(
        (k) => k.textContent.trim().replace("×", "")
    );

    try {
        const results = await eel.crawl(url, keywords)();
        document.getElementById("crawling-results").innerHTML = results;
    } catch (error) {
        console.error("Error during crawling:", error);
        document.getElementById("crawling-results").innerHTML = "Fehler beim Crawling: " + error;
    }
}

// Scheduled sites management
async function saveNewSite() {
    const title = document.getElementById("site-name").value;
    const url = document.getElementById("site-url").value;
    const scheduleTime = document.getElementById("crawl-time").value;
    const scheduleDay = Array.from(document.querySelectorAll('.days-selection input:checked'))
        .map(checkbox => checkbox.value).join(',');
    const keywords = Array.from(document.getElementById('popup-keywords').getElementsByClassName('keyword'))
        .map(k => k.textContent.trim().replace('×', ''));
    
    // Validation
    if (!title || !url || !scheduleTime || !scheduleDay || keywords.length === 0) {
        alert("Bitte füllen Sie alle Felder aus und wählen Sie mindestens einen Tag.");
        return;
    }

    try {
        const response = await eel.add_crawl(title, url, scheduleTime, scheduleDay, keywords)();
        if (response.status === 'success') {
            window.onbeforeunload = null;
            window.location.reload();
        } else {
            alert('Fehler beim Speichern: ' + response.message);
        }
    } catch (error) {
        console.error("Error saving crawl:", error);
        alert('Fehler beim Speichern: ' + error);
    }
}

function addNewScheduledSite() {
    const popup = document.createElement("div");
    popup.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
        width: 400px;
        max-height: 90vh;
        overflow-y: auto;
    `;

    popup.innerHTML = `
        <h3>Neuer Crawl hinzufügen</h3>
        <div class="form-group">
            <label for="site-name">Titel:</label>
            <input type="text" id="site-name" placeholder="z.B. JobScout24">
        </div>
        <div class="form-group">
            <label for="site-url">URL:</label>
            <input type="text" id="site-url" placeholder="https://example.com">
        </div>
        <div class="form-group">
            <label>Tags:</label>
            <div class="keywords" id="popup-keywords"></div>
            <input type="text" id="popup-new-keyword" placeholder="Tag eingeben und Enter drücken">
        </div>
        <div class="form-group">
            <label for="crawl-time">Crawl-Zeit:</label>
            <input type="time" id="crawl-time">
        </div>
        <div class="form-group">
            <label>Crawl-Tage:</label>
            <div class="days-selection">
                <label><input type="checkbox" value="Mon"> Montag</label>
                <label><input type="checkbox" value="Tue"> Dienstag</label>
                <label><input type="checkbox" value="Wed"> Mittwoch</label>
                <label><input type="checkbox" value="Thu"> Donnerstag</label>
                <label><input type="checkbox" value="Fri"> Freitag</label>
                <label><input type="checkbox" value="Sat"> Samstag</label>
                <label><input type="checkbox" value="Sun"> Sonntag</label>
            </div>
        </div>
        <div style="display: flex; gap: 10px; margin-top: 20px;">
            <button onclick="saveNewSite()">Speichern</button>
            <button onclick="closePopup()" style="background: #6c757d;">Abbrechen</button>
        </div>
    `;

    const overlay = document.createElement("div");
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 999;
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(popup);

    window.currentPopup = popup;
    window.currentOverlay = overlay;

    addInputEventListeners(popup, saveNewSite);
}

function addInputEventListeners(popup, saveCallback) {
    const inputs = popup.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                if (input.id === 'popup-new-keyword') {
                    addKeyword();
                } else {
                    saveCallback();
                }
            }
        });
    });
}

function closePopup() {
    if (window.currentPopup) {
        window.onbeforeunload = null;
        window.currentPopup.remove();
        window.currentOverlay.remove();
    }
}

// Delete functionality
async function deleteCrawl(crawlID) {
    const modalHTML = `
        <div id="delete-confirm-modal" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        ">
            <div style="
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                max-width: 400px;
                width: 90%;
            ">
                <h3>Crawl löschen</h3>
                <p>Möchten Sie diesen Crawl wirklich löschen?</p>
                <div style="display: flex; justify-content: center; gap: 10px; margin-top: 20px;">
                    <button id="confirm-delete" style="background: #dc3545;">Löschen</button>
                    <button id="cancel-delete" style="background: #6c757d;">Abbrechen</button>
                </div>
            </div>
        </div>
    `;
    
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);

    const modal = document.getElementById('delete-confirm-modal');
    const confirmButton = document.getElementById('confirm-delete');
    const cancelButton = document.getElementById('cancel-delete');

    confirmButton.addEventListener('click', async () => {
        modal.remove();
        try {
            const response = await eel.delete_crawl(crawlID)();
            if (response.status === 'success') {
                window.location.reload();
            } else {
                alert(response.message || 'Fehler beim Löschen');
            }
        } catch (error) {
            console.error("Error deleting crawl:", error);
            alert('Fehler beim Löschen: ' + error);
        }
    });

    cancelButton.addEventListener('click', () => {
        modal.remove();
    });

    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.remove();
        }
    });
}

// Edit functionality
function editCrawl(crawlID) {
    const crawl = document.querySelector(`.site-card[data-id="${crawlID}"]`);
    if (!crawl) return;

    const popup = document.createElement("div");
    popup.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
        width: 400px;
    `;

    const existingName = crawl.querySelector('h3').textContent;
    const existingUrl = crawl.querySelector('p').textContent.replace('URL: ', '');
    const existingTime = crawl.querySelector('p:last-of-type').textContent.match(/\d{2}:\d{2}/)[0];
    const existingKeywords = Array.from(crawl.querySelectorAll('.keyword'))
        .map(k => k.textContent.trim());

    popup.innerHTML = `
        <h3>Crawl bearbeiten</h3>
        <div class="form-group">
            <label for="site-name">Titel:</label>
            <input type="text" id="site-name" value="${existingName}">
        </div>
        <div class="form-group">
            <label for="site-url">URL:</label>
            <input type="text" id="site-url" value="${existingUrl}">
        </div>
        <div class="form-group">
            <label>Tags:</label>
            <div class="keywords" id="popup-keywords">
                ${existingKeywords.map(keyword => `
                    <span class="keyword">${keyword} <span class="remove" onclick="this.parentElement.remove()">×</span></span>
                `).join('')}
            </div>
            <input type="text" id="popup-new-keyword" placeholder="Tag eingeben und Enter drücken">
        </div>
        <div class="form-group">
            <label for="crawl-time">Crawl-Zeit:</label>
            <input type="time" id="crawl-time" value="${existingTime}">
        </div>
        <div class="form-group">
            <label>Crawl-Tage:</label>
            <div class="days-selection">
                <label><input type="checkbox" value="Mon"> Montag</label>
                <label><input type="checkbox" value="Tue"> Dienstag</label>
                <label><input type="checkbox" value="Wed"> Mittwoch</label>
                <label><input type="checkbox" value="Thu"> Donnerstag</label>
                <label><input type="checkbox" value="Fri"> Freitag</label>
                <label><input type="checkbox" value="Sat"> Samstag</label>
                <label><input type="checkbox" value="Sun"> Sonntag</label>
            </div>
        </div>
        <div style="display: flex; gap: 10px; margin-top: 20px;">
            <button onclick="saveEditedSite(${crawlID})">Speichern</button>
            <button onclick="closePopup()" style="background: #6c757d;">Abbrechen</button>
        </div>
    `;

    const overlay = document.createElement("div");
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 999;
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(popup);
    
    const existingDays = crawl.querySelector('p:last-of-type').textContent
        .match(/an (.*?)$/)[1]
        .split(', ')
        .map(germanDay => {
            return Object.entries(dayNames).find(([key, value]) => value === germanDay)[0];
        });

    existingDays.forEach(day => {
        const checkbox = popup.querySelector(`input[value="${day}"]`);
        if (checkbox) checkbox.checked = true;
    });

    window.currentPopup = popup;
    window.currentOverlay = overlay;

    addInputEventListeners(popup, () => saveEditedSite(crawlID));
}

async function saveEditedSite(crawlID) {
    const title = document.getElementById("site-name").value;
    const url = document.getElementById("site-url").value;
    const scheduleTime = document.getElementById("crawl-time").value;
    const scheduleDay = Array.from(document.querySelectorAll('.days-selection input:checked'))
        .map(checkbox => checkbox.value).join(',');
    const keywords = Array.from(document.getElementById('popup-keywords').getElementsByClassName('keyword'))
        .map(k => k.textContent.trim().replace('×', ''));
    
    if (!title || !url || !scheduleTime || !scheduleDay || keywords.length === 0) {
        alert("Bitte füllen Sie alle Felder aus.");
        return;
    }

    try {
        const response = await eel.update_crawl(crawlID, title, url, scheduleTime, scheduleDay, keywords)();
        if (response.status === 'success') {
            window.onbeforeunload = null;
            window.location.reload();
        } else {
            alert('Fehler beim Speichern: ' + response.message);
        }
    } catch (error) {
        console.error("Error updating crawl:", error);
        alert('Fehler beim Speichern: ' + error);
    }
}

// Load Crawls when page loads
async function loadCrawls() {
    try {
        const crawls = await eel.get_crawls()();
        console.log("Received crawls:", crawls);
        const container = document.getElementById('scheduled-sites-container');

        if (!crawls || crawls.length === 0) {
            container.innerHTML = '<p>Noch keine Crawls vorhanden</p>';
            return;
        }
    
        container.innerHTML = crawls.map(crawl => `
            <div class="site-card" data-id="${crawl.id}">
                <h3>${crawl.title}</h3>
                <p>URL: ${crawl.url}</p>
                <div class="keywords">
                    ${crawl.keywords.map(keyword => `
                        <span class="keyword">${keyword}</span>
                    `).join('')}
                </div>
                <p>Häufigkeit: ${formatSchedule(crawl.scheduleTime, crawl.scheduleDay)}</p>
                <div class="site-actions">
                    <button class="edit-btn" onclick="editCrawl(${crawl.id})">Bearbeiten</button>
                    <button class="delete-btn" onclick="deleteCrawl(${crawl.id})">Löschen</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading crawls: ', error);
    } 
}

function formatSchedule(time, days) {
    const daysArray = Array.isArray(days) ? days : days.split(',');
    const formattedDays = daysArray.map(day => dayNames[day.trim()]).join(', ');
    return `${time} Uhr an ${formattedDays}`;
}


async function manageEmails(){
    try {
        // If the settings modal is open, close it
        const settingsModal = document.querySelector('.settings-modal');
        if (settingsModal && settingsModal.parentElement) {
            const emailTimeInput = document.getElementById('emailTimeInput');
            if (emailTimeInput && emailTimeInput.value) {
                await saveEmailTime(emailTimeInput.value);
            }
            settingsModal.parentElement.remove();
        }

        const emails = await eel.get_emails()();

        if (window.currentPopup) {
            closePopup();
        }

        const popup = document.createElement("div");
        popup.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            width: 400px;
            max-height: 90vh;
            overflow-y: auto;
        `;

        popup.innerHTML = `
            <h3>Email-Benachrichtigung verwalten</h3>
            <div class="form-group">
                <label for="email">Neuer E-Mail Empfänger hinzufügen:</label>
                <div style="display: flex; gap: 10px;">
                    <input type="email" id="new-email" placeholder="email@example.com">
                    <button id="add-email-button">Hinzufügen</button>
                </div>
            </div>
            <div class="email-list" style="margin-top: 20px;">
                <h4>Gespeicherte Email-Adressen</h4>
                <div id="email-container">
                    ${emails.map(email => `
                        <div class="email-item" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span>${email.email}</span>
                            <button onclick="confirmDeleteEmail(${email.id})" style="background: #dc3545;">Löschen</button>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div style="margin-top: 20px;">
                <button onclick="closePopup()" style="background: #6c757d;">Schließen</button>
            </div>
        `;

        const overlay = document.createElement("div");
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
        `;

        document.body.appendChild(overlay);
        document.body.appendChild(popup);

        window.currentPopup = popup;
        window.currentOverlay = overlay;

        const addButton = document.getElementById('add-email-button');
        const emailInput = document.getElementById('new-email');

        if (addButton && emailInput) {
            addButton.addEventListener('click', addNewEmail);
            emailInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    addNewEmail();
                }
            });
        }

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closePopup();
            }
        })

        const handleEscapeKey = (e) => {
            if (e.key === 'Escape') {
                closePopup();
                document.removeEventListener('keydown', handleEscapeKey);
            }
        };

        document.addEventListener('keydown', handleEscapeKey);

    } catch (error) {
        console.error('Error loading emails:', error);
        showAlert('Fehler beim Laden der Email-Adressen: ' + error);
    }
}


async function addNewEmail(){
    const emailInput = document.getElementById('new-email');
    const email = emailInput.value.trim();

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email)) {
        showAlert('Bitte geben Sie eine gültige Email-Adresse ein.');
        return;
    }

    try {
        // Simply refresh the current popup's email list
        const result = await eel.add_email(email)();
        const emails = await eel.get_emails()();
        const container = document.getElementById('email-container');
     
        if (container) {
            container.innerHTML = emails.map(email => `
                <div class="email-item" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span>${email.email}</span>
                    <button onclick="confirmDeleteEmail(${email.id})" style="background: #dc3545;">Löschen</button>
                </div>
            `).join('');
            
            // Clear input field after successful addition
            emailInput.value = '';

        }
    } catch (error) {
        console.error('Error adding email:', error);
        showAlert('Fehlerbeim speichern der Email-Adresse: ' + error);
    }
}


function confirmDeleteEmail(emailId) {
    const confirmModal = document.createElement("div");
    confirmModal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 2000;
    `;
    confirmModal.innerHTML = `
        <div class="custom-modal">
            <h3>Bestätigung</h3>
            <p>Möchten Sie diese Email-Adresse wirklich löschen?</p>
            <div class="modal-actions">
                <button id="confirm-delete">Löschen</button>
                <button id="cancel-delete" class="secondary">Abbrechen</button>
            </div>
        </div>
    `;
    document.body.appendChild(confirmModal);

    const deleteEmail = async () => {
        confirmModal.remove();
        document.removeEventListener('keydown', keyHandler);
        try {
            const response = await eel.delete_email(emailId)();
            if (response.status === 'success') {
                const emails = await eel.get_emails()();
                const container = document.getElementById('email-container');
                if (container) {
                    container.innerHTML = emails.map(email => `
                        <div class="email-item" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span>${email.email}</span>
                            <button onclick="confirmDeleteEmail(${email.id})" style="background: #dc3545;">Löschen</button>
                        </div>
                    `).join('');
                }
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('Fehler beim Löschen der Email-Adresse');
        }
    };

    const closeModal = () => {
        confirmModal.remove();
        document.removeEventListener('keydown', keyHandler);
    };

    // Click handlers
    confirmModal.addEventListener('click', (event) => {
        if (event.target === confirmModal) {
            closeModal();
        }
    });
    document.getElementById('confirm-delete').addEventListener('click', deleteEmail);
    document.getElementById('cancel-delete').addEventListener('click', closeModal);

    // Global keyboard handler
    const keyHandler = (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            deleteEmail();
        } else if (event.key === 'Escape') {
            event.preventDefault();
            closeModal();
        }
    };
    document.addEventListener('keydown', keyHandler);
}


function showSettings() {
    if (window.currentPopup) {
        closePopup();
    }

    const settingsModal = document.createElement("div");
    settingsModal.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
        width: 400px;
        max-height: 90vh;
        overflow-y: auto;
    `;
    
    settingsModal.innerHTML = `
        <h3>Einstellungen</h3>
        <div class="settings-section">
            <div class="setting-item">
                <label class="setting-label">Crawler mit Windows starten</label>
                <div class="toggle-switch">
                    <input type="checkbox" id="startupToggle" onchange="toggleStartup()">
                    <label for="startupToggle"></label>
                </div>
            </div>
        </div>

        <div class="settings-section">
            <h4>Email-Benachrichtigungen</h4>
            <div class="setting-item">
                <label class="setting-label">Tägliche E-Mail senden um:</label>
                <input type="time" id="emailTimeInput" class="time-input">
            </div>
            <div class="settings-item">
                <button id="manageEmailsButton" onclick="manageEmails()" style="width: 100%;">
                    E-Mail-Empfänger verwalten
                </button>
            </div>
        </div>

        <div style="text-align: right; margin-top: 15px;">
            <button onclick="closePopup()" style="background: #6c757d;">Schließen</button>
        </div>
    `;

    const overlay = document.createElement("div");
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 999;
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(settingsModal);

    // Set global references für closePopup()
    window.currentPopup = settingsModal;
    window.currentOverlay = overlay;

    // Initialize settings
    checkStartupStatus(); 
    loadEmailSettings();
    
    // Add keypress event listener for the time input
    setTimeout(() => {
        const emailTimeInput = document.getElementById('emailTimeInput');
        if (emailTimeInput) {
            emailTimeInput.addEventListener('keypress', function(event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    saveEmailTime(emailTimeInput.value);
                }
            });
        }
    }, 100);

    // Event-Listener für Klick außerhalb des Modals
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            saveEmailTimeBeforeClose();
            closePopup();
        }
    });

    // Event-Listener für ESC-Taste
    const handleEscapeKey = (e) => {
        if (e.key === 'Escape') {
            saveEmailTimeBeforeClose();
            closePopup();
            document.removeEventListener('keydown', handleEscapeKey);
        }
    };
    
    document.addEventListener('keydown', handleEscapeKey);

    // Erweiterte closePopup function für Settings
    const originalClosePopup = window.closePopup;
    window.closePopup = function() {
        saveEmailTimeBeforeClose();
        document.removeEventListener('keydown', handleEscapeKey);
        originalClosePopup();
        // Reset to original closePopup
        window.closePopup = originalClosePopup;
    };
}

// Helper function to save email time before closing
function saveEmailTimeBeforeClose() {
    const emailTimeInput = document.getElementById('emailTimeInput');
    if (emailTimeInput && emailTimeInput.value) {
        saveEmailTime(emailTimeInput.value);
    }
}



async function saveEmailTime(emailTime) {
    if (!emailTime) return;

    // Save actual value for comparison
    if (!window.previousEmailTime){
        window.previousEmailTime = emailTime;
        return;
    }

    // Update only if the value has changed
    if (emailTime !== window.previousEmailTime) {
        try {
            const result = await eel.update_email_settings(emailTime)();
            if (result.status === 'success') {
                window.previousEmailTime = emailTime; // Update the previous value
                showAlert('Die E-Mail-Zeit wurde erfolgreich auf ' + emailTime + ' Uhr aktualisiert.')
            } else {
                showAlert("Fehler beim Aktualisieren der E-Mail-Zeit: " + result.message);
            }
        } catch (error) {
            console.error('Error updating email time:', error);
            showAlert('Fehler beim Aktualisieren der E-Mail-Zeit: ' + error);
        }
    }
}



async function loadEmailSettings() {
    try {
        const settings = await eel.get_email_settings()();
        if (settings.status === 'success') {
            const emailTimeInput = document.getElementById('emailTimeInput');
            if (emailTimeInput) {
                emailTimeInput.value = settings.email_time;
                window.previousEmailTime = settings.email_time;
            }
        }
    } catch (error) {
        console.error('Error loading email settings:', error);
    }
}


async function updateEmailTime() {
    const emailTimeInput = document.getElementById('emailTimeInput');
    if (!emailTimeInput) return;

    const emailTime = emailTimeInput.value;
    if (!emailTime) return;

    try {
        const result = await eel.update_email_settings(emailTime)();
        if (result.status === 'success') {
            showAlert('Die E-Mail-Zeit wurde erfolgreich aktualisiert.');
        } else {
            showAlert("Fehler beim Aktualisieren der E-Mail-Zeit: " + result.message);
        }
    } catch (error) {
        console.error('Error updating email time:', error);
        showAlert('Fehler beim Aktualisieren der E-Mail-Zeit: ' + error);
    }
}


async function toggleStartup() {
    try {
        const result = await eel.toggle_startup()();
        if (result.status === 'success') {
            updateStartupToggle(result.enabled);
            showAlert(result.enabled ? 
                'Automatischer Start wurde aktiviert' : 
                'Automatischer Start wurde deaktiviert');
        } else {
            showAlert('Fehler beim Ändern der Starteinstellungen');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Fehler beim Ändern der Starteinstellungen: ' + error);
    }
}

async function checkStartupStatus() {
    try {
        const result = await eel.get_startup_status()();
        if (result.status === 'success') {
            updateStartupToggle(result.enabled || false);
        } else {
            updateStartupToggle(false);
            console.error('Error checking startup status:', result.message);
        }
    } catch (error) {
        updateStartupToggle(false);
        console.error('Error checking startup status:', error);
    }
}

function updateStartupToggle(enabled) {
    const toggle = document.getElementById('startupToggle');
    if (toggle) {
        toggle.checked = enabled === true;
    }
}

// Call this when the page loads
document.addEventListener('DOMContentLoaded', () => {
    updateViewportVariables(); 
    loadCrawls();
    setupKeywordAutocomplete();

    // Event listener for creating popup
    const originalAddNewScheduledSite = addNewScheduledSite;
    window.addNewScheduledSite = function() {
        originalAddNewScheduledSite();
        setTimeout(setupKeywordAutocomplete, 100); 
    };

    const originalEditCrawl = editCrawl;
    window.editCrawl = function(crawlID) {
        originalEditCrawl(crawlID);
        setTimeout(setupKeywordAutocomplete, 100);
    }
});

function detectScreenType(viewportWidth, viewportHeight) {
    let screenType = 'desktop';
    
    if (viewportWidth <= 1280) {
        screenType = 'small-desktop';
    } else if (viewportWidth <= 1440) {
        screenType = 'standard-desktop';
    } else if (viewportWidth <= 1920) {
        screenType = 'large-desktop';
    } else {
        screenType = 'ultra-desktop';
    }
    
    // CSS Klassen setzen für Responsive Design
    document.body.className = document.body.className.replace(/screen-\w+/g, '');
    document.body.classList.add(`screen-${screenType}`);
    
    // CSS Properties setzen
    updateScreenSpecificProperties(screenType, viewportWidth, viewportHeight);
}

function updateViewportVariables() {
    const vh = window.innerHeight * 0.01;
    const vw = window.innerWidth * 0.01;
    const viewportWidth = window.innerWidth;  
    const viewportHeight = window.innerHeight; 
    const screenWidth = window.screen.width;   
    const screenHeight = window.screen.height;
    
    // CSS Custom Properties updaten
    document.documentElement.style.setProperty('--vh', `${vh}px`);
    document.documentElement.style.setProperty('--vw', `${vw}px`);
    document.documentElement.style.setProperty('--screen-width', `${screenWidth}px`);
    document.documentElement.style.setProperty('--screen-height', `${screenHeight}px`);
    
    // Screen-Type Detection
    detectScreenType(viewportWidth, viewportHeight);
}

// ✅ Erweiterte updateScreenSpecificProperties
function updateScreenSpecificProperties(screenType, viewportWidth, viewportHeight) {
    const root = document.documentElement;
    
    // ✅ Anpassungen basierend auf Viewport-Größe
    switch(screenType) {
        case 'small-desktop': 
            root.style.setProperty('--container-padding-multiplier', '1.5');
            root.style.setProperty('--font-scale', '0.9');
            root.style.setProperty('--modal-scale', '0.8');
            break;
        case 'standard-desktop': 
            root.style.setProperty('--container-padding-multiplier', '2');
            root.style.setProperty('--font-scale', '1');
            root.style.setProperty('--modal-scale', '1');
            break;
        case 'large-desktop': 
            root.style.setProperty('--container-padding-multiplier', '2.5');
            root.style.setProperty('--font-scale', '1.1');
            root.style.setProperty('--modal-scale', '1.2');
            break;
        case 'ultra-desktop': 
            root.style.setProperty('--container-padding-multiplier', '3');
            root.style.setProperty('--font-scale', '1.2');
            root.style.setProperty('--modal-scale', '1.3');
            break;
    }
    
    root.style.setProperty('--viewport-width', `${viewportWidth}px`);
    root.style.setProperty('--viewport-height', `${viewportHeight}px`);
}

// Performance-optimierte Resize-Handler
let resizeTimeout;
function handleResize() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        updateViewportVariables();
    }, 100); // Debounce für bessere Performance
}

// ✅ Event Listeners hinzufügen
window.addEventListener('resize', handleResize);
window.addEventListener('orientationchange', () => {
    setTimeout(updateViewportVariables, 100);
});

// ✅ Window Focus Event für Multi-Monitor Setups
window.addEventListener('focus', () => {
    setTimeout(updateViewportVariables, 50);
});