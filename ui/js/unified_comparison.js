/**
 * unified_comparison.js — Unified AI Market Research + Vendor Quote Comparison Table
 * v2.2 — ADDITIVE ONLY. Loads as a panel inside the Project Folder View modal.
 *
 * API used:  GET /api/unified-comparison/{project_id}
 * Triggered: via "📊 Unified Comparison" button injected into the project modal.
 */

(function () {
    'use strict';

    // ── Status Badge Colours ─────────────────────────────────────────────────
    const QUOTE_STATUS_COLOR = {
        SELECTED: '#22c55e',
        REVIEWED: '#3b82f6',
        PENDING: '#f59e0b',
        REJECTED: '#ef4444'
    };

    // ── Public: called by rfq_folder_view.js after project modal opens ────────
    window.unifiedComparison = {
        injectButton,
        openComparisonPanel
    };

    // ── Inject button into project modal ─────────────────────────────────────
    function injectButton(projectId, mountEl) {
        if (!mountEl) return;
        if (mountEl.querySelector('#btnUnifiedComparison')) return; // already injected

        const btn = document.createElement('button');
        btn.id = 'btnUnifiedComparison';
        btn.innerHTML = '📊 Unified Comparison';
        btn.style.cssText = `
            padding:8px 18px;border-radius:8px;border:1px solid #334155;
            background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;
            cursor:pointer;font-size:13px;font-weight:600;margin-top:4px;
            transition:opacity .2s;`;
        btn.onmouseover = () => btn.style.opacity = '0.85';
        btn.onmouseout = () => btn.style.opacity = '1';
        btn.onclick = () => openComparisonPanel(projectId);
        mountEl.appendChild(btn);
    }

    // ── Open/render the comparison panel ─────────────────────────────────────
    async function openComparisonPanel(projectId) {
        // Create or reset panel inside the existing project modal
        let panel = document.getElementById('unifiedCompPanel');
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'unifiedCompPanel';
            panel.style.cssText = `
                margin-top:20px;border-top:1px solid #334155;padding-top:20px;`;

            const modal = document.getElementById('projectFolderModal');
            if (modal) {
                const inner = modal.querySelector('div');
                if (inner) inner.appendChild(panel);
            } else {
                document.body.appendChild(panel);
            }
        }

        panel.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                <h3 style="margin:0;font-size:16px;color:#8b5cf6;">📊 Unified Comparison Table</h3>
                <button onclick="document.getElementById('unifiedCompPanel').style.display='none'"
                    style="background:transparent;border:none;color:#64748b;cursor:pointer;font-size:18px;">✕</button>
            </div>
            <p style="color:#64748b;font-size:12px;margin:0 0 12px;">
                AI Market Estimate vs. Real Vendor Quotes — one row per procurement item.
            </p>
            <div id="unifiedCompLoading" style="text-align:center;padding:20px;color:#64748b;">
                ⏳ Loading comparison data...
            </div>`;
        panel.style.display = 'block';

        try {
            const token = localStorage.getItem('token');
            const resp = await fetch(`/api/unified-comparison/${projectId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const json = await resp.json();

            document.getElementById('unifiedCompLoading').style.display = 'none';

            if (!json.success) {
                panel.insertAdjacentHTML('beforeend',
                    `<p style="color:#ef4444;">Error: ${json.error}</p>`);
                return;
            }

            const rows = json.data || [];
            const summary = json.summary || {};

            if (!rows.length) {
                panel.insertAdjacentHTML('beforeend', `
                    <div style="text-align:center;padding:24px;color:#64748b;">
                        No comparison data yet.<br>
                        <small>Vendor quotes and/or AI research data will appear here after pipeline runs.</small>
                    </div>`);
                return;
            }

            // ── Summary Pills ─────────────────────────────────────────────────
            panel.insertAdjacentHTML('beforeend', `
                <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;">
                    ${pill('Total Items', summary.total_items || 0, '#6366f1')}
                    ${pill('With AI Data', summary.items_with_ai_data || 0, '#38bdf8')}
                    ${pill('With Quotes', summary.items_with_vendor_quotes || 0, '#f59e0b')}
                    ${pill('Fully Covered', summary.items_fully_covered || 0, '#22c55e')}
                </div>`);

            // ── Comparison Table ──────────────────────────────────────────────
            const vendorNames = [...new Set(
                rows.flatMap(r => (r.vendor_quotes || []).map(q => q.vendor))
            )];

            const vendorCols = vendorNames.map(v =>
                `<th style="padding:10px 12px;text-align:left;color:#94a3b8;
                            font-size:11px;text-transform:uppercase;">
                    🏢 ${v}
                </th>`).join('');

            const tableRows = rows.map(row => {
                const aiCell = _buildAICell(row);
                const vendorCells = vendorNames.map(vName => {
                    const q = (row.vendor_quotes || []).find(x => x.vendor === vName);
                    return q ? _buildVendorCell(q, row.best_ai_price) : '<td style="padding:10px 12px;color:#334155;">—</td>';
                }).join('');

                const recBadge = row.recommended_vendor
                    ? `<span style="background:rgba(34,197,94,.15);color:#22c55e;
                                   border-radius:6px;padding:2px 8px;font-size:10px;">
                           ✅ Best: ${row.recommended_vendor}
                       </span>` : '';

                const varNote = row.variance_note
                    ? `<div style="font-size:11px;color:#94a3b8;margin-top:4px;">${row.variance_note}</div>` : '';

                return `
                    <tr style="border-bottom:1px solid #1e3a5f;">
                        <td style="padding:10px 12px;">
                            <div style="color:#e2e8f0;font-weight:600;">${row.item_name}</div>
                            ${recBadge}
                            ${varNote}
                        </td>
                        ${aiCell}
                        ${vendorCells}
                    </tr>`;
            }).join('');

            panel.insertAdjacentHTML('beforeend', `
                <div style="overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;font-size:13px;">
                        <thead>
                            <tr style="background:#0f172a;">
                                <th style="padding:10px 12px;text-align:left;color:#94a3b8;
                                           font-size:11px;text-transform:uppercase;min-width:180px;">
                                    Item
                                </th>
                                <th style="padding:10px 12px;text-align:left;color:#38bdf8;
                                           font-size:11px;text-transform:uppercase;min-width:160px;">
                                     AI Market Estimate
                                </th>
                                ${vendorCols}
                            </tr>
                        </thead>
                        <tbody>${tableRows}</tbody>
                    </table>
                </div>
                <div style="margin-top:12px;font-size:11px;color:#64748b;text-align:center;">
                    ⚠️ AI prices are indicative estimates only. Verify with vendor before purchasing.
                    Human approval required.
                </div>`);

        } catch (e) {
            const loadEl = document.getElementById('unifiedCompLoading');
            if (loadEl) loadEl.innerHTML = `<span style="color:#ef4444;">Failed to load: ${e.message}</span>`;
            console.error('[UnifiedComparison] Error:', e);
        }
    }

    // ── Cell Builders ─────────────────────────────────────────────────────────

    function _buildAICell(row) {
        if (!row.has_ai) {
            return `<td style="padding:10px 12px;color:#334155;font-style:italic;">No data yet</td>`;
        }
        const best = row.best_ai_price;
        const priceStr = best ? best.price_display : 'See report';
        const sources = (row.ai_market_data || []).slice(0, 2);

        const sourceLinks = sources.map(s => {
            const link = s.source_url
                ? `<a href="${s.source_url}" target="_blank"
                       style="color:#38bdf8;text-decoration:none;">${s.supplier}</a>`
                : s.supplier;
            return `<div style="font-size:11px;color:#64748b;">${link} — ${s.price_display || 'N/A'}</div>`;
        }).join('');

        return `
            <td style="padding:10px 12px;">
                <div style="color:#38bdf8;font-weight:700;">${priceStr}</div>
                ${sourceLinks}
            </td>`;
    }

    function _buildVendorCell(quote, bestAI) {
        const priceColor = _getPriceColor(quote.quoted_price, bestAI?.unit_price);
        const statusColor = QUOTE_STATUS_COLOR[quote.status] || '#94a3b8';

        return `
            <td style="padding:10px 12px;">
                <div style="color:${priceColor};font-weight:700;">${quote.price_display}</div>
                ${quote.lead_time ? `<div style="font-size:11px;color:#64748b;">📦 ${quote.lead_time}</div>` : ''}
                <span style="background:rgba(148,163,184,.1);color:${statusColor};
                             border-radius:4px;padding:2px 6px;font-size:10px;">
                    ${quote.status}
                </span>
            </td>`;
    }

    function _getPriceColor(vendorPrice, aiPrice) {
        if (!vendorPrice || !aiPrice) return '#e2e8f0';
        if (vendorPrice < aiPrice * 0.95) return '#22c55e'; // Green — vendor cheaper
        if (vendorPrice > aiPrice * 1.05) return '#f59e0b'; // Amber — vendor expensive
        return '#e2e8f0'; // Neutral — within 5%
    }

    // ── Helper: small summary pill ────────────────────────────────────────────
    function pill(label, value, color) {
        return `
            <div style="background:#0f172a;border:1px solid ${color}33;border-radius:8px;
                        padding:8px 14px;text-align:center;min-width:80px;">
                <div style="font-size:18px;font-weight:700;color:${color};">${value}</div>
                <div style="font-size:10px;color:#64748b;text-transform:uppercase;">${label}</div>
            </div>`;
    }

})();
