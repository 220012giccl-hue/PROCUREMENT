let currentEmails = [];
let currentProducts = [];
let currentVendorDrafts = [];
let uploadedFiles = {}; // Store uploaded files with their IDs
let selectedDraftId = null;

// --- View Management ---

// Map each view to its nav item ID and parent section
const VIEW_NAV_MAP = {
    'dashboard': { navId: 'nav-dashboard', parent: null },
    'inbox': { navId: 'nav-inbox', parent: 'emails-section', parentBtn: 'nav-emails-parent' },
    'drafts': { navId: 'nav-drafts', parent: 'emails-section', parentBtn: 'nav-emails-parent' },
    'projects': { navId: 'nav-projects', parent: 'projects-section', parentBtn: 'nav-projects-parent' },
    'clients': { navId: 'nav-clients', parent: 'projects-section', parentBtn: 'nav-projects-parent' },
    'ai-assistant': { navId: 'nav-ai-assistant', parent: null },
    'vendors': { navId: 'nav-vendors', parent: 'suppliers-section', parentBtn: 'nav-suppliers-parent' },
    'comparison': { navId: 'nav-comparison', parent: 'suppliers-section', parentBtn: 'nav-suppliers-parent' },
    'settings': { navId: 'nav-settings', parent: null },
};

function switchView(viewName) {
    // Hide all views
    document.querySelectorAll('.view').forEach(v => v.style.display = 'none');

    // Remove active from all nav items and sub-items
    document.querySelectorAll('.nav-item, .nav-sub-item').forEach(el => el.classList.remove('active'));

    // Show target view with animation
    const targetView = document.getElementById(`${viewName}-view`);
    if (targetView) {
        targetView.style.display = 'block';
        targetView.classList.add('fade-in');
        setTimeout(() => targetView.classList.remove('fade-in'), 600);
    }

    // Activate the correct nav item
    const navConfig = VIEW_NAV_MAP[viewName];
    if (navConfig) {
        const navEl = document.getElementById(navConfig.navId);
        if (navEl) navEl.classList.add('active');

        // Auto-open parent section if this is a sub-item
        if (navConfig.parent) {
            const section = document.getElementById(navConfig.parent);
            const parentBtn = document.getElementById(navConfig.parentBtn);
            if (section && !section.classList.contains('open')) {
                section.classList.add('open');
                if (parentBtn) parentBtn.classList.add('open');
            }
        }
    }

    // Update header title
    const titles = {
        'dashboard': 'Dashboard',
        'inbox': 'Inbound Emails',
        'ai-assistant': 'AI Assistant',
        'vendors': 'Supplier Management',
        'drafts': 'Draft Emails',
        'comparison': 'Price Comparison',
        'projects': 'Recent Projects',
        'clients': 'Client Directory'
    };
    const titleEl = document.getElementById('view-title');
    if (titleEl) titleEl.innerText = titles[viewName] || 'Dashboard';

    // Load dashboard stats when switching to dashboard
    if (viewName === 'dashboard') loadDashboard();
    if (viewName === 'projects') loadProjects();
    if (viewName === 'clients') loadClients();
    if (viewName === 'inbox') {
        if (currentEmails.length > 0) renderEmailTable();
        else renderEmptyInbox();
    }
    if (viewName === 'drafts') loadDrafts();
}

let hasFetchedEmails = false;

function renderEmptyInbox() {
    const listBody = document.getElementById('email-list-body');
    if (!listBody) return;
    listBody.innerHTML = `
        <tr>
            <td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-muted); opacity: 0.7;">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;"><i class="fas fa-envelope-open-text"></i></div>
                <div style="font-size: 1.1rem; font-weight: 500;">Inbox is empty</div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem;">Click <strong>"Fetch Gmail"</strong> or <strong>"Fetch Outlook"</strong> above to retrieve and classify procurement requests.</div>
            </td>
        </tr>
    `;
}

// --- Sidebar Collapsible Sections ---

function toggleNavSection(sectionId, parentId) {
    const section = document.getElementById(sectionId);
    const parentEl = document.getElementById(parentId);
    if (!section) return;

    const isOpen = section.classList.contains('open');

    if (isOpen) {
        section.classList.remove('open');
        if (parentEl) parentEl.classList.remove('open');
    } else {
        section.classList.add('open');
        if (parentEl) parentEl.classList.add('open');
    }
}

// --- Toast Notification Utility ---

/**
 * Show a brief toast notification to the user.
 * @param {string} message - The message to display
 * @param {string} type - 'success' | 'warning' | 'info' | 'error'
 * @param {number} duration - Duration in ms (default 4000)
 */
function showToast(message, type = 'info', duration = 4000) {
    // Remove any existing toast
    const existing = document.getElementById('procurement-toast');
    if (existing) existing.remove();

    const colors = {
        success: '#22c55e',
        warning: '#f59e0b',
        info: '#3b82f6',
        error: '#ef4444'
    };

    const toast = document.createElement('div');
    toast.id = 'procurement-toast';
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: ${colors[type] || colors.info};
        color: #fff;
        padding: 0.85rem 1.4rem;
        border-radius: 10px;
        font-size: 0.95rem;
        font-weight: 500;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        z-index: 99999;
        max-width: 380px;
        line-height: 1.4;
        opacity: 0;
        transform: translateY(10px);
        transition: opacity 0.3s ease, transform 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });

    // Auto-dismiss
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 350);
    }, duration);
}

// --- Email Connect Functions ---

function connectGmail() {
    // Real OAuth2 Redirect
    window.location.href = '/api/auth/google/login';
}

function connectOutlook() {
    // Real OAuth2 Redirect
    window.location.href = '/api/auth/outlook/login';
}

// --- Logout ---

function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        if (window.procurementLogout) {
            window.procurementLogout();
        } else {
            sessionStorage.removeItem('procurement_agent_logged_in');
            window.location.href = 'login.html';
        }
    }
}

// --- Sidebar Chat History Rendering ---

// --- Sidebar Chat History Rendering ---

