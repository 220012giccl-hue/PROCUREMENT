// RFQ Agent - API Client
// Handles all communication with FastAPI backend

if (typeof API_BASE_URL === 'undefined') {
    var API_BASE_URL = window.location.origin;
}

// Use a self-executing function to avoid global namespace pollution and re-declaration issues
(function() {
    if (window.RFQAgentAPIInitialized) return;

    class RFQAgentAPI {
        constructor() {
            this.baseURL = API_BASE_URL;
        }

        async request(endpoint, options = {}) {
            const url = `${this.baseURL}${endpoint}`;
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers
            };

            // Add Auth token if available
            const token = localStorage.getItem('token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            try {
                const response = await fetch(url, { 
                    ...options, 
                    headers,
                    credentials: 'include' // MANDATORY: Required to send HttpOnly session cookies
                });
                if (response.status === 401) {
                    console.warn('[API] Unauthorized access - redirecting to login');
                    const path = window.location.pathname;
                    if (!path.includes('login') && path !== '/' && path !== '') {
                        window.location.href = '/';
                    }
                }
                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    throw new Error(err.detail || `HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error(`API Error (${endpoint}):`, error);
                throw error;
            }
        }

        // --- AUTH & USER ---
        async login(email, password) {
            return await this.request('/api/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });
        }

        async getCurrentUser() {
            return await this.request('/api/user/me');
        }

        // --- DASHBOARD & STATS ---
        async getDashboardStats() {
            return await this.request('/api/dashboard/stats');
        }

        async getSystemStatus() {
            return await this.request('/api/dashboard/status');
        }

        async getRecentActivity(limit = 10) {
            return await this.request(`/api/activity?limit=${limit}`);
        }

        async getMorningBrief() {
            return await this.request('/api/morning-brief');
        }

        async getTasks() {
            return await this.request('/api/tasks');
        }

        async getSessionSummary(fromTime, toTime) {
            return await this.request(`/api/session-summary?from_time=${encodeURIComponent(fromTime)}&to_time=${encodeURIComponent(toTime)}`);
        }

        // --- AGENT CONTROL ---
        async processEmails() {
            return await this.request('/api/process-emails', { method: 'POST' });
        }

        async getAgentStatus() {
            return await this.request('/api/agent/status');
        }

        // --- EMAILS & THREADS ---
        async getEmails(filters = {}) {
            // filters can be: { thread_id, status, include_all }
            const params = new URLSearchParams();
            if (filters && typeof filters === 'object') {
                if (filters.thread_id) params.set('thread_id', filters.thread_id);
                if (filters.status) params.set('status', filters.status);
                if (filters.include_all) params.set('include_all', 'true');
            } else if (filters && typeof filters === 'string') {
                params.set('thread_id', filters);
            }
            const q = params.toString() ? `?${params.toString()}` : '';
            return await this.request(`/api/emails${q}`);
        }

        async getEmail(id) {
            return await this.request(`/api/emails/${id}`);
        }

        async addTagToEmail(emailId, tagId) {
            return await this.request(`/api/emails/${emailId}/tags/${tagId}`, { method: 'POST' });
        }

        async archiveEmail(id) {
            return await this.request(`/api/emails/${id}/archive`, { method: 'POST' });
        }

        async getThreads() {
            return await this.request('/api/threads');
        }

        async getThread(threadId) {
            return await this.request(`/api/threads/${threadId}`);
        }

        // --- TAGS ---
        async getTags() {
            return await this.request('/api/tags');
        }

        async createTag(name, color) {
            return await this.request('/api/tags', {
                method: 'POST',
                body: JSON.stringify({ name, color })
            });
        }

        // --- CONTACTS ---
        async getContacts() {
            return await this.request('/api/contacts');
        }

        async getContact(contactId) {
            return await this.request(`/api/contacts/${contactId}`);
        }

        async getContactIntelligence(contactId) {
            return await this.request(`/api/contacts/${contactId}/intelligence`);
        }

        async addContact(data) {
            return await this.request('/api/contacts', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        // --- DRAFTS ---
        async getDrafts(threadId = null) {
            const q = threadId ? `?thread_id=${threadId}` : '';
            return await this.request(`/api/drafts${q}`);
        }

        async getDraft(draftId) {
            return await this.request(`/api/drafts/${draftId}`);
        }

        async updateDraft(draftId, data) {
            return await this.request(`/api/drafts/${draftId}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        }

        async deleteDraft(draftId) {
            return await this.request(`/api/drafts/${draftId}`, { method: 'DELETE' });
        }

        async sendDraft(draftId) {
            return await this.request(`/api/drafts/${draftId}/send`, { method: 'POST' });
        }

        async saveDraft(data) {
            return await this.request('/api/drafts', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        // --- ATTACHMENTS ---
        async getAttachments(threadId = null) {
            const endpoint = threadId ? `/api/threads/${threadId}/attachments` : '/api/attachments';
            return await this.request(endpoint);
        }

        // --- FOLLOW-UPS ---
        async getFollowups() {
            return await this.request('/api/followups');
        }

        async approveFollowup(id) {
            return await this.request(`/api/followups/${id}/approve`, { method: 'POST' });
        }

        async dismissFollowup(id) {
            return await this.request(`/api/followups/${id}/dismiss`, { method: 'POST' });
        }

        // --- CALENDAR & MEETINGS ---
        async getCalendarEvents(days = 7) {
            return await this.request(`/api/calendar/events?days=${days}`);
        }

        async deleteCalendarEvent(provider, eventId) {
            return await this.request(`/api/calendar/events/${provider}/${eventId}`, { method: 'DELETE' });
        }

        async bookSuggestedMeeting(threadId, provider = 'google') {
            return await this.request('/api/meetings/book-suggested', {
                method: 'POST',
                body: JSON.stringify({ thread_id: threadId, provider })
            });
        }

        // --- PROCUREMENT ---
        async getProcurementList() {
            return await this.request('/api/procurement/list');
        }

        async saveToProcurementList(data) {
            return await this.request('/api/procurement/save', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        async deleteProcurementItem(id) {
            return await this.request(`/api/procurement/${id}`, {
                method: 'DELETE'
            });
        }

        async createRFQ(data) {
            return await this.request('/api/procurement/rfq/create', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        async getRFQs() {
            return await this.request('/api/procurement/rfqs');
        }

        async getRFQDetail(id) {
            return await this.request(`/api/procurement/rfqs/${id}`);
        }

        async updateRFQStatus(id, status) {
            return await this.request(`/api/procurement/rfqs/${id}/status`, {
                method: 'PATCH',
                body: JSON.stringify({ status })
            });
        }

        async getComparisons() {
            return await this.request('/api/procurement/comparison/list');
        }

        async getComparisonDetail(id) {
            return await this.request(`/api/procurement/comparison/${id}`);
        }

        async saveComparison(data) {
            return await this.request('/api/procurement/comparison/save', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        async getSuppliers() {
            return await this.request('/api/procurement/suppliers');
        }

        async addSupplier(data) {
            return await this.request('/api/procurement/suppliers', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        async updateSupplier(id, data) {
            return await this.request(`/api/procurement/suppliers/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        }

        async deleteSupplier(id) {
            return await this.request(`/api/procurement/suppliers/${id}`, {
                method: 'DELETE'
            });
        }

        // --- ASSISTANT ---
        async getChatHistory(conversationId = null) {
            const q = conversationId ? `?conversation_id=${conversationId}` : '';
            return await this.request(`/api/assistant/history${q}`);
        }

        async askAssistant(query, context = null, conversationId = null, mode = 'procurement') {
            return await this.request('/api/assistant/chat', {
                method: 'POST',
                body: JSON.stringify({ query, context, conversation_id: conversationId, mode })
            });
        }

        async getConversations(mode = 'procurement') {
            return await this.request(`/api/assistant/conversations?mode=${mode}`);
        }

        async createConversation(title, mode = 'procurement') {
            return await this.request('/api/assistant/conversations', {
                method: 'POST',
                body: JSON.stringify({ title, mode })
            });
        }

        async deleteConversation(id) {
            return await this.request(`/api/assistant/conversations/${id}`, { method: 'DELETE' });
        }

        async locateThreadByItem(itemName) {
            return await this.request(`/api/assistant/locate-thread-by-item?item_name=${encodeURIComponent(itemName)}`);
        }

        // --- SEARCH SOURCES ---
        async getSearchSources() {
            return await this.request('/api/procurement/search-sources');
        }

        async addSearchSource(data) {
            return await this.request('/api/procurement/search-sources', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        }

        async deleteSearchSource(id) {
            return await this.request(`/api/procurement/search-sources/${id}`, { method: 'DELETE' });
        }

        async updateSearchSource(id, data) {
            return await this.request(`/api/procurement/search-sources/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        }
    }

    // Create singleton instance
    const apiInstance = new RFQAgentAPI();
    window.api = apiInstance;
    window.RFQAgentAPI = apiInstance; 
    window.RFQAgentAPIClass = RFQAgentAPI;
    window.RFQAgentAPIReady = true;
    window.RFQAgentAPIInitialized = true;

    // Trigger custom event so other scripts know API is ready
    window.dispatchEvent(new CustomEvent('RFQAgentAPIReady'));
    console.log('[API] Executive Intelligence Client Ready');
})();
