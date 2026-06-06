import os

file_path = r'c:\Users\22001\Desktop\procurement\Executive-RFQ-Assistant-main\ui\js\api.js'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = """        async getThread(threadId) {
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
        async getContactIntelligence(contactId) {
            return await this.request(`/api/contacts/${contactId}/intelligence`);
        }"""

if "async getTags()" not in content:
    content = content.replace(
        "        async getThread(threadId) {\n            return await this.request(`/api/threads/${threadId}`);\n        }",
        replacement
    )
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Methods added successfully.")
else:
    print("Methods already exist.")