function renderSidebarHistory() {
    const sidebarList = document.getElementById('sidebar-chat-history');
    if (!sidebarList) return;

    sidebarList.innerHTML = '';
    savedChats.slice().reverse().forEach((chat, revIdx) => {
        const idx = savedChats.length - 1 - revIdx;
        const li = document.createElement('li');
        li.className = currentChatId === idx ? 'active' : '';

        const firstUserMsg = chat.messages.find(m => m.role === 'user')?.content || 'New Chat';
        const displayName = chat.name || (firstUserMsg.length > 30 ? firstUserMsg.substring(0, 30) + '...' : firstUserMsg);

        li.innerHTML = `
            <span class="chat-name-text">${displayName}</span>
            <div class="history-actions">
                <button class="history-action-btn edit-btn" onclick="event.stopPropagation(); renameChat(${idx});" title="Rename Chat">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="history-action-btn delete-btn" onclick="event.stopPropagation(); deleteChat(${idx});" title="Delete Chat">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        li.title = chat.name || firstUserMsg;
        li.onclick = () => {
            switchView('ai-assistant');
            switchChat(idx);
        };
        sidebarList.appendChild(li);
    });
}


// --- API Calls ---

async function syncAndRefresh(provider) {
    showToast(`🔄 Synchronizing ${provider} emails...`, 'info');
    hasFetchedEmails = true; // Mark as fetched
    try {
        const response = await fetch('/api/emails/fetch', { method: 'POST' });
        if (response.ok) {
            showToast('✅ Fetch started! Emails will appear shortly. Drafts auto-generate in ~15s.', 'success', 6000);
            
            // Step 1: Refresh inbox after 3s (emails appear quickly)
            setTimeout(() => {
                fetchEmails();
                showToast('📬 Inbox refreshed. Classifying emails...', 'info', 3000);
            }, 3000);
            
            // Step 2: Refresh inbox again after 8s (classification might still be running)
            setTimeout(fetchEmails, 8000);
            
            // Step 3: Reload drafts after 15s (AI draft generation takes time)
            setTimeout(() => {
                loadDrafts();
                showToast('📝 Checking for new auto-generated drafts...', 'info', 3000);
            }, 15000);
            
            // Step 4: Final refresh after 25s
            setTimeout(() => {
                fetchEmails();
                loadDrafts();
                showToast('✅ Sync complete! Check Drafts tab for auto-generated RFQs.', 'success', 5000);
            }, 25000);
        } else {
            showToast('❌ Failed to trigger sync.', 'error');
        }
    } catch (error) {
        console.error('Sync error:', error);
        showToast('❌ Sync error. Is the server running?', 'error');
    }
}

let _fetchEmailsDebounceTimer = null;
async function fetchEmails() {
    clearTimeout(_fetchEmailsDebounceTimer);
    _fetchEmailsDebounceTimer = setTimeout(_doFetchEmails, 300);
}

async function _doFetchEmails() {
    console.log("DEBUG: [app.js] Fetching emails from DB...");
    try {
        const query = document.getElementById('email-search-input')?.value || '';
        const category = document.getElementById('email-category-filter')?.value || '';
        const dateFrom = document.getElementById('email-date-from')?.value || '';
        const dateTo = document.getElementById('email-date-to')?.value || '';
        
        let url = '/api/emails?';
        if (query) url += `query=${encodeURIComponent(query)}&`;
        if (category) url += `classification=${encodeURIComponent(category)}&`;

        const response = await fetch(url);
        const emails = await response.json();
        
        // Frontend local filter for dates (since backend date filtering isn't implemented yet)
        let filtered = emails;
        if (dateFrom) {
            const from = new Date(dateFrom).getTime();
            filtered = filtered.filter(e => new Date(e.received_at).getTime() >= from);
        }
        if (dateTo) {
            const to = new Date(dateTo).getTime() + 86400000; // end of day
            filtered = filtered.filter(e => new Date(e.received_at).getTime() <= to);
        }

        currentEmails = filtered;
        renderEmailTable();
    } catch (error) {
        console.error("DEBUG: [app.js] Error fetching emails:", error);
    }
}

function applyInboxFilters() {
    renderFilterChips();
    fetchEmails();
}

function resetInboxFilters() {
    const inputs = ['email-search-input', 'email-category-filter', 'email-date-from', 'email-date-to'];
    inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    renderFilterChips();
    fetchEmails();
}

function renderFilterChips() {
    const container = document.getElementById('filter-chips-container');
    if (!container) return;
    container.innerHTML = '';

    const filters = [
        { id: 'email-search-input', label: 'Search', value: document.getElementById('email-search-input')?.value },
        { id: 'email-category-filter', label: 'Category', value: document.getElementById('email-category-filter')?.value },
        { id: 'email-date-from', label: 'From', value: document.getElementById('email-date-from')?.value },
        { id: 'email-date-to', label: 'To', value: document.getElementById('email-date-to')?.value }
    ];

    filters.forEach(f => {
        if (f.value) {
            const chip = document.createElement('div');
            chip.style.cssText = `
                background: var(--deep-blue);
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                display: flex;
                align-items: center;
                gap: 8px;
                animation: fadeIn 0.3s;
            `;
            const displayVal = f.id === 'email-category-filter' ? f.value.replace('_', ' ').toUpperCase() : f.value;
            chip.innerHTML = `
                <span><strong>${f.label}:</strong> ${displayVal}</span>
                <i class="fas fa-times-circle" style="cursor:pointer; opacity:0.8;" onclick="removeFilter('${f.id}')"></i>
            `;
            container.appendChild(chip);
        }
    });
}

function removeFilter(id) {
    const el = document.getElementById(id);
    if (el) el.value = '';
    applyInboxFilters();
}

function renderEmailTable() {
    const tableBody = document.getElementById('email-table-body');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    if (!currentEmails || currentEmails.length === 0) {
        if (!hasFetchedEmails) {
            renderEmptyInbox();
        } else {
            tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 2rem; opacity: 0.5;">No emails found matching filters.</td></tr>';
        }
        return;
    }

    const seenIds = new Set();
    currentEmails.forEach(email => {
        if (seenIds.has(email.id)) return;
        seenIds.add(email.id);

        const dateObj = new Date(email.received_at);
        const dateStr = dateObj.toLocaleDateString();
        const timeStr = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const isProcurement = email.classification === 'new_procurement';
        const isRead = email.is_read || false;
        
        const statusClass = isRead ? 'badge-success' : (isProcurement ? 'badge-pending' : 'badge-neutral');
        const statusLabel = isRead ? 'PROCESSED' : (isProcurement ? 'AWAITING REVIEW' : 'GENERAL');
        const categoryLabel = (email.requirement_category || email.classification || 'General').toUpperCase();

        const row = document.createElement('tr');
        row.className = isRead ? 'email-row-read' : 'email-row-unread';
        row.innerHTML = `
            <td><div style="font-weight:bold;">${dateStr}</div><div style="font-size:0.8rem; opacity:0.7;">${timeStr}</div></td>
            <td><div style="max-width:180px; overflow:hidden; text-overflow:ellipsis;">${email.sender}</div></td>
            <td style="max-width:350px; font-weight:500;">${email.subject}</td>
            <td><span class="badge ${isProcurement ? 'badge-warning' : 'badge-neutral'}">${categoryLabel}</span></td>
            <td><span class="badge ${statusClass}">${statusLabel}</span></td>
            <td>
                <button class="btn btn-small" onclick="analyzeEmail(${JSON.stringify(email).replace(/"/g, '&quot;')})" title="View Details"><i class="fas fa-search-plus"></i></button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

