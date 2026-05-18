
// --- Project & Client Management ---

let currentLifecycleProjectId = null;

async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const projects = await response.json();
        const tbody = document.getElementById('projects-table-body');
        if (!tbody) return;

        if (!projects.length) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:30px; color:#94a3b8;">No projects found. Fetch emails to auto-create projects from client requests.</td></tr>';
            return;
        }

        tbody.innerHTML = projects.map(p => `
            <tr>
                <td><span class="badge badge-neutral">${p.client_formatted_id}</span></td>
                <td><strong>${p.client_name}</strong></td>
                <td>
                    <strong>${p.name}</strong>
                    ${p.source_email_id ? `
                        <a href="#" onclick="viewEmailDetails(${p.source_email_id}); return false;" title="View Source Request" style="margin-left:8px; color:#60a5fa; font-size:0.8rem;">
                            <i class="fas fa-external-link-alt"></i> Original
                        </a>
                    ` : ''}
                </td>
                <td><span style="font-size: 0.85rem; color: var(--text-muted);">${p.client_email}</span></td>
                <td><span class="status-badge ${p.status}">${p.status.toUpperCase()}</span></td>
                <td>${new Date(p.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="viewProject(${p.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error("Load Projects Error:", err);
    }
}

// ... (loadClients removed from view but keeping for internal use if needed)

// ── View a specific project: open lifecycle modal ──
async function viewProject(projectId) {
    currentLifecycleProjectId = projectId;
    const modal = document.getElementById('lifecycle-modal');
    if (!modal) return;

    // Show modal with loading state
    modal.style.display = 'flex';
    document.getElementById('lc-project-name').textContent = 'Loading...';
    document.getElementById('lc-emails-list').innerHTML = '<p style="color:#94a3b8; font-size:0.85rem;">Loading...</p>';
    document.getElementById('lc-drafts-list').innerHTML = '<p style="color:#94a3b8; font-size:0.85rem;">Loading...</p>';
    document.getElementById('lc-responses-list').innerHTML = '<p style="color:#94a3b8; font-size:0.85rem;">Loading...</p>';

    try {
        const res = await fetch(`/api/projects/${projectId}/lifecycle`);
        if (!res.ok) throw new Error('Failed to load lifecycle');
        const data = await res.json();
        renderLifecycleModal(data);
    } catch (err) {
        console.error('viewProject error:', err);
        showToast('Failed to load project details.', 'error');
        modal.style.display = 'none';
    }
}

// ── Render lifecycle data into the modal ──
function renderLifecycleModal(data) {
    // Project header
    document.getElementById('lc-project-name').textContent = data.project.name;
    document.getElementById('lc-project-meta').textContent = `Created ${new Date(data.project.created_at).toLocaleDateString()} · Project ID: ${data.project.id}`;
    document.getElementById('lc-project-status').textContent = data.project.status.toUpperCase();
    document.getElementById('lc-project-status').className = `lc-status-badge lc-status-${data.project.status}`;

    // Client info
    document.getElementById('lc-client-name').textContent = `${data.client.name} (ID: ${data.client.id})`;
    document.getElementById('lc-client-email').textContent = data.client.email || '';

    // De-duplicate emails (by subject and body snippet) for clean UI
    const uniqueEmails = [];
    const seenEmails = new Set();
    data.emails.forEach(e => {
        const key = `${e.subject}|${e.body.substring(0, 100)}`;
        if (!seenEmails.has(key)) {
            seenEmails.add(key);
            uniqueEmails.push(e);
        }
    });

    // Counts
    document.getElementById('lc-email-count').textContent = uniqueEmails.length;
    document.getElementById('lc-draft-count').textContent = data.drafts.length;
    document.getElementById('lc-response-count').textContent = data.vendor_responses.length;
    document.getElementById('lc-quote-count').textContent = data.comparison_data.length;

    // Emails
    const emailList = document.getElementById('lc-emails-list');
    emailList.innerHTML = uniqueEmails.length
        ? uniqueEmails.map(e => `
            <div class="lc-item">
                <strong><i class="fas fa-envelope" style="color:#60a5fa;"></i> ${e.subject}</strong>
                <span class="lc-item-meta">${e.sender} · ${new Date(e.received_at).toLocaleDateString()}</span>
                <p class="lc-item-body">${e.body}</p>
            </div>`).join('')
        : '<p class="lc-empty-text">No client emails linked yet.</p>';

    // Drafts
    const draftList = document.getElementById('lc-drafts-list');
    draftList.innerHTML = data.drafts.length
        ? data.drafts.map(d => `
            <div class="lc-item">
                <strong><i class="fas fa-paper-plane" style="color:#a78bfa;"></i> ${d.subject}</strong>
                <span class="lc-item-meta">To: ${d.vendor_name} · <span class="lc-status-mini ${d.status}">${d.status.toUpperCase()}</span> ${d.sent_at ? '· Sent ' + new Date(d.sent_at).toLocaleDateString() : ''}</span>
                <p class="lc-item-body">${d.body}</p>
            </div>`).join('')
        : '<p class="lc-empty-text">No drafts generated yet.</p>';

    // Vendor Responses
    const responseList = document.getElementById('lc-responses-list');
    responseList.innerHTML = data.vendor_responses.length
        ? data.vendor_responses.map(r => `
            <div class="lc-item lc-item-green">
                <strong><i class="fas fa-reply" style="color:#34d399;"></i> ${r.subject}</strong>
                <span class="lc-item-meta">From: ${r.vendor_email} · ${new Date(r.received_at).toLocaleDateString()}</span>
                <p class="lc-item-body">${r.body}</p>
            </div>`).join('')
        : '<p class="lc-empty-text">No vendor responses yet.</p>';

    // Comparison Table
    renderLifecycleComparison(data.comparison_data);
}

function renderLifecycleComparison(quotes) {
    const table = document.getElementById('lc-comparison-table');
    const noQuotes = document.getElementById('lc-no-quotes');
    const tbody = document.getElementById('lc-comparison-body');

    if (!quotes.length) {
        table.style.display = 'none';
        noQuotes.style.display = 'block';
        return;
    }

    table.style.display = 'table';
    noQuotes.style.display = 'none';

    // Find best (lowest) price per product
    const priceByProduct = {};
    quotes.forEach(q => {
        if (!priceByProduct[q.product] || q.price < priceByProduct[q.product]) {
            priceByProduct[q.product] = q.price;
        }
    });

    tbody.innerHTML = quotes.map(q => {
        const isBest = q.price === priceByProduct[q.product];
        return `<tr class="${isBest ? 'lc-best-row' : ''}">
            <td>${q.vendor_email || '—'}</td>
            <td>${q.product}</td>
            <td><strong>${Number(q.price).toLocaleString()}</strong> ${isBest ? '<span class="lc-best-badge">BEST</span>' : ''}</td>
            <td>${q.unit || '—'}</td>
            <td style="font-size:0.8rem; color:#94a3b8;">${q.vendor_notes || '—'}</td>
        </tr>`;
    }).join('');
}

// ── View Client: show their projects ──
async function viewClient(clientId) {
    try {
        const res = await fetch(`/api/clients/${clientId}/projects`);
        if (!res.ok) throw new Error('Failed to load client projects');
        const data = await res.json();
        showToast(`${data.client.name}: ${data.projects.length} project(s). Opening first project...`, 'info');
        if (data.projects.length > 0) {
            viewProject(data.projects[0].id);
        }
    } catch (err) {
        showToast('Could not load client details.', 'error');
    }
}

// ── Close lifecycle modal ──
function closeLifecycleModal() {
    const modal = document.getElementById('lifecycle-modal');
    if (modal) modal.style.display = 'none';
    currentLifecycleProjectId = null;
}

// ── Toggle the vendor response input box ──
function toggleProcessBox() {
    const box = document.getElementById('lc-process-box');
    if (!box) return;
    box.style.display = box.style.display === 'none' ? 'block' : 'none';
}

// ── Submit vendor response for AI extraction ──
async function submitVendorResponse() {
    if (!currentLifecycleProjectId) return;

    const body = document.getElementById('lc-vendor-body').value.trim();
    const email = document.getElementById('lc-vendor-email-input').value.trim();
    const subject = document.getElementById('lc-vendor-subject').value.trim();

    if (!body || !email) {
        showToast('Please fill in vendor email and response text.', 'warning');
        return;
    }

    try {
        showToast('Extracting prices using AI...', 'info');
        const res = await fetch(`/api/projects/${currentLifecycleProjectId}/process-vendor-response`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vendor_email: email, subject: subject || 'Vendor Quote', body })
        });

        if (!res.ok) throw new Error('Processing failed');
        const result = await res.json();

        showToast(`Success! ${result.extracted_quotes.length} price items extracted.`, 'success');

        // Clear form and refresh modal
        document.getElementById('lc-vendor-body').value = '';
        document.getElementById('lc-vendor-email-input').value = '';
        document.getElementById('lc-vendor-subject').value = '';
        document.getElementById('lc-process-box').style.display = 'none';

        // Reload the lifecycle view to show new data
        await viewProject(currentLifecycleProjectId);
    } catch (err) {
        showToast('Failed to process vendor response.', 'error');
    }
}

// --- Manual Client & Project Creation ---

function showAddClientModal() {
    const modal = document.getElementById('manual-client-modal');
    if (modal) modal.style.display = 'flex';
}

async function showAddProjectModal() {
    const modal = document.getElementById('manual-project-modal');
    if (!modal) return;
    modal.style.display = 'flex';

    // Populate client dropdown
    try {
        const response = await fetch('/api/clients');
        const clients = await response.json();
        const select = document.getElementById('mp-client-id');
        if (!select) return;

        if (!clients || !clients.length) {
            select.innerHTML = '<option value="">No clients found. Add a client first.</option>';
            return;
        }

        select.innerHTML = clients.map(c => `
            <option value="${c.id}">${c.name || 'Unknown'} (${c.email})</option>
        `).join('');
    } catch (err) {
        console.error("Failed to load clients for project modal:", err);
    }
}

async function saveManualClient() {
    const name = document.getElementById('mc-name').value.trim();
    const email = document.getElementById('mc-email').value.trim();

    if (!name || !email) {
        showToast('Please provide both name and email.', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/clients', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email })
        });

        if (!response.ok) throw new Error('Failed to save client');

        showToast('Client added successfully!', 'success');
        hideModal('manual-client-modal');
        loadClients(); // Refresh list

        // Clear fields
        document.getElementById('mc-name').value = '';
        document.getElementById('mc-email').value = '';
    } catch (err) {
        showToast('Error saving client.', 'error');
    }
}

async function saveManualProject() {
    const name = document.getElementById('mp-name').value.trim();
    const clientId = document.getElementById('mp-client-id').value;

    if (!name || !clientId) {
        showToast('Please provide project name and select a client.', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, client_id: parseInt(clientId) })
        });

        if (!response.ok) throw new Error('Failed to save project');

        showToast('Project created successfully!', 'success');
        hideModal('manual-project-modal');
        loadProjects(); // Refresh list

        // Clear fields
        document.getElementById('mp-name').value = '';
    } catch (err) {
        showToast('Error saving project.', 'error');
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'none';
}
