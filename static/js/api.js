/**
 * API Helper - Centralized API communication with JWT token management
 * Handles all backend API calls with automatic token injection and error handling
 */

class APIClient {
    constructor() {
        this.baseURL = window.location.origin;
        this.tokenKey = 'selfmade_token';
    }

    /**
     * Get JWT token from storage
     * @returns {string|null} JWT token or null
     */
    getToken() {
        return localStorage.getItem(this.tokenKey);
    }

    /**
     * Set JWT token in storage
     * @param {string} token - JWT token
     */
    setToken(token) {
        localStorage.setItem(this.tokenKey, token);
    }

    /**
     * Remove JWT token from storage
     */
    removeToken() {
        localStorage.removeItem(this.tokenKey);
    }

    /**
     * Check if user is authenticated
     * @returns {boolean} True if token exists
     */
    isAuthenticated() {
        return !!this.getToken();
    }

    /**
     * Build request headers with JWT token
     * @returns {Object} Headers object
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    }

    /**
     * Handle API response
     * @param {Response} response - Fetch response
     * @returns {Promise} Parsed JSON or error
     */
    async handleResponse(response) {
        const contentType = response.headers.get('content-type');

        // Parse JSON response
        let data;
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        // Handle errors
        if (!response.ok) {
            // Unauthorized - redirect to login
            if (response.status === 401) {
                this.removeToken();
                window.location.href = '/ui/login.html?error=session_expired';
                throw new Error('Unauthorized');
            }

            // Other errors
            const error = new Error(data.detail || data.message || 'Request failed');
            error.status = response.status;
            error.data = data;
            throw error;
        }

        return data;
    }

