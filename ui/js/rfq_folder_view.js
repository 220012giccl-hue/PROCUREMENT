/**
 * rfq_folder_view.js — RFQ Register Project Folder View (v2.1)
 * Adds a "Project View" toggle to the RFQ Register page.
 * ADDITIVE: existing list view untouched, toggled by button.
 */

(function () {
    'use strict';

    // ── State ────────────────────────────────────────────────────────────────
    let currentMode = 'list';   // 'list' | 'folders'
    let selectedProject = null;

    // ── Init ─────────────────────────────────────────────────────────────────
    function initFolderView() {
        injectProjectModal();
        loadProjects();
    }

    // ── Project Detail Modal ─────────────────────────────────────────────────
    function injectProjectModal() {
        if (document.getElementById('projectFolderModal')) return;
        const modal = document.createElement('div');
        modal.id = 'projectFolderModal';
        modal.style.cssText = `
            display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;
            align-items:center;justify-content:center;`;
        modal.innerHTML = `
            <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;
                        width:90%;max-width:860px;max-height:85vh;overflow-y:auto;padding:28px 32px;box-shadow:0 10px 25px rgba(0,0,0,0.1);">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                    <div>
                        <h2 id="pmProjectName" style="margin:0;color:#0f172a;font-size:20px;"></h2>
                        <span id="pmProjectRef" style="color:#64748b;font-size:13px;"></span>
                    </div>
                    <button onclick="window.rfqFolderView.closeModal()"
                        style="background:#f1f5f9;border:none;color:#475569;
                               border-radius:8px;padding:8px 16px;cursor:pointer;font-weight:600;font-size:13px;">✕ Close</button>
                </div>

                <!-- Per-project KPI pills -->
                <div id="pmKpis" style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;"></div>

                <!-- Reports -->
                <div id="pmReportsSection" style="display:none;margin-bottom:16px;">
                    <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;">Market Research Reports</p>
                    <div id="pmReportsList" style="display:flex;gap:8px;flex-wrap:wrap;"></div>
                </div>

                <!-- RFQ Table -->
                <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;">RFQs in this Project</p>
                <div style="overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;font-size:13px;">
                        <thead>
                            <tr style="background:#f8fafc;color:#64748b;text-transform:uppercase;font-size:11px;letter-spacing:0.05em;border-bottom:2px solid #e2e8f0;">
                                <th style="padding:12px 14px;text-align:left;">RFQ #</th>
                                <th style="padding:12px 14px;text-align:left;">Specs / Item</th>
                                <th style="padding:12px 14px;text-align:left;">Qty</th>
                                <th style="padding:12px 14px;text-align:left;">Required By</th>
                                <th style="padding:12px 14px;text-align:left;">Status</th>
                            </tr>
                        </thead>
                        <tbody id="pmRfqTableBody"></tbody>
                    </table>
                    <div id="pmEmpty" style="display:none;text-align:center;padding:24px;color:#64748b;">No RFQs in this project yet.</div>
                </div>
            </div>`;
        document.body.appendChild(modal);
    }



    // ── Load Projects ────────────────────────────────────────────────────────
    async function loadProjects() {
        const grid  = document.getElementById('folderGrid');
        const empty = document.getElementById('folderEmpty');
        if (!grid) return;
        grid.innerHTML = '<p style="color:#64748b;padding:16px;">Loading projects...</p>';

        try {
            const json = await window.api.request('/api/projects/list');
            if (!json.success || !json.data.length) {
                grid.innerHTML = '';
                empty.style.display = 'block';
                return;
            }

            // --- Populate Top KPI Cards ---
            let total = 0, open = 0, received = 0, approved = 0;
            json.data.forEach(p => {
                const k = p.kpis || {};
                total += (k.total || 0);
                open += (k.draft || 0) + (k.sent || 0) + (k.ready || 0);
                received += (k.quotes_received || 0);
                approved += (k.approved || 0);
            });
            const setStat = (id, val) => { const el = document.getElementById(id); if(el) el.textContent = val; };
            setStat('statTotal', total);
            setStat('statOpen', open);
            setStat('statReceived', received);
            setStat('statApproved', approved);
            // ------------------------------

            empty.style.display = 'none';
            grid.innerHTML = `
                <div style="overflow-x:auto;">
                    <table style="width:100%; border-collapse:collapse; text-align:left; font-size:13px; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08); border:1px solid #e2e8f0;">
                        <thead>
                            <tr style="background:#f8fafc; color:#64748b; text-transform:uppercase; font-size:11px; letter-spacing:0.05em; border-bottom:2px solid #e2e8f0;">
                                <th style="padding:14px 16px;">Project Name</th>
                                <th style="padding:14px 16px;">Reference</th>
                                <th style="padding:14px 16px; text-align:center;">Total RFQs</th>
                                <th style="padding:14px 16px; text-align:center;">Draft / Sent</th>
                                <th style="padding:14px 16px; text-align:center;">Quotes Received</th>
                                <th style="padding:14px 16px; text-align:right;">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${json.data.map(buildFolderCard).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (e) {
            grid.innerHTML = `<p style="color:#ef4444;">Error loading projects: ${e.message}</p>`;
        }
    }

    function buildFolderCard(p) {
        const k = p.kpis || {};
        const reportBadge = p.has_report
            ? '<span style="background:#dcfce7;color:#166534;font-size:10px;padding:2px 8px;border-radius:12px;margin-left:8px;font-weight:600;">Report</span>'
            : '';
        return `
        <tr style="border-bottom:1px solid #e2e8f0; transition:background 0.15s;"
            onmouseover="this.style.background='#f8fafc'"
            onmouseout="this.style.background='#fff'">
            <td style="padding:14px 16px; font-weight:700; color:#0f172a; font-size:14px;">
                📁 ${p.project_name} ${reportBadge}
            </td>
            <td style="padding:14px 16px; color:#64748b; font-size:13px;">${p.project_reference || '—'}</td>
            <td style="padding:14px 16px; text-align:center; font-weight:700; color:#6366f1;">${k.total || 0}</td>
            <td style="padding:14px 16px; text-align:center; font-size:13px;">
                <span style="color:#94a3b8;">${k.draft || 0} Draft</span>
                <span style="color:#cbd5e1; margin:0 4px;">/</span>
                <span style="color:#3b82f6; font-weight:600;">${k.sent || 0} Sent</span>
            </td>
            <td style="padding:14px 16px; text-align:center; font-weight:700; color:#f59e0b;">${k.quotes_received || 0}</td>
            <td style="padding:14px 16px; text-align:right;">
                <button onclick="event.stopPropagation(); window.rfqFolderView.openReportDrawer(${p.id}, '${(p.project_name||'').replace(/'/g,'\\&apos;')}');"
                    style="padding:7px 16px; background:linear-gradient(135deg,#6366f1,#8b5cf6); color:white; border:none; border-radius:8px; font-weight:600; cursor:pointer; font-size:12px; box-shadow:0 2px 6px rgba(99,102,241,0.25);"
                    onmouseover="this.style.opacity=0.85" onmouseout="this.style.opacity=1">
                    View Report
                </button>
            </td>
        </tr>`;
    }

    function kpiPill(label, value, color) {
        return `<div style="background:rgba(${hexToRgb(color)},.1);border:1px solid rgba(${hexToRgb(color)},.3);
                            border-radius:8px;padding:8px 10px;text-align:center;">
                    <div style="font-size:18px;font-weight:700;color:${color};">${value}</div>
                    <div style="font-size:10px;color:#64748b;text-transform:uppercase;">${label}</div>
                </div>`;
    }

    function hexToRgb(hex) {
        const r = parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);
        return `${r},${g},${b}`;
    }

    // ── Open Project Modal ───────────────────────────────────────────────────
    async function openProject(projectId) {
        selectedProject = projectId;
        const modal = document.getElementById('projectFolderModal');
        if (!modal) return;
        modal.style.display = 'flex';

        document.getElementById('pmProjectName').textContent = 'Loading…';
        document.getElementById('pmProjectRef').textContent  = '';
        document.getElementById('pmKpis').innerHTML          = '';
        document.getElementById('pmRfqTableBody').innerHTML  = '';
        document.getElementById('pmEmpty').style.display     = 'none';
        document.getElementById('pmReportsSection').style.display = 'none';

        try {
            const [kpiJson, rfqJson] = await Promise.all([
                window.api.request(`/api/projects/${projectId}/kpis`),
                window.api.request(`/api/projects/${projectId}/rfqs`)
            ]);

            // Update project name from KPIs response context
            const k = (kpiJson.success && kpiJson.data) || {};

            // KPI pills
            document.getElementById('pmKpis').innerHTML = [
                { label: 'Total RFQs',       val: k.total || 0,           color: '#6366f1' },
                { label: 'Sent',             val: k.sent || 0,            color: '#3b82f6' },
                { label: 'Quotes Received',  val: k.quotes_received || 0, color: '#f59e0b' },
                { label: 'Approved',         val: k.approved || 0,        color: '#22c55e' }
            ].map(x => `
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
                            padding:12px 18px;text-align:center;min-width:110px;">
                    <div style="font-size:22px;font-weight:800;color:${x.color};">${x.val}</div>
                    <div style="font-size:11px;color:#64748b;text-transform:uppercase;margin-top:2px;">${x.label}</div>
                </div>`).join('');

            // Reports
            const reports = k.reports || [];
            if (reports.length > 0) {
                document.getElementById('pmReportsSection').style.display = 'block';
                document.getElementById('pmReportsList').innerHTML = reports.map(r =>
                    `<a href="${r.url}" target="_blank"
                        style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                               padding:8px 14px;color:#0ea5e9;font-size:13px;text-decoration:none;font-weight:600;">
                        📄 ${r.filename}
                    </a>`).join('');
            }

            // RFQ rows
            const rfqs = (rfqJson.success && rfqJson.data) || [];
            if (!rfqs.length) {
                document.getElementById('pmEmpty').style.display = 'block';
            } else {
                const STATUS_COLORS = {
                    APPROVED:'#22c55e', SENT:'#3b82f6', DRAFT:'#94a3b8',
                    RECEIVED:'#f59e0b', REJECTED:'#ef4444', CLOSED:'#64748b'
                };
                document.getElementById('pmRfqTableBody').innerHTML = rfqs.map(r => {
                    const color = STATUS_COLORS[r.status] || '#94a3b8';
                    const date  = r.required_delivery_date
                        ? new Date(r.required_delivery_date).toLocaleDateString() : '—';
                    return `<tr style="border-bottom:1px solid #f1f5f9;">
                        <td style="padding:12px 14px;color:#0f172a;font-weight:600;">${r.rfq_number || '—'}</td>
                        <td style="padding:12px 14px;color:#334155;">${(r.technical_requirements||'').slice(0,60)||'—'}</td>
                        <td style="padding:12px 14px;color:#64748b;font-weight:500;">${r.quantity||'—'}</td>
                        <td style="padding:12px 14px;color:#64748b;">${date}</td>
                        <td style="padding:12px 14px;">
                            <span style="background:rgba(${hexToRgb(color)},.15);color:${color};
                                         border-radius:6px;padding:4px 10px;font-size:11px;font-weight:700;">
                                ${r.status}
                            </span>
                        </td>
                    </tr>`;
                }).join('');
            }

        } catch (e) {
            document.getElementById('pmProjectName').textContent = 'Error loading project';
            console.error('[FolderView] Project load error:', e);
        }

        // ── NEW v2.2: Inject "Unified Comparison" button ──────────────────────
        // Runs after data loads. Calls unified_comparison.js if available.
        try {
            if (window.unifiedComparison) {
                const kpiEl = document.getElementById('pmKpis');
                window.unifiedComparison.injectButton(projectId, kpiEl);
            }
        } catch (e) {
            console.warn('[FolderView] Could not inject comparison button:', e);
        }
    }

    function closeModal() {
        const modal = document.getElementById('projectFolderModal');
        if (modal) modal.style.display = 'none';
        // Also hide unified comparison panel if open
        const compPanel = document.getElementById('unifiedCompPanel');
        if (compPanel) compPanel.style.display = 'none';
        selectedProject = null;
    }

    // ── Report Drawer (View Report button) ──────────────────────────────────
    function openReportDrawer(projectId, projectName) {
        // Remove old drawer if exists
        const old = document.getElementById('reportDrawer');
        if (old) old.remove();

        const drawer = document.createElement('div');
        drawer.id = 'reportDrawer';
        drawer.style.cssText = `
            position:fixed;inset:0;z-index:10000;background:rgba(15,23,42,0.55);
            display:flex;align-items:flex-start;justify-content:flex-end;`;
        drawer.innerHTML = `
            <div id="reportDrawerPanel" style="
                width:min(860px,95vw);height:100vh;background:#fff;overflow-y:auto;
                box-shadow:-8px 0 40px rgba(0,0,0,0.18);display:flex;flex-direction:column;">
                <!-- Header -->
                <div style="padding:20px 28px;border-bottom:1px solid #e2e8f0;
                            display:flex;justify-content:space-between;align-items:center;
                            background:#f8fafc;position:sticky;top:0;z-index:1;">
                    <div>
                        <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;">AI vs Vendor Comparison</div>
                        <div style="font-size:18px;font-weight:800;color:#0f172a;">${projectName}</div>
                    </div>
                    <button onclick="document.getElementById('reportDrawer').remove()"
                        style="background:#f1f5f9;border:none;border-radius:8px;padding:8px 16px;
                               color:#475569;font-weight:600;cursor:pointer;font-size:13px;">
                        Close
                    </button>
                </div>
                <!-- Body -->
                <div id="reportDrawerBody" style="padding:24px 28px;flex:1;">
                    <div style="text-align:center;padding:40px;color:#64748b;">Loading data...</div>
                </div>
                <div style="padding:16px 28px;border-top:1px solid #e2e8f0;background:#f8fafc;
                            font-size:11px;color:#94a3b8;text-align:center;">
                    AI prices are indicative estimates from public sources. Verify with vendor before purchase.
                </div>
            </div>`;

        // Close on backdrop click
        drawer.addEventListener('click', e => { if (e.target === drawer) drawer.remove(); });
        document.body.appendChild(drawer);

        // Fetch data
        _loadDrawerData(projectId);
    }

    async function _loadDrawerData(projectId) {
        const body = document.getElementById('reportDrawerBody');
        if (!body) return;
        try {
            const [kpiJson, rfqJson, compJson] = await Promise.all([
                window.api.request(`/api/projects/${projectId}/kpis`),
                window.api.request(`/api/projects/${projectId}/rfqs`),
                window.api.request(`/api/unified-comparison/${projectId}`)
            ]);

            if (!compJson.success) {
                body.innerHTML = `<p style="color:#ef4444;text-align:center;">Error: ${compJson.error}</p>`;
                return;
            }

            const k = (kpiJson.success && kpiJson.data) || {};
            const rfqs = (rfqJson.success && rfqJson.data) || [];
            const cats = compJson.categories || {};
            const catNames = Object.keys(cats);

            // 1. KPI Pills
            const kpiHtml = [
                { label: 'Total RFQs',       val: k.total || 0,           color: '#6366f1' },
                { label: 'Sent',             val: k.sent || 0,            color: '#3b82f6' },
                { label: 'Quotes Received',  val: k.quotes_received || 0, color: '#f59e0b' },
                { label: 'Approved',         val: k.approved || 0,        color: '#22c55e' }
            ].map(x => `
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
                            padding:12px 18px;text-align:center;min-width:110px;">
                    <div style="font-size:22px;font-weight:800;color:${x.color};">${x.val}</div>
                    <div style="font-size:11px;color:#64748b;text-transform:uppercase;margin-top:2px;">${x.label}</div>
                </div>`).join('');

            // 2. Reports
            const reports = k.reports || [];
            const reportsHtml = reports.length > 0 ? `
                <div style="margin-bottom:24px;">
                    <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;">Market Research Reports</p>
                    <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        ${reports.map(r => `
                            <a href="${r.url}" target="_blank"
                                style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                                       padding:8px 14px;color:#0ea5e9;font-size:13px;text-decoration:none;font-weight:600;">
                                📄 ${r.filename}
                            </a>`).join('')}
                    </div>
                </div>` : '';

            // 3. RFQs Table
            const STATUS_COLORS = {
                APPROVED:'#22c55e', SENT:'#3b82f6', DRAFT:'#94a3b8',
                RECEIVED:'#f59e0b', REJECTED:'#ef4444', CLOSED:'#64748b'
            };
            const rfqRowsHtml = rfqs.map(r => {
                const color = STATUS_COLORS[r.status] || '#94a3b8';
                const date  = r.required_delivery_date
                    ? new Date(r.required_delivery_date).toLocaleDateString() : '—';
                return `<tr style="border-bottom:1px solid #f1f5f9;">
                    <td style="padding:12px 14px;color:#0f172a;font-weight:600;">${r.rfq_number || '—'}</td>
                    <td style="padding:12px 14px;color:#334155;">${(r.technical_requirements||'').slice(0,60)||'—'}</td>
                    <td style="padding:12px 14px;color:#64748b;font-weight:500;">${r.quantity||'—'}</td>
                    <td style="padding:12px 14px;color:#64748b;">${date}</td>
                    <td style="padding:12px 14px;">
                        <span style="background:rgba(${hexToRgb(color)},.15);color:${color};
                                     border-radius:6px;padding:4px 10px;font-size:11px;font-weight:700;">
                            ${r.status}
                        </span>
                    </td>
                </tr>`;
            }).join('');
            
            const rfqTableHtml = rfqs.length > 0 ? `
                <div style="margin-bottom:32px;">
                    <p style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;">RFQs in this Project</p>
                    <div style="overflow-x:auto;border-radius:12px;border:1px solid #e2e8f0;">
                        <table style="width:100%;border-collapse:collapse;font-size:13px;">
                            <thead>
                                <tr style="background:#f8fafc;color:#64748b;text-transform:uppercase;font-size:11px;letter-spacing:0.05em;border-bottom:2px solid #e2e8f0;">
                                    <th style="padding:12px 14px;text-align:left;">RFQ #</th>
                                    <th style="padding:12px 14px;text-align:left;">Specs / Item</th>
                                    <th style="padding:12px 14px;text-align:left;">Qty</th>
                                    <th style="padding:12px 14px;text-align:left;">Required By</th>
                                    <th style="padding:12px 14px;text-align:left;">Status</th>
                                </tr>
                            </thead>
                            <tbody>${rfqRowsHtml}</tbody>
                        </table>
                    </div>
                </div>` : '';

            // 4. Comparison Table (Dynamic by Category)
            let compHtml = '';
            
            if (catNames.length === 0) {
                compHtml = `
                    <div style="text-align:center;padding:48px;color:#94a3b8;border:2px dashed #e2e8f0;border-radius:12px;">
                        No vendor or AI comparison data yet.
                    </div>`;
            } else {
                compHtml = catNames.map(catName => {
                    const cat = cats[catName];
                    const vendors = cat.vendors || [];
                    const specHeaders = cat.spec_headers || [];
                    const items = cat.items || [];
                    
                    // Vendor headers
                    const vendorTH = vendors.map(v =>
                        `<th style="padding:12px 14px;text-align:left;min-width:160px;border-bottom:2px solid #e2e8f0;
                                    font-size:11px;color:#7c3aed;text-transform:uppercase;letter-spacing:.04em;border-right:1px solid #e2e8f0;">
                            ${v}
                        </th>`).join('');
                        
                    // Spec headers
                    const specTH = specHeaders.map(sh => 
                        `<th style="padding:12px 14px;text-align:left;min-width:100px;border-bottom:2px solid #e2e8f0;
                                    font-size:11px;color:#475569;text-transform:uppercase;letter-spacing:.04em;background:#f8fafc;">
                            ${sh}
                        </th>`).join('');

                    const trows = items.map(row => {
                        // AI Cell
                        const aiCell = row.has_ai
                            ? `<td style="padding:12px 14px;background:#f0f9ff;vertical-align:middle;border-right:1px solid #e2e8f0;">
                                    <div style="font-weight:700;color:#0369a1;font-size:15px;">${row.best_ai_price?.price_display || 'See report'}</div>
                                    ${(row.ai_market_data||[]).slice(0,2).map(s =>
                                        s.source_url
                                            ? `<div style="font-size:11px;color:#64748b;margin-top:4px;"><a href="${s.source_url}" target="_blank" style="color:#0369a1;">${s.supplier}</a> — ${s.price_display||'N/A'}</div>`
                                            : `<div style="font-size:11px;color:#64748b;margin-top:4px;">${s.supplier} — ${s.price_display||'N/A'}</div>`
                                    ).join('')}
                               </td>`
                            : `<td style="padding:12px 14px;color:#94a3b8;font-style:italic;vertical-align:middle;border-right:1px solid #e2e8f0;">No data</td>`;

                        // Vendor Cells
                        const STATUS_BG = {SELECTED:'#dcfce7',REVIEWED:'#e0f2fe',PENDING:'#fef9c3',REJECTED:'#fee2e2'};
                        const STATUS_C  = {SELECTED:'#166534',REVIEWED:'#0369a1',PENDING:'#854d0e',REJECTED:'#991b1b'};
                        const vCells = vendors.map((vName, vIdx) => {
                            const q = (row.vendor_quotes||[]).find(x => x.vendor === vName);
                            const rightBorder = 'border-right:1px solid #e2e8f0;';
                            if (!q) return `<td style="padding:12px 14px;color:#cbd5e1;vertical-align:middle;${rightBorder}">—</td>`;
                            
                            const ai = row.best_ai_price?.unit_price;
                            let pc = '#0f172a';
                            if (ai && q.quoted_price) {
                                if (q.quoted_price < ai*0.95) pc='#10b981';
                                else if (q.quoted_price > ai*1.05) pc='#f59e0b';
                            }
                            const bg = STATUS_BG[q.status]||'#f1f5f9';
                            const fc = STATUS_C[q.status]||'#475569';
                            return `<td style="padding:12px 14px;vertical-align:middle;${rightBorder}">
                                <div style="font-weight:700;color:${pc};font-size:15px;">${q.price_display}</div>
                                ${q.lead_time?`<div style="font-size:11px;color:#64748b;margin-top:3px;">Lead: ${q.lead_time}</div>`:''}
                                <span style="display:inline-block;margin-top:6px;background:${bg};color:${fc};
                                             font-size:10px;font-weight:700;padding:2px 8px;
                                             border-radius:6px;text-transform:uppercase;">${q.status}</span>
                            </td>`;
                        }).join('');

                        // Specs Cells (Merge AI and Selected Vendor specs)
                        const bestSpecs = row.best_ai_price?.specs || {};
                        const vendorSpecs = (row.vendor_quotes && row.vendor_quotes.length > 0) ? row.vendor_quotes[0].specs : {};
                        const mergedSpecs = { ...bestSpecs, ...vendorSpecs };
                        if (row.best_ai_price?.brand) mergedSpecs['Brand'] = row.best_ai_price.brand;
                        if (row.vendor_quotes && row.vendor_quotes.length > 0 && row.vendor_quotes[0].brand) mergedSpecs['Brand'] = row.vendor_quotes[0].brand;

                        const sCells = specHeaders.map(sh => {
                            const val = mergedSpecs[sh] || '—';
                            return `<td style="padding:12px 14px;vertical-align:middle;color:#334155;font-size:12px;">${val}</td>`;
                        }).join('');

                        const varCell = `<td style="padding:12px 14px;vertical-align:middle;font-size:12px;border-left:1px solid #e2e8f0;">
                            ${row.variance_note ? `<div style="color:#10b981;font-weight:600;">${row.variance_note}</div>` : ''}
                            ${row.recommended_vendor ? `<div style="margin-top:4px;background:#dcfce7;color:#166534;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:700;">Best: ${row.recommended_vendor}</div>` : ''}
                        </td>`;

                        return `<tr style="border-bottom:1px solid #f1f5f9;">
                            <td style="padding:12px 14px;font-weight:600;color:#0f172a;vertical-align:middle;border-right:1px solid #e2e8f0;">
                                <div style="display:flex;align-items:center;gap:12px;">
                                    ${row.best_ai_price?.image_url 
                                        ? `<img src="${row.best_ai_price.image_url}" style="width:40px;height:40px;object-fit:contain;border-radius:6px;border:1px solid #e2e8f0;background:#fff;" />` 
                                        : `<div style="width:40px;height:40px;border-radius:6px;background:#f1f5f9;border:1px solid #e2e8f0;display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:16px;">${cat.icon}</div>`}
                                    <span>${row.item_name}</span>
                                </div>
                            </td>
                            ${aiCell}${vCells}${sCells}${varCell}
                        </tr>`;
                    }).join('');

                    return `
                        <div style="margin-bottom:32px;">
                            <h3 style="color:${cat.color};font-size:14px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:12px;display:flex;align-items:center;gap:8px;">
                                <span>${cat.icon}</span> ${catName} Comparison
                            </h3>
                            <div style="overflow-x:auto;border-radius:12px;border:1px solid #e2e8f0;background:#fff;">
                                <table style="width:100%;border-collapse:collapse;font-size:13px;">
                                    <thead>
                                        <tr style="background:#f8fafc;">
                                            <th style="padding:12px 14px;text-align:left;border-bottom:2px solid #e2e8f0;min-width:220px;font-size:11px;color:#64748b;text-transform:uppercase;border-right:1px solid #e2e8f0;">Item</th>
                                            <th style="padding:12px 14px;text-align:left;border-bottom:2px solid #e2e8f0;min-width:160px;font-size:11px;color:#0369a1;text-transform:uppercase;background:#f0f9ff;border-right:1px solid #e2e8f0;">AI Market Est.</th>
                                            ${vendorTH}
                                            ${specTH}
                                            <th style="padding:12px 14px;text-align:left;border-bottom:2px solid #e2e8f0;font-size:11px;color:#10b981;text-transform:uppercase;border-left:1px solid #e2e8f0;">Variance / Best</th>
                                        </tr>
                                    </thead>
                                    <tbody>${trows}</tbody>
                                </table>
                            </div>
                        </div>`;
                }).join('');
            }

            body.innerHTML = `
                <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px;">${kpiHtml}</div>
                ${reportsHtml}
                ${rfqTableHtml}
                ${compHtml}
            `;

        } catch(e) {
            body.innerHTML = `<p style="color:#ef4444;text-align:center;">Failed: ${e.message}</p>`;
            console.error('[ReportDrawer]', e);
        }
    }

    // ── Public API ───────────────────────────────────────────────────────────
    window.rfqFolderView = { openProject, closeModal, openReportDrawer };

    // ── Auto-init on DOM ready ───────────────────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFolderView);
    } else {
        initFolderView();
    }
})();