async function autoAnalyzeEmails() {
    console.log('🔍 Starting auto-analysis of ALL emails...');
    console.log('📧 Total emails fetched:', currentEmails.length);

    // Load relevance keywords from backend config
    let workKeywords = [
        'order', 'purchase', 'quote', 'rfq', 'request', 'supply', 'material', 'equipment',
        'procurement', 'quotation', 'qutation', 'urgent', 'cable', 'wire', 'pipe', 'valve', 'cement',
        'steel', 'brick', 'concrete', 'delivery', 'price', 'rate'
    ];

    try {
        const configResponse = await fetch('/data/config.json');
        const config = await configResponse.json();
        workKeywords = config.email_relevance_keywords || workKeywords;
        console.log('✅ Loaded keywords from config:', workKeywords);
    } catch (error) {
        console.log('⚠️ Using default keywords for email filtering');
    }

    let allProducts = [];
    let workRelatedCount = 0; // counts only work-related emails (for stats)
    let emailDomIndex = 0;    // counts ALL emails (for correct DOM targeting)

    // Process all emails returned by the backend (they are already filtered for procurement)
    for (const emailItem of currentEmails) {
        console.log(`\n📨 Analyzing relevant email ${emailDomIndex + 1}/${currentEmails.length}: "${emailItem.subject}"`);

        // Update DOM to show analysis progress
        const list = document.getElementById('email-list');
        if (list) {
            const items = list.getElementsByClassName('email-item');
            if (items[emailDomIndex]) {
                items[emailDomIndex].innerHTML += '<br><span style="color: #4CAF50; font-size: 0.8rem;">(Auto-analyzing...)</span>';
            }
        }
        workRelatedCount++;

        try {
            console.log('Calling LLM to analyze email and attachments...');
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email_body: emailItem.body, email_id: emailItem.id })
            });
            const data = await response.json();

            console.log('📦 Products extracted:', data.products);

            if (data.products && data.products.length > 0) {
                allProducts = allProducts.concat(data.products);
                console.log(`✅ Added ${data.products.length} products. Total so far: ${allProducts.length}`);
            }
        } catch (error) {
            console.error('❌ Auto-analysis failed for email:', emailItem.subject, error);
        }

        emailDomIndex++;
    }

    console.log(`\n🏁 Auto-analysis complete!`);
    console.log(`📊 Processed ${workRelatedCount} work-related emails`);
    console.log(`📦 Total products extracted: ${allProducts.length}`);

    // Bug 6 fix: notify the user of the result
    if (allProducts.length > 0) {
        currentProducts = allProducts;
        console.log('🚀 Generating drafts for ALL vendors with all products...');
        showToast(`✅ Analyzed ${workRelatedCount} email(s), found ${allProducts.length} product(s). Generating RFQ drafts...`, 'success');
        await generateDrafts();
    } else {
        if (workRelatedCount > 0) {
            showToast(`⚠️ Analyzed ${workRelatedCount} work-related email(s) but no products were extracted.`, 'warning');
        } else {
            showToast('ℹ️ No procurement-related emails found in your inbox.', 'info');
        }
        console.log('❌ No products found in any email');
    }
}

// renderEmailTable is now used instead

function selectEmail(email) {
    document.querySelectorAll('.email-item').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');

    analyzeEmail(email);
}

async function analyzeEmail(email) {
    const modal = document.getElementById('analysis-section');
    const content = document.getElementById('analysis-content');
    if (!modal || !content) {
        console.error("Analysis modal elements not found!");
        return;
    }
    
    modal.style.display = 'flex';
    content.innerHTML = `
        <div style="text-align:center; padding:20px;">
            <i class="fas fa-circle-notch fa-spin" style="font-size:2rem; color:var(--deep-blue);"></i>
            <p style="margin-top:10px;">Deeply analyzing email and extracting requirements...</p>
        </div>
    `;

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email_body: email.body, email_id: email.id })
        });
        const data = await response.json();
        
        let html = `
            <div class="analysis-results">
                <div style="background:#f8fafc; padding:15px; border-radius:10px; margin-bottom:1.5rem;">
                    <h4 style="margin-top:0;"><i class="fas fa-box-open"></i> Extracted Items</h4>
                    <ul style="margin-bottom:0;">
                        ${data.products.map(p => `<li><strong>${p.product}</strong>: ${p.quantity}</li>`).join('')}
                    </ul>
                </div>
                
                <div style="background:#f0f9ff; padding:15px; border-radius:10px;">
                    <h4 style="margin-top:0;"><i class="fas fa-users"></i> Matched Vendors</h4>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                        ${data.matched_vendors ? data.matched_vendors.map(v => `
                            <div style="background:white; padding:10px; border-radius:8px; border:1px solid var(--border-light);">
                                <strong>${v.name}</strong><br>
                                <span style="font-size:0.8rem; color:var(--text-muted);">${v.category} | ${v.email}</span>
                            </div>
                        `).join('') : '<p>No vendors matched yet.</p>'}
                    </div>
                </div>
            </div>
        `;
        content.innerHTML = html;
    } catch (error) {
        content.innerHTML = '<div class="alert alert-danger">Analysis failed. Please try again.</div>';
    }
}

async function generateDrafts() {
    const listUl = document.getElementById('drafts-list-ul');
    const previewEmpty = document.getElementById('drafts-preview-empty');

    // Switch to drafts view to show progress
    switchView('drafts');
    if (listUl) listUl.innerHTML = '<li style="padding: 20px; text-align: center; color: var(--text-muted);"><i class="fas fa-spinner fa-spin"></i> Generating drafts...</li>';
    if (previewEmpty) previewEmpty.textContent = 'Generating vendor drafts based on category...';

    try {
        const response = await fetch('/api/generate-drafts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ products: currentProducts })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server error (${response.status}): ${errorText}`);
        }

        const data = await response.json();
        currentVendorDrafts = Array.isArray(data) ? data : [];
        console.log('📧 Generated', currentVendorDrafts.length, 'drafts');
        renderDrafts();
    } catch (error) {
        console.error('Draft generation error:', error);
        if (listUl) listUl.innerHTML = '<li style="padding: 20px; text-align: center; color: #dc2626;">Generation failed.</li>';
        showToast(`Draft generation failed: ${error.message}`, 'error');
    }
}

async function loadDrafts() {
    try {
        const response = await fetch('/api/emails/vendor-drafts');
        if (!response.ok) throw new Error('Failed to load drafts');
        const data = await response.json();
        currentVendorDrafts = Array.isArray(data) ? data : [];
        console.log(`[app.js] Loaded ${currentVendorDrafts.length} drafts from DB`);
        renderDrafts();
    } catch (error) {
        console.error('[app.js] Error loading drafts:', error);
        showToast('Failed to load drafts', 'error');
    }
}