    /**
     * Make HTTP GET request
     * @param {string} endpoint - API endpoint
     * @returns {Promise} Response data
     */
    async get(endpoint) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'GET',
            headers: this.getHeaders()
        });

        return this.handleResponse(response);
    }

    /**
     * Make HTTP POST request
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request body
     * @returns {Promise} Response data
     */
    async post(endpoint, data = {}) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(data)
        });

        return this.handleResponse(response);
    }

    /**
     * Make HTTP PUT request
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request body
     * @returns {Promise} Response data
     */
    async put(endpoint, data = {}) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'PUT',
            headers: this.getHeaders(),
            body: JSON.stringify(data)
        });

        return this.handleResponse(response);
    }

    /**
     * Make HTTP DELETE request
     * @param {string} endpoint - API endpoint
     * @returns {Promise} Response data
     */
    async delete(endpoint) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'DELETE',
            headers: this.getHeaders()
        });

        return this.handleResponse(response);
    }

    // ==================== User & Auth ====================

    /**
     * Get current user profile
     * @returns {Promise} User profile
     */
    async getProfile() {
        return this.get('/me');
    }

    /**
     * Update user profile
     * @param {Object} data - Profile data {full_name, theme, notifications_enabled}
     * @returns {Promise} Update result
     */
    async updateProfile(data) {
        return this.put('/profile', data);
    }

    /**
     * Get user statistics
     * @returns {Promise} User stats
     */
    async getUserStats() {
        return this.get('/profile/stats');
    }

    /**
     * Logout user
     * @returns {Promise} Logout result
     */
    async logout() {
        await this.post('/auth/logout');
        this.removeToken();
        window.location.href = '/ui/login.html';
    }

    // ==================== Labs ====================

    /**
     * Get lab catalog
     * @returns {Promise} Array of available labs
     */
    async getLabs() {
        return this.get('/labs');
    }

    /**
     * Start a lab
     * @param {string} labId - Lab ID
     * @returns {Promise} Lab start result with port and access info
     */
    async startLab(labId) {
        return this.post('/labs/start', { lab_id: labId });
    }

    /**
     * Stop a lab
     * @param {string} labId - Lab ID
     * @returns {Promise} Lab stop result
     */
    async stopLab(labId) {
        return this.post('/labs/stop', { lab_id: labId });
    }

    /**
     * Get running labs status
     * @returns {Promise} Array of running labs
     */
    async getLabStatus() {
        return this.get('/labs/status');
    }

    // ==================== Services ====================

    /**
     * Get service catalog
     * @returns {Promise} Array of available services
     */
    async getServicesCatalog() {
        return this.get('/services/catalog');
    }

    /**
     * Start a service
     * @param {string} serviceId - Service ID
     * @returns {Promise} Service start result with credentials
     */
    async startService(serviceId) {
        return this.post('/services/start', { service_id: serviceId });
    }

    /**
     * Stop a service
     * @param {string} serviceId - Service ID
     * @returns {Promise} Service stop result
     */
    async stopService(serviceId) {
        return this.post('/services/stop', { service_id: serviceId });
    }

    /**
     * Get running services status
     * @returns {Promise} Array of running services
     */
    async getServiceStatus() {
        return this.get('/services/status');
    }

    /**
     * Get service credentials
     * @param {string} serviceId - Service ID
     * @returns {Promise} Service credentials
     */
    async getServiceCredentials(serviceId) {
        return this.get(`/services/${serviceId}/credentials`);
    }

    // ==================== Notifications ====================

    /**
     * Get user notifications
     * @param {boolean} unreadOnly - Fetch only unread notifications
     * @returns {Promise} Array of notifications
     */
    async getNotifications(unreadOnly = false) {
        const params = unreadOnly ? '?unread_only=true' : '';
        return this.get(`/notifications${params}`);
    }

    /**
     * Get unread notification count
     * @returns {Promise} Unread count object {count: number}
     */
    async getUnreadCount() {
        return this.get('/notifications/unread-count');
    }

    /**
     * Mark notification as read
     * @param {string} notificationId - Notification ID
     * @returns {Promise} Update result
     */
    async markNotificationRead(notificationId) {
        return this.post(`/notifications/${notificationId}/read`);
    }

    /**
     * Mark all notifications as read
     * @returns {Promise} Update result
     */
    async markAllNotificationsRead() {
        return this.post('/notifications/read-all');
    }

    /**
     * Delete notification
     * @param {string} notificationId - Notification ID
     * @returns {Promise} Delete result
     */
    async deleteNotification(notificationId) {
        return this.delete(`/notifications/${notificationId}`);
    }

    // ==================== Admin ====================

    /**
     * Create user (admin only)
     * @param {Object} data - User data {email, full_name, role}
     * @returns {Promise} Created user
     */
    async adminCreateUser(data) {
        return this.post('/admin/users', data);
    }

    /**
     * Get all users (admin only)
     * @returns {Promise} Array of users
     */
    async adminGetUsers() {
        return this.get('/admin/users');
    }

    /**
     * Update user role (admin only)
     * @param {string} email - User email
     * @param {string} role - New role (admin|user)
     * @returns {Promise} Update result
     */
    async adminUpdateUserRole(email, role) {
        return this.put(`/admin/users/${email}/role`, { role });
    }

    /**
     * Delete user (admin only)
     * @param {string} email - User email
     * @returns {Promise} Delete result
     */
    async adminDeleteUser(email) {
        return this.delete(`/admin/users/${email}`);
    }

    /**
     * Get audit logs (admin only)
     * @param {number} limit - Max number of logs
     * @returns {Promise} Array of audit logs
     */
    async adminGetAuditLogs(limit = 100) {
        return this.get(`/admin/audit-logs?limit=${limit}`);
    }

    /**
     * Get platform statistics (admin only)
     * @returns {Promise} Platform stats
     */
    async adminGetStats() {
        return this.get('/admin/stats');
    }
}

// Initialize global API client
const api = new APIClient();

// Helper function to extract token from URL (for OAuth callbacks)
function extractTokenFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (token) {
        api.setToken(token);

        // Remove token from URL for security
        const newURL = window.location.pathname;
        window.history.replaceState({}, document.title, newURL);

        return token;
    }

    return null;
}

// Check authentication on page load
function requireAuth() {
    if (!api.isAuthenticated()) {
        window.location.href = '/ui/login.html';
        return false;
    }
    return true;
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, api, extractTokenFromURL, requireAuth };
}
