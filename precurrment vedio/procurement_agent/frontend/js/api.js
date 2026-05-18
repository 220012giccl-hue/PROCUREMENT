/**
 * Procurement Agent API Module
 * Clean separation layer between Frontend and Backend
 * Handles all API calls with consistent error handling
 */

window.ProcurementAPI = {
    baseURL: '',

    /**
     * AI Assistant Chat
     * @param {string} message - User's message
     * @param {object} context - File context (optional)
     * @param {array} chatHistory - Previous messages (optional)
     * @param {function(string, string): void} [onChunk] - Callback for streaming chunks (chunk, fullText)
     * @returns {Promise<string>} AI response
     */
    async askAssistant(message, context = null, chatHistory = [], onChunk = null) {
        try {
            const payload = {
                question: message,
                chat_history: chatHistory
            };

            // Add file context if provided
            if (context && context.file_id) {
                payload.file_id = context.file_id;
            }

            const response = await fetch('/api/ai-chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            // Handle Streaming
            if (onChunk) {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullText = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    fullText += chunk;
                    console.log('AI Assistant Chunk:', chunk); // Deep console logging for chunks
                    onChunk(chunk, fullText);
                }
                return fullText;
            } else {
                // Classic mode (fallback)
                const data = await response.json();
                return data.response || 'No response from AI';
            }

        } catch (error) {
            console.error('❌ API Error in askAssistant:', error);
            throw error;
        }
    },

    /**
     * Upload File for Analysis
     * @param {File} file - File object to upload
     * @returns {Promise<object>} Upload result with file_id
     */
    async uploadFile(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/upload-file', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('❌ API Error in uploadFile:', error);
            throw error;
        }
    },

    /**
     * Fetch Emails from Provider
     * @param {string} provider - 'gmail' or 'outlook'
     * @returns {Promise<array>} List of emails
     */
    async fetchEmails(provider) {
        try {
            const response = await fetch(`/api/emails?provider=${provider}`);

            if (!response.ok) {
                throw new Error(`Failed to fetch emails: ${response.status}`);
            }

            const data = await response.json();
            // Backend returns a raw array; handle both formats for safety
            return Array.isArray(data) ? data : (data.emails || []);

        } catch (error) {
            console.error('❌ API Error in fetchEmails:', error);
            throw error;
        }
    },

    /**
     * Analyze Email Content
     * @param {string} emailBody - Email content
     * @param {string} emailId - Email ID
     * @returns {Promise<object>} Analysis result with products
     */
    async analyzeEmail(emailBody, emailId) {
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email_body: emailBody,
                    email_id: emailId
                })
            });

            if (!response.ok) {
                throw new Error(`Analysis failed: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('❌ API Error in analyzeEmail:', error);
            throw error;
        }
    },

    /**
     * Generate RFQ Drafts
     * @param {array} products - List of products
     * @returns {Promise<object>} Generated drafts
     */
    async generateDrafts(products) {
        try {
            const response = await fetch('/api/generate-drafts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ products })
            });

            if (!response.ok) {
                throw new Error(`Draft generation failed: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('❌ API Error in generateDrafts:', error);
            throw error;
        }
    },

    /**
     * Get Vendors List
     * @returns {Promise<array>} List of vendors
     */
    async getVendors() {
        try {
            const response = await fetch('/api/vendors');

            if (!response.ok) {
                throw new Error(`Failed to fetch vendors: ${response.status}`);
            }

            const data = await response.json();
            return data.vendors || [];

        } catch (error) {
            console.error('❌ API Error in getVendors:', error);
            throw error;
        }
    },

    /**
     * Save Vendor
     * @param {object} vendor - Vendor data
     * @returns {Promise<object>} Save result
     */
    async saveVendor(vendor) {
        try {
            const response = await fetch('/api/vendors', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(vendor)
            });

            if (!response.ok) {
                throw new Error(`Failed to save vendor: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('❌ API Error in saveVendor:', error);
            throw error;
        }
    },

    /**
     * Send Draft Email
     * @param {string} draftId - Draft ID to send
     * @returns {Promise<object>} Send result
     */
    async sendDraft(draftId) {
        try {
            const response = await fetch(`/api/send-draft?draft_id=${draftId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`Failed to send draft: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('❌ API Error in sendDraft:', error);
            throw error;
        }
    },

    /**
     * Improve Draft with AI
     * @param {string} draftId - Draft ID
     * @param {string} instruction - Improvement instruction
     * @returns {Promise<object>} Improved draft
     */
    async improveDraft(draftId, instruction) {
        try {
            const response = await fetch('/api/improve-draft', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    draft_id: draftId,
                    instruction
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to improve draft: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('❌ API Error in improveDraft:', error);
            throw error;
        }
    }
};

/**
 * RFQ Agent AI Assistant API (3-Layer Architecture)
 * Unified interface for the dedicated Assistant frontend
 */
window.RFQAgentAPI = {
    /**
     * AI Assistant Chat (Optimized)
     * @param {string} text - User's message
     * @param {string} context - Document context string (optional)
     * @param {array} chatHistory - Previous messages (optional)
     * @returns {Promise<string>} AI response
     */
    async askAssistant(text, context = null, chatHistory = []) {
        try {
            const payload = {
                question: text,
                context: context,
                chat_history: chatHistory
            };

            const response = await fetch('/api/ai-chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `AI Service Error: ${response.status}`);
            }

            const data = await response.json();
            return data.response || 'No response from the Procurement Agent.';

        } catch (error) {
            console.error('❌ RFQAgentAPI Error:', error);
            throw error;
        }
    }
};

console.log('✅ Procurement API & RFQAgentAPI Modules Loaded');