function renderDrafts() {
    const listUl = document.getElementById('drafts-list-ul');
    if (!listUl) return;
    listUl.innerHTML = '';

    if (!Array.isArray(currentVendorDrafts) || currentVendorDrafts.length === 0) {
        listUl.innerHTML = '<li style="padding: 20px; text-align: center; color: var(--text-muted);">No drafts available</li>';
        document.getElementById('drafts-preview-empty').style.display = 'flex';
        document.getElementById('drafts-preview-content').style.display = 'none';
        return;
    }

    currentVendorDrafts.forEach(draft => {
        const li = document.createElement('li');
        li.className = selectedDraftId === draft.id ? 'active-draft' : '';
        li.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div class="draft-subject">${draft.subject || draft.vendor_name}</div>
                ${draft.source_id ? '<span style="font-size: 0.7rem; color: var(--primary-color); background: rgba(59,130,246,0.1); padding: 2px 6px; border-radius: 4px;"><i class="fas fa-link"></i> Source</span>' : ''}
            </div>
            <div class="draft-meta">${draft.vendor_name} • ${draft.status.toUpperCase()}</div>
        `;
        li.onclick = () => selectDraft(draft.id);
        listUl.appendChild(li);
    });

    // Auto-select first draft if none selected
    if (!selectedDraftId && currentVendorDrafts.length > 0) {
        selectDraft(currentVendorDrafts[0].id);
    } else if (selectedDraftId) {
        showDraftPreview(selectedDraftId);
    }
}

function selectDraft(draftId) {
    selectedDraftId = draftId;
    renderDrafts();
    showDraftPreview(draftId);
}

function showDraftPreview(draftId) {
    const draft = currentVendorDrafts.find(d => d.id === draftId);
    const emptyMsg = document.getElementById('drafts-preview-empty');
    const content = document.getElementById('drafts-preview-content');

    if (!draft) {
        emptyMsg.style.display = 'flex';
        content.style.display = 'none';
        return;
    }

    emptyMsg.style.display = 'none';
    content.style.display = 'flex';

    document.getElementById('preview-vendor').textContent = draft.vendor_name;
    document.getElementById('preview-to').textContent = draft.recipient;
    document.getElementById('preview-subject').textContent = draft.subject;
    document.getElementById('preview-body').textContent = draft.body;

    // Admin Backlink Bar (Audit Trace)
    const backlinkContainer = document.getElementById('draft-backlink-container');
    if (backlinkContainer && draft.source_id) {
        backlinkContainer.innerHTML = `
            <div style="margin: 0.75rem 0; padding: 1rem; background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(37,99,235,0.05)); border-left: 5px solid var(--primary-color); border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="color: var(--text-primary); font-size: 0.9rem; font-weight: 500;">
                        <i class="fas fa-search-plus" style="color: var(--primary-color); margin-right: 0.5rem;"></i> 
                        Audit Trace: <span>Source Email Detected</span>
                    </div>
                    <button class="btn btn-sm btn-primary" onclick="viewEmailDetails(${draft.source_id})" style="padding: 4px 12px; font-size: 0.8rem;">
                        <i class="fas fa-eye"></i> View Detail Reference
                    </button>
                </div>
            </div>`;
        backlinkContainer.style.display = 'block';
    } else if (backlinkContainer) {
        backlinkContainer.style.display = 'none';
    }

    // Attach button actions
    const editBtn = document.getElementById('btn-edit-draft');
    const sendBtn = document.getElementById('btn-send-draft');
    const deleteBtn = document.getElementById('btn-delete-draft');

    editBtn.onclick = () => editDraft(draft.id);
    sendBtn.onclick = () => sendDraft(draft.id);
    deleteBtn.onclick = () => deleteDraft(draft.id);

    // Update button states
    sendBtn.disabled = draft.status === 'sent';
    sendBtn.style.opacity = draft.status === 'sent' ? '0.5' : '1';
}

function deleteDraft(draftId) {
    if (confirm('Are you sure you want to delete this draft?')) {
        currentVendorDrafts = currentVendorDrafts.filter(d => d.id !== draftId);
        if (selectedDraftId === draftId) {
            selectedDraftId = currentVendorDrafts.length > 0 ? currentVendorDrafts[0].id : null;
        }
        renderDrafts();
    }
}

let currentEditingDraft = null;

function editDraft(draftId) {
    const draft = currentVendorDrafts.find(d => d.id === draftId);
    if (!draft) return;

    currentEditingDraft = draft;
    document.getElementById('draft-recipient').value = `${draft.vendor_name} <${draft.recipient}>`;
    document.getElementById('draft-subject').value = draft.subject;
    document.getElementById('draft-body').value = draft.body;
    document.getElementById('draft-modal').style.display = 'flex';
}

function hideDraftModal() {
    document.getElementById('draft-modal').style.display = 'none';
    currentEditingDraft = null;
}

async function sendEditedDraft() {
    if (!currentEditingDraft) return;

    // Update draft with edited content
    currentEditingDraft.subject = document.getElementById('draft-subject').value;
    currentEditingDraft.body = document.getElementById('draft-body').value;

    // Send the draft
    await sendDraft(currentEditingDraft.id);
    hideDraftModal();
}

async function sendDraft(draftId) {
    const btn = document.getElementById('btn-send-draft');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    }

    try {
        const response = await fetch(`/api/send-draft?draft_id=${draftId}`, { method: 'POST' });
        if (response.ok) {
            showToast('Email sent successfully!', 'success');
            // Update status locally
            const draft = currentVendorDrafts.find(d => d.id === draftId);
            if (draft) draft.status = 'sent';
            renderDrafts();
        } else {
            const err = await response.json();
            showToast(`Failed: ${err.detail || 'Server error'}`, 'error');
        }
    } catch (error) {
        showToast('Failed to send email. Check connection.', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Quotation';
        }
    }
}

// --- New Draft Modal ---

function openNewDraftModal() {
    document.getElementById('nd-vendor-name').value = '';
    document.getElementById('nd-vendor-email').value = '';
    document.getElementById('nd-subject').value = '';
    document.getElementById('nd-body').value = '';
    document.getElementById('new-draft-modal').style.display = 'flex';
}

function closeNewDraftModal() {
    document.getElementById('new-draft-modal').style.display = 'none';
}

async function saveNewDraft(andSend = false) {
    const vendorName = document.getElementById('nd-vendor-name').value.trim();
    const vendorEmail = document.getElementById('nd-vendor-email').value.trim();
    const subject = document.getElementById('nd-subject').value.trim();
    const body = document.getElementById('nd-body').value.trim();

    if (!vendorEmail || !subject || !body) {
        showToast('Please fill in Vendor Email, Subject, and Body.', 'warning');
        return null;
    }

    try {
        // Create an RFQ-less draft via a lightweight endpoint
        const res = await fetch('/api/vendor-drafts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                vendor_name: vendorName || vendorEmail,
                vendor_email: vendorEmail,
                subject,
                body
            })
        });

        if (!res.ok) throw new Error(await res.text());
        const saved = await res.json();

        // Add to local list and re-render
        const draftEntry = {
            id: saved.id,
            vendor_name: vendorName || vendorEmail,
            recipient: vendorEmail,
            subject,
            body,
            status: 'pending'
        };
        currentVendorDrafts.unshift(draftEntry);
        renderDrafts();
        selectDraft(saved.id);
        closeNewDraftModal();
        showToast('Draft saved successfully!', 'success');

        if (andSend) {
            await sendDraft(saved.id);
        }
        return saved.id;
    } catch (err) {
        console.error('saveNewDraft error:', err);
        showToast('Failed to save draft: ' + err.message, 'error');
        return null;
    }
}

async function saveAndSendNewDraft() {
    await saveNewDraft(true);
}


let editingVendor = null;

async function loadVendors() {
    const container = document.getElementById('vendor-categories');
    container.innerHTML = '';

    try {
        const response = await fetch('/api/vendors');
        const vendors = await response.json();

        // Group vendors by category
        const categories = {
            'Electrician': [],
            'Plumber': [],
            'Builder': [],
            'Other': []
        };

        vendors.forEach(v => {
            const cat = v.category.toLowerCase();
            if (cat.includes('electric')) {
                categories['Electrician'].push(v);
            } else if (cat.includes('plumb')) {
                categories['Plumber'].push(v);
            } else if (cat.includes('build') || cat.includes('steel') || cat.includes('ac')) {
                categories['Builder'].push(v);
            } else {
                categories['Other'].push(v);
            }
        });

        // Render each category as a card
        Object.keys(categories).forEach(categoryName => {
            const categoryVendors = categories[categoryName];

            const categoryCard = document.createElement('div');
            categoryCard.className = 'category-card';

            let categoryHTML = `<h3>${categoryName}</h3>`;

            if (categoryVendors.length === 0) {
                categoryHTML += `<div class="empty-category">No suppliers in this category</div>`;
            } else {
                categoryVendors.forEach(v => {
                    categoryHTML += `
                        <div class="supplier-item">
                            <div class="supplier-name">${v.name}</div>
                            <div class="supplier-email">${v.email}</div>
                            <div class="supplier-actions">
                                <button class="btn btn-primary" onclick="editVendor('${v.email}')">
                                    <i class="fas fa-edit"></i> Edit
                                </button>
                                <button class="btn btn-danger" onclick="deleteVendor('${v.email}')">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </div>
                        </div>
                    `;
                });
            }

            categoryCard.innerHTML = categoryHTML;
            container.appendChild(categoryCard);
        });
    } catch (error) {
        console.error('Error loading vendors:', error);
        container.innerHTML = '<p style="color: red;">Failed to load suppliers</p>';
    }
}

async function editVendor(email) {
    try {
        const response = await fetch('/api/vendors');
        const vendors = await response.json();
        const vendor = vendors.find(v => v.email === email);

        if (vendor) {
            editingVendor = email;
            document.getElementById('v-name').value = vendor.name;
            document.getElementById('v-email').value = vendor.email;
            document.getElementById('v-category').value = vendor.category;
            document.getElementById('v-desc').value = vendor.description || '';
            document.getElementById('modal-title').innerText = 'Edit Supplier';
            showVendorModal();
        }
    } catch (error) {
        console.error('Error loading vendor for edit:', error);
    }
}

async function deleteVendor(email) {
    if (!confirm(`Are you sure you want to delete vendor: ${email}?`)) return;

    try {
        const response = await fetch(`/api/vendors/${encodeURIComponent(email)}`, {
            method: 'DELETE'
        });
        if (response.ok) {
            alert('Supplier deleted successfully!');
            loadVendors();
        }
    } catch (error) {
        alert('Failed to delete supplier.');
    }
}

function showVendorModal() {
    document.getElementById('vendor-modal').style.display = 'flex';
}

function hideVendorModal() {
    document.getElementById('vendor-modal').style.display = 'none';
    editingVendor = null;
    document.getElementById('modal-title').innerText = 'Add New Supplier';
    document.getElementById('v-name').value = '';
    document.getElementById('v-email').value = '';
    document.getElementById('v-category').value = 'Builder';
    document.getElementById('v-desc').value = '';
}

async function saveVendor() {
    const vendor = {
        name: document.getElementById('v-name').value,
        email: document.getElementById('v-email').value,
        category: document.getElementById('v-category').value,
        description: document.getElementById('v-desc').value
    };

    try {
        if (editingVendor) {
            // Update existing vendor
            await fetch(`/api/vendors/${encodeURIComponent(editingVendor)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(vendor)
            });
        } else {
            // Add new vendor
            await fetch('/api/vendors', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(vendor)
            });
        }
        hideVendorModal();
        loadVendors();
    } catch (error) {
        alert('Failed to save supplier.');
    }
}

