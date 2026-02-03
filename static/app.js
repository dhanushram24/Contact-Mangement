/**
 * Contact Management Frontend Application
 * Handles login, authentication, and contact display
 */

// Configuration
const API_BASE_URL = "http://127.0.0.1:8000";

// DOM Elements
const elements = {
    loginForm: document.getElementById("loginForm"),
    usernameInput: document.getElementById("username"),
    passwordInput: document.getElementById("password"),
    errorDiv: document.getElementById("error"),
    loadingDiv: document.getElementById("loading"),
    userInfoDiv: document.getElementById("userInfo"),
    contactsSection: document.getElementById("contactsSection"),
    noContactsDiv: document.getElementById("noContacts"),
    contactsList: document.getElementById("contactsList"),
    displayUsername: document.getElementById("displayUsername"),
    displayDatabase: document.getElementById("displayDatabase"),
    displayToken: document.getElementById("displayToken"),
    displayCount: document.getElementById("displayCount")
};

// Utility Functions
const UI = {
    /**
     * Show loading state
     */
    showLoading() {
        elements.errorDiv.classList.remove("show");
        elements.userInfoDiv.classList.remove("show");
        elements.contactsSection.classList.remove("show");
        elements.noContactsDiv.classList.remove("show");
        elements.loadingDiv.classList.add("show");
    },

    /**
     * Hide loading state
     */
    hideLoading() {
        elements.loadingDiv.classList.remove("show");
    },

    /**
     * Show error message
     */
    showError(message) {
        elements.errorDiv.textContent = `Error: ${message}`;
        elements.errorDiv.classList.add("show");
    },

    /**
     * Hide error message
     */
    hideError() {
        elements.errorDiv.classList.remove("show");
    },

    /**
     * Reset all UI sections
     */
    resetUI() {
        elements.errorDiv.classList.remove("show");
        elements.userInfoDiv.classList.remove("show");
        elements.contactsSection.classList.remove("show");
        elements.noContactsDiv.classList.remove("show");
        elements.contactsList.innerHTML = "";
    }
};

// API Functions
const API = {
    /**
     * Login user and fetch contacts
     */
    async login(username, password) {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            mode: "cors",
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    },

    /**
     * Verify token
     */
    async verifyToken(token) {
        const response = await fetch(`${API_BASE_URL}/verify-token?token=${token}`, {
            method: "GET",
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error("Token verification failed");
        }

        return await response.json();
    }
};

// Display Functions
const Display = {
    /**
     * Display user information
     */
    showUserInfo(data) {
        elements.displayUsername.textContent = data.username;
        elements.displayDatabase.textContent = data.database;
        elements.displayToken.textContent = data.access_token;
        elements.displayCount.textContent = data.contact_count;
        elements.userInfoDiv.classList.add("show");
    },

    /**
     * Create contact card HTML
     */
    createContactCard(contact) {
        const card = document.createElement("div");
        card.className = "contact-card";

        const statusClass = contact.status == 2 ? "status-active" : "status-inactive";
        const statusText = contact.status == 2 ? "Active" : `Status ${contact.status}`;

        card.innerHTML = `
            <div class="contact-header">
                <div class="contact-name">${contact.f_name || ''} ${contact.l_name || ''}</div>
                <div class="contact-status ${statusClass}">${statusText}</div>
            </div>
            <div class="contact-details">
                <div class="detail-item">
                    <span class="detail-label">Email:</span> ${contact.email || 'N/A'}
                </div>
                <div class="detail-item">
                    <span class="detail-label">Created:</span> ${contact.creation_date || 'N/A'}
                </div>
                <div class="detail-item">
                    <span class="detail-label">Modified:</span> ${contact.modification_date || 'N/A'}
                </div>
                <div class="detail-item">
                    <span class="detail-label">ID:</span> ${contact.id || 'N/A'}
                </div>
            </div>
        `;

        return card;
    },

    /**
     * Display contacts list
     */
    showContacts(contacts) {
        if (!contacts || contacts.length === 0) {
            elements.noContactsDiv.classList.add("show");
            return;
        }

        elements.contactsList.innerHTML = "";

        contacts.forEach((contact) => {
            const card = this.createContactCard(contact);
            elements.contactsList.appendChild(card);
        });

        elements.contactsSection.classList.add("show");
    }
};

// Event Handlers
const EventHandlers = {
    /**
     * Handle login form submission
     */
    async handleLogin(event) {
        event.preventDefault();

        UI.resetUI();
        UI.showLoading();

        try {
            const username = elements.usernameInput.value;
            const password = elements.passwordInput.value;

            console.log("Attempting login for:", username);

            // Call login API
            const data = await API.login(username, password);

            console.log("Login successful:", data);

            UI.hideLoading();

            // Display user info
            Display.showUserInfo(data);

            // Display contacts
            Display.showContacts(data.contacts);

            // Store token (optional)
            sessionStorage.setItem("access_token", data.access_token);
            sessionStorage.setItem("username", data.username);
            sessionStorage.setItem("database", data.database);

        } catch (error) {
            console.error("Login error:", error);
            UI.hideLoading();
            UI.showError(error.message);
        }
    }
};

// Initialize Application
function init() {
    console.log("Contact Management App initialized");

    // Attach event listeners
    elements.loginForm.addEventListener("submit", EventHandlers.handleLogin);

    // Check for existing session
    const savedToken = sessionStorage.getItem("access_token");
    if (savedToken) {
        console.log("Found saved token, verifying...");
        API.verifyToken(savedToken)
            .then(data => {
                console.log("Token valid:", data);
                // Optionally auto-populate username
                elements.usernameInput.value = data.username;
            })
            .catch(err => {
                console.log("Token expired or invalid:", err);
                sessionStorage.clear();
            });
    }
}

// Start the application when DOM is ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}

// Export for potential module usage
if (typeof module !== "undefined" && module.exports) {
    module.exports = { UI, API, Display, EventHandlers };
}