// --- Price Comparison Testing ---

async function testComparison() {
    console.log('🧪 Generating 50 products demo data...');

    // --- Configuration ---
    const vendors = [
        "Saudi Electricity Co", "Saudi Cable Company", "Ragusa Minerals",
        "Portland Cement", "Zamil Industrial Investment Co", "99 Bikes (Osborne Park/Perth)",
        "TechFix Solutions", "Global Construction", "Alpha Steel", "Beta Supplies",
        "Gamma Tools", "Delta Pipes", "Oman Cables", "Bahra Cables"
    ];

    const productTypes = [
        // Electrician
        "Electrical Cable (3-core)", "Power Switch (20A)", "Circuit Breaker", "Generator (5kVA)",
        "Transformer", "Socket Outlet", "Junction Box", "Distribution Board", "Copper Wire",
        // Plumber
        "PVC Pipe (1 inch)", "Water Pump", "Gate Valve", "Pipe Flange", "Rubber Gasket",
        "Conduit Pipe", "Bathroom Tap", "Shower Head", "Drainage Pipe", "Water Tank",
        // Builder
        "Portland Cement", "Steel Bar (12mm)", "Red Bricks", "River Sand", "Gravel",
        "Concrete Mix", "Plywood Sheet", "Gypsum Board", "Roofing Sheet", "Ceramic Tiles"
    ];

    const specs = ["Type A", "Type B", "Heavy Duty", "Industrial", "Standard", "Premium", "Economy", "Pro", "Ultra"];

    // --- Generation Logic ---
    const comparisonResults = [];

    // Generate 50 unique products
    for (let i = 1; i <= 50; i++) {
        const type = productTypes[Math.floor(Math.random() * productTypes.length)];
        const spec = specs[Math.floor(Math.random() * specs.length)];
        const uniqueId = Math.floor(Math.random() * 1000);
        const productName = `${type} - ${spec} (Ref-${uniqueId})`;

        // Select 2-4 random vendors for this product
        const numVendors = 2 + Math.floor(Math.random() * 3);
        const selectedVendors = [];
        while (selectedVendors.length < numVendors) {
            const v = vendors[Math.floor(Math.random() * vendors.length)];
            if (!selectedVendors.includes(v)) selectedVendors.push(v);
        }

        // Generate quotes
        const productQuotes = [];
        const basePrice = 50 + Math.floor(Math.random() * 5000); // Random base price

        selectedVendors.forEach(vendor => {
            // Price variation +/- 25% allow logic
            const variance = (Math.random() * 0.5) - 0.25;
            const price = Math.floor(basePrice * (1 + variance));

            productQuotes.push({
                vendor: vendor,
                product: productName,
                price: price,
                quantity: `${10 + Math.floor(Math.random() * 100)} units`,
                highlight: null, // to be calculated
                recommended: false
            });
        });

        // Determine Highlights (Best/High)
        let minPrice = Infinity;
        let maxPrice = -Infinity;

        productQuotes.forEach(q => {
            if (q.price < minPrice) minPrice = q.price;
            if (q.price > maxPrice) maxPrice = q.price;
        });

        // Apply highlights
        productQuotes.forEach(q => {
            if (q.price === minPrice) {
                q.highlight = 'lowest';
                q.recommended = true; // Recommend the cheapest for demo
            } else if (q.price === maxPrice && productQuotes.length > 2) {
                q.highlight = 'highest';
            }
        });

        // Add to main results
        comparisonResults.push(...productQuotes);
    }

    console.log(`✅ Generated ${comparisonResults.length} quotes for 50 products.`);

    // Render
    renderComparisonTable(comparisonResults);
    alert('✅ Generated 50 Dummy Products Data!');
}

function renderComparisonTable(results) {
    const tbody = document.getElementById('comparison-body');
    tbody.innerHTML = '';

    if (!results || results.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4">No comparison data available.</td></tr>';
        return;
    }

    // Group by product
    const productGroups = {};
    results.forEach(item => {
        if (!productGroups[item.product]) {
            productGroups[item.product] = [];
        }
        productGroups[item.product].push(item);
    });

    // Render each product group
    for (const [product, quotes] of Object.entries(productGroups)) {
        // Product header row
        const headerRow = document.createElement('tr');
        headerRow.className = 'product-group-header';
        headerRow.innerHTML = `<td colspan="4"><i class="fas fa-box-open" style="margin-right: 8px; color: var(--deep-blue);"></i> ${product}</td>`;
        tbody.appendChild(headerRow);

        // Supplier rows
        quotes.forEach(quote => {
            const row = document.createElement('tr');

            // Price Formatting
            let priceHtml = `<span class="price-text">SAR ${quote.price.toLocaleString()}</span>`;
            if (quote.highlight === 'lowest') {
                priceHtml += ` <span class="badge-best"><i class="fas fa-check"></i> BEST</span>`;
            } else if (quote.highlight === 'highest') {
                priceHtml += ` <span class="badge-high"><i class="fas fa-arrow-up"></i> HIGH</span>`;
            }

            // Action Badge & View Button
            let actionHtml = `<div style="display: flex; align-items: center; gap: 0.5rem;">`;

            // View Doc Button
            actionHtml += `<button class="btn-view" onclick="alert('Viewing original document for ${quote.vendor}... (Dummy)')"><i class="fas fa-file-alt"></i> View</button>`;

            if (quote.recommended) {
                actionHtml += `<span class="badge-recommended"><i class="fas fa-star"></i> Recommended</span>`;
            }
            actionHtml += `</div>`;

            row.innerHTML = `
                <td style="font-weight: 500; color: var(--text-primary);">${quote.vendor}</td>
                <td style="color: var(--text-muted);">${quote.quantity || '-'}</td>
                <td>${priceHtml}</td>
                <td>${actionHtml}</td>
            `;
            tbody.appendChild(row);
        });
    }
}

// --- AI Assistant Chat Functions (3-Layer Architecture) ---

let chatHistory = [];
let savedChats = JSON.parse(localStorage.getItem('procurement_chats')) || [];
let currentChatId = null;

/**
 * Initialize AI Assistant on load
 */
document.addEventListener('DOMContentLoaded', () => {
    renderHistory();
    renderSidebarHistory();
    // Open Chat History section by default
    const histSection = document.getElementById('history-section');
    const histParent = document.getElementById('nav-history-parent');
    if (histSection) histSection.classList.add('open');
    if (histParent) histParent.classList.add('open');
});

/**
 * Render Chat History Sidebar
 */
function renderHistory() {
    const historyList = document.getElementById('chat-history-list');
    if (historyList) {
        historyList.innerHTML = '';
        savedChats.slice().reverse().forEach((chat, revIdx) => {
            const idx = savedChats.length - 1 - revIdx;
            const li = document.createElement('li');
            li.className = `history-item ${currentChatId === idx ? 'active' : ''}`;

            const firstUserMsg = chat.messages.find(m => m.role === 'user')?.content || 'New Chat';
            const displayName = chat.name || (firstUserMsg.length > 50 ? firstUserMsg.substring(0, 50) + '...' : firstUserMsg);

            li.innerHTML = `
                <span class="chat-name-text">${displayName}</span>
                <div class="history-actions">
                    <button class="history-action-btn edit-btn" onclick="event.stopPropagation(); renameChat(${idx});" title="Rename Chat">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="history-action-btn delete-btn" onclick="event.stopPropagation(); deleteChat(${idx});" title="Delete Chat">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            li.title = chat.name || firstUserMsg;
            li.onclick = () => switchChat(idx);
            historyList.appendChild(li);
        });
    }
    // Also update the sidebar history list
    renderSidebarHistory();
}

/**
 * Switch to a specific chat from history
 */
function switchChat(idx) {
    currentChatId = idx;
    const chat = savedChats[idx];
    chatHistory = [...chat.messages];

    toggleAIChatState(true);
    const msgContainer = document.getElementById('chat-messages');
    msgContainer.innerHTML = '';

    chat.messages.forEach(msg => {
        addChatMessage(msg.role, msg.content, msg.role === 'assistant');
    });

    renderHistory();
}

/**
 * Start a Fresh Chat
 */
function startNewChat() {
    currentChatId = null;
    toggleAIChatState(false);
    renderHistory();
}

/**
 * Save Current Session to History
 */
function saveChatToHistory() {
    if (chatHistory.length === 0) return;

    if (currentChatId !== null) {
        savedChats[currentChatId].messages = [...chatHistory];
    } else {
        savedChats.push({
            id: Date.now(),
            timestamp: new Date().toISOString(),
            messages: [...chatHistory],
            name: null // Optional custom name
        });
        currentChatId = savedChats.length - 1;
    }

    localStorage.setItem('procurement_chats', JSON.stringify(savedChats));
    renderHistory();
}

/**
 * Rename a specific chat
 */
function renameChat(idx) {
    const chat = savedChats[idx];
    const firstUserMsg = chat.messages.find(m => m.role === 'user')?.content || 'New Chat';
    const oldName = chat.name || firstUserMsg;

    const newName = prompt('Enter new name for this chat:', oldName);
    if (newName !== null && newName.trim() !== '') {
        savedChats[idx].name = newName.trim();
        localStorage.setItem('procurement_chats', JSON.stringify(savedChats));
        renderHistory();
        showToast('Chat renamed successfully!', 'success');
    }
}

/**
 * Delete a specific chat
 */
function deleteChat(idx) {
    if (confirm('Are you sure you want to delete this chat history?')) {
        savedChats.splice(idx, 1);

        // Handle current chat state
        if (currentChatId === idx) {
            startNewChat();
        } else if (currentChatId > idx) {
            currentChatId--;
        }

        localStorage.setItem('procurement_chats', JSON.stringify(savedChats));
        renderHistory();
        showToast('Chat deleted successfully!', 'success');
    }
}

/**
 * Voice Recognition Implementation
 */
function startVoiceRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Your browser does not support voice recognition.");
        return;
    }

    const recognition = new SpeechRecognition();
    const voiceBtn = document.getElementById('voice-btn');

    recognition.onstart = () => {
        voiceBtn.classList.add('listening');
        voiceBtn.innerHTML = '<i class="fas fa-microphone-alt"></i>';
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const input = document.getElementById('chat-input');
        if (input) {
            input.value = transcript;
            // Optionally auto-send:
            // sendChatMessage();
        }
    };

    recognition.onerror = (event) => {
        console.error('Voice Recognition Error:', event.error);
        voiceBtn.classList.remove('listening');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    };

    recognition.onend = () => {
        voiceBtn.classList.remove('listening');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    };

    recognition.start();
}

/**
 * Switch between Empty State and Chat View
 * @param {boolean} showChat - If true, shows chat container; otherwise shows empty state
 */
function toggleAIChatState(showChat) {
    const emptyState = document.getElementById('ai-empty-state');
    const chatContainer = document.getElementById('chat-messages-container');

    if (showChat) {
        if (emptyState) emptyState.style.display = 'none';
        if (chatContainer) chatContainer.style.display = 'block';
    } else {
        if (emptyState) emptyState.style.display = 'flex';
        if (chatContainer) chatContainer.style.display = 'none';
        // Clear chat content when resetting
        const msgContainer = document.getElementById('chat-messages');
        if (msgContainer) msgContainer.innerHTML = '';
        chatHistory = [];
        uploadedFiles = {};
        const filePreview = document.getElementById('uploaded-files-preview');
        if (filePreview) filePreview.innerHTML = '';
    }
}

/**
 * Handle Quick Action Questions
 * @param {string} question - The question to ask
 */
function askQuickQuestion(question) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = question;
        sendChatMessage();
    }
}

/**
 * Send Chat Message
 * Flow: User -> Controller (app.js) -> API Layer (api.js) -> Backend
 */
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    if (!input) return;

    const question = input.value.trim();
    if (!question) return;

    // 0. Prevent concurrent sends
    if (input.disabled) return;

    // 1. Update UI - Switch to chat view if in empty state
    toggleAIChatState(true);

    // 2. Add User Message
    addChatMessage('user', question);
    input.value = '';
    input.disabled = true; // Lock input

    // 3. Add Loading Indicator
    const loadingId = addChatMessage('assistant', '💭 Thinking...');

    try {
        // Prepare Context (Files)
        const fileIds = Object.keys(uploadedFiles);
        const context = fileIds.length > 0 ? { file_id: fileIds[0] } : null;

        // 4. Call API Layer
        // Ensure ProcurementAPI is available
        if (window.ProcurementAPI) {
            let accumulatedResponse = '';

            const responseText = await ProcurementAPI.askAssistant(
                question,
                context,
                chatHistory,
                (chunk, fullText) => {
                    accumulatedResponse = fullText;
                    // Update UI with partial response
                    updateChatMessage(loadingId, fullText);
                }
            );

            // 6. Update History
            chatHistory.push({ role: 'user', content: question });
            chatHistory.push({ role: 'assistant', content: responseText });

            // 7. Persist to localStorage History
            saveChatToHistory();
        } else {
            console.error('ProcurementAPI not found');
            throw new Error('API module not loaded');
        }

    } catch (error) {
        console.error('Chat Flow Error:', error);
        // Update thinking bubble to show error
        updateChatMessage(loadingId, '❌ Connection Error. Please try again.');
    } finally {
        input.disabled = false;
        input.focus();
    }
}

/**
 * Update an existing chat message content
 * @param {string} messageId - ID of the message to update
 * @param {string} newContent - New content to display
 */
function updateChatMessage(messageId, newContent) {
    const messageDiv = document.getElementById(messageId);
    if (!messageDiv) return;

    // Clear existing content (keep the strong tag if it exists in a specific structure, 
    // but our addChatMessage structure puts strong inside. Let's rebuild it properly)

    // Check if it's an assistant message
    const isAssistant = messageDiv.classList.contains('assistant-message');
    const label = isAssistant ? 'AI Assistant' : 'You';

    if (isAssistant) {
        // Parse Markdown
        let renderedContent = newContent;
        if (window.marked) {
            renderedContent = marked.parse(newContent);
        }

        messageDiv.innerHTML = `<strong>${label}:</strong><div style="margin: 0.5rem 0 0 0;">${renderedContent}</div>`;

        // Highlight code blocks
        if (window.hljs) {
            messageDiv.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    } else {
        messageDiv.textContent = newContent;
    }

    // Re-scroll
    const scrollContainer = document.getElementById('chat-messages-container');
    if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
    }
}

/**
 * Clear Chat and Reset to Empty State
 */
function clearChat() {
    // If there are messages, confirm before clearing
    const msgContainer = document.getElementById('chat-messages');
    if (msgContainer && msgContainer.children.length > 0) {
        if (confirm('Are you sure you want to clear the conversation?')) {
            toggleAIChatState(false);
        }
    } else {
        toggleAIChatState(false);
    }
}

/**
 * Add Message to Chat UI
 */
function addChatMessage(role, content, useMarkdown = false) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    // Create Message Bubble
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role === 'user' ? 'user-message' : 'assistant-message'}`;

    // Format Content
    if (role === 'assistant') {
        const strong = document.createElement('strong');
        strong.innerText = 'AI Assistant:';
        messageDiv.appendChild(strong);

        const contentDiv = document.createElement('div');
        if (useMarkdown && window.marked) {
            contentDiv.innerHTML = marked.parse(content);
            // Highlight code blocks
            if (window.hljs) {
                contentDiv.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            }
        } else {
            contentDiv.textContent = content;
        }
        messageDiv.appendChild(contentDiv);
    } else {
        messageDiv.textContent = content; // User message is plain text
    }

    // Append and Scroll
    messagesContainer.appendChild(messageDiv);

    // Scroll parent container
    const scrollContainer = document.getElementById('chat-messages-container');
    if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
    } else {
        // Fallback if container logic changed
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Return ID for removal (loading state)
    const msgId = 'msg-' + Date.now();
    messageDiv.id = msgId;
    return msgId;
}

// --- Draft Improvement Functions ---

let currentImprovingDraftId = null;

function showImproveModal(draftId) {
    currentImprovingDraftId = draftId;
    document.getElementById('improve-instructions').value = '';
    document.getElementById('improve-modal').style.display = 'flex';
}

function hideImproveModal() {
    document.getElementById('improve-modal').style.display = 'none';
    currentImprovingDraftId = null;
}

async function applyImprovement() {
    const instructions = document.getElementById('improve-instructions').value.trim();

    if (!instructions) {
        alert('Please provide improvement instructions.');
        return;
    }

    if (!currentImprovingDraftId) {
        alert('No draft selected.');
        return;
    }

    try {
        // Show loading state
        const improveBtn = event.target;
        const originalText = improveBtn.innerText;
        improveBtn.innerText = 'Improving...';
        improveBtn.disabled = true;

        const response = await fetch('/api/improve-draft', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                draft_id: currentImprovingDraftId,
                instructions: instructions
            })
        });

        if (!response.ok) {
            throw new Error('Failed to improve draft');
        }

        const data = await response.json();

        // Update the draft in currentVendorDrafts
        const draft = currentVendorDrafts.find(d => d.id === currentImprovingDraftId);
        if (draft) {
            draft.body = data.improved_body;
        }

        // Re-render drafts to show the improvement
        renderDrafts();

        // Close modal
        hideImproveModal();

        alert('✅ Draft improved successfully!');

    } catch (error) {
        console.error('Improvement error:', error);
        alert('❌ Failed to improve draft. Please try again.');
    }
}

// --- Dashboard Functions ---

async function loadDashboard() {
    try {
        const response = await fetch('/api/dashboard-stats');
        const stats = await response.json();

        if (document.getElementById('stat-emails')) document.getElementById('stat-emails').textContent = stats.total_emails || 0;
        if (document.getElementById('stat-vendors')) document.getElementById('stat-vendors').textContent = stats.total_vendors || 0;
        if (document.getElementById('stat-drafts')) document.getElementById('stat-drafts').textContent = stats.pending_drafts || 0;
        if (document.getElementById('stat-sent')) document.getElementById('stat-sent').textContent = stats.sent_rfqs || 0;

        // Render recent activity
        const activityList = document.getElementById('recent-activity');
        if (activityList && stats.recent_activity) {
            activityList.innerHTML = stats.recent_activity.map(item => `
                <li class="activity-item">
                    <div class="activity-info">
                        <span class="activity-action">${item.action}</span>
                        <span class="activity-time">${item.time}</span>
                    </div>
                </li>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load dashboard stats:', error);
    }
}

// --- File Upload Functions ---

async function handleFileSelect(event) {
    const files = event.target.files;
    for (let file of files) {
        await uploadFile(file);
    }
    // Reset input
    event.target.value = '';
}

function handleFileDrop(event) {
    event.preventDefault();
    event.target.classList.remove('drag-over');

    const files = event.dataTransfer.files;
    for (let file of files) {
        uploadFile(file);
    }
}

async function uploadFile(file) {
    // Show uploading status (optional, can be improved)
    console.log(`Uploading ${file.name}...`);

    try {
        // Use 3-Layer API Module
        if (window.ProcurementAPI) {
            const data = await ProcurementAPI.uploadFile(file);

            if (data.status === 'success') {
                // Store file info
                uploadedFiles[data.file_id] = data;

                // Add file preview card
                addFilePreview(data);

                // If in empty state, we might want to stay there or not. 
                // For now, staying in current state is fine as preview is shared.
            } else {
                throw new Error(data.message || 'Upload failed');
            }
        } else {
            throw new Error('API module not loaded');
        }

    } catch (error) {
        console.error('File upload error:', error);
        alert(`❌ Failed to upload ${file.name}. Please try again.`);
    }
}

function addFilePreview(fileData) {
    const preview = document.getElementById('uploaded-files-preview');
    const fileCard = document.createElement('div');
    fileCard.className = 'file-card';
    fileCard.innerHTML = `
        <i class="fas fa-file"></i>
        <span>${fileData.filename}</span>
        <i class="fas fa-times remove-btn" onclick="removeFile('${fileData.file_id}')"></i>
    `;
    preview.appendChild(fileCard);
}

function removeFile(fileId) {
    delete uploadedFiles[fileId];
    // Remove from UI
    const preview = document.getElementById('uploaded-files-preview');
    const cards = preview.querySelectorAll('.file-card');
    cards.forEach(card => {
        if (card.textContent.includes(fileId)) {
            card.remove();
        }
    });
}

// --- Draft Save Function ---

async function saveDraft() {
    if (!currentEditingDraft) return;

    // Update draft with edited content
    currentEditingDraft.subject = document.getElementById('draft-subject').value;
    currentEditingDraft.body = document.getElementById('draft-body').value;

    // Update in drafts array
    const draftIndex = currentVendorDrafts.findIndex(d => d.id === currentEditingDraft.id);
    if (draftIndex !== -1) {
        currentVendorDrafts[draftIndex] = currentEditingDraft;
    }

    // Re-render drafts
    renderDrafts();
    hideDraftModal();

    alert('✅ Draft saved successfully!');
}

// --- Improve from Edit Modal ---

function showImproveModalFromEdit() {
    if (!currentEditingDraft) return;
    currentImprovingDraftId = currentEditingDraft.id;
    document.getElementById('improve-instructions').value = '';
    document.getElementById('improve-modal').style.display = 'flex';
}

// Initial Load
switchView('dashboard');
loadVendors();
loadDashboard();
renderSidebarHistory();
checkAuthStatus();

// Check for redirect params
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('connected')) {
    const provider = urlParams.get('connected');
    alert(`Successfully connected to ${provider.toUpperCase()}`);
    // Clean URL
    window.history.replaceState({}, document.title, window.location.pathname);
}

async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const status = await response.json();

        // Update Gmail UI
        if (status.gmail && status.gmail.connected) {
            updateProviderUI('gmail', true, status.gmail.email);
        }

        // Update Outlook UI
        if (status.outlook && status.outlook.connected) {
            updateProviderUI('outlook', true, status.outlook.email);
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
    }
}

function updateProviderUI(provider, isConnected, email = '') {
    const statusEl = document.getElementById(`${provider}-status`);
    const badge = document.getElementById(`${provider}-badge`);
    const btn = document.getElementById(`${provider}-connect-btn`);
    const emailLabel = document.getElementById(`${provider}-connected-email`);

    if (isConnected) {
        if (statusEl) statusEl.classList.add('connected');
        if (badge) { badge.textContent = 'Connected'; badge.className = 'connection-badge connected'; }
        if (btn) {
            btn.innerHTML = '<i class="fas fa-check"></i> Connected';
            btn.className = `btn-connect-page ${provider}-connect connected`;
        }
        if (emailLabel) emailLabel.textContent = email;
    }
}
function createBacklinkContainer() {
    const parent = document.getElementById('drafts-preview-content');
    if (!parent) return null;
    
    let container = document.getElementById('draft-backlink-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'draft-backlink-container';
        // Insert before body
        const bodyElem = document.getElementById('preview-body');
        parent.insertBefore(container, bodyElem);
    }
    return container;
}

async function triggerSmartDrafts() {
    if (!currentProject) return;
    const btn = document.getElementById('btn-smart-drafts');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    }

    try {
        const response = await fetch(`/api/projects/${currentProject.id}/smart-drafts`, { method: 'POST' });
        const data = await response.json();
        if (response.ok) {
            showToast(`✨ Successfully generated ${data.count} specialized drafts!`, 'success');
            // Refresh lifecycle to show new drafts
            viewProject(currentProject.id);
        } else {
            showToast(`Failed: ${data.detail || 'Error'}`, 'error');
        }
    } catch (error) {
        console.error("Smart draft error:", error);
        showToast("Error triggering smart drafts.", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-magic"></i> Auto-Generate Multi-Vendor Drafts';
        }
    }
}

async function viewEmailDetails(emailOrId) {
    let email = null;
    if (typeof emailOrId === 'object') {
        email = emailOrId;
    } else if (typeof emailOrId === 'number') {
        // Find locally
        email = currentEmails.find(e => e.id === emailOrId);
        // Not found locally? Fetch from server
        if (!email) {
            try {
                const res = await fetch(`/api/emails/${emailOrId}`);
                if (res.ok) email = await res.json();
            } catch (err) { console.error("Fetch email error:", err); }
        }
    }
    
    if (!email) {
        showToast("Source email not found.", "error");
        return;
    }

    // Open in Modal for better professional feel
    const modal = document.getElementById('source-viewer-modal');
    if (modal) {
        document.getElementById('source-subject').textContent = email.subject;
        document.getElementById('source-meta').textContent = `From: ${email.sender} • Received: ${new Date(email.received_at).toLocaleString()}`;
        document.getElementById('source-body').innerHTML = email.body; 
        modal.style.display = 'flex';
        return;
    }

    // Fallback if modal not found
    switchView('inbox');
    const section = document.getElementById('analysis-section');
    const content = document.getElementById('analysis-content');
    if (section && content) {
        section.style.display = 'block';
        content.innerHTML = `
            <div style="border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1rem; padding-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="font-weight:bold; font-size: 1.1rem; color: #fff;">${email.subject}</div>
                    <div style="font-size: 0.9rem; opacity: 0.7; color: #94a3b8;">From: ${email.sender} · ${new Date(email.received_at).toLocaleString()}</div>
                </div>
                <button class="btn btn-small btn-outline" onclick="document.getElementById('analysis-section').style.display='none'"><i class="fas fa-times"></i></button>
            </div>
            <div style="white-space: pre-wrap; font-family: 'Inter', sans-serif; font-size: 0.95rem; line-height: 1.6; color: #e2e8f0; background: #1e293b; padding: 1.5rem; border-radius: 8px; border: 1px solid #334155;">
                ${email.body}
            </div>
        `;
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

function closeSourceViewer() {
    const modal = document.getElementById('source-viewer-modal');
    if (modal) modal.style.display = 'none';
}
