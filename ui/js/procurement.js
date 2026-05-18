/**
 * Procurement Assistant Utilities
 * Handles rendering, parsing, and specific procurement actions
 */

function renderProcurementCard(container, text) {
    const sections = parseProcurementSections(text);

    // Extract badges from Section 7 if it exists
    let badgesHtml = '';
    const badgesSectionIndex = sections.findIndex(s => s.title.toUpperCase().includes('INTELLIGENCE BADGES'));
    if (badgesSectionIndex !== -1) {
        const badgesBody = sections[badgesSectionIndex].body;
        
        // Parse the fields
        const matchConf = badgesBody.match(/CONFIDENCE:\s*(.*)/i);
        const matchSource = badgesBody.match(/SOURCE:\s*(.*)/i);
        const matchMissing = badgesBody.match(/MISSING:\s*(.*)/i);
        const matchChecked = badgesBody.match(/CHECKED:\s*(.*)/i);

        const conf = matchConf ? matchConf[1].trim() : 'N/A';
        const source = matchSource ? matchSource[1].trim() : 'N/A';
        const missing = matchMissing ? matchMissing[1].trim() : 'None';
        const checked = matchChecked ? matchChecked[1].trim() : 'N/A';
        
        let confColor = conf.toUpperCase().includes('HIGH') ? '#10b981' : (conf.toUpperCase().includes('MEDIUM') ? '#f59e0b' : '#ef4444');

        badgesHtml = `
            <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; margin-bottom:12px; padding:12px; background:#f8fafc; border-radius:8px; border:1px solid #e2e8f0; font-size:0.75rem;">
                <div style="display:flex; align-items:center; gap:4px;">
                    <span style="color:#64748b; font-weight:600;">Confidence:</span>
                    <span style="color:${confColor}; font-weight:700;">${conf}</span>
                </div>
                <div style="width:1px; background:#e2e8f0; margin:0 4px;"></div>
                <div style="display:flex; align-items:center; gap:4px;">
                    <span style="color:#64748b; font-weight:600;">Source:</span>
                    <span style="color:#1e293b;">${source}</span>
                </div>
                <div style="width:1px; background:#e2e8f0; margin:0 4px;"></div>
                <div style="display:flex; align-items:center; gap:4px;">
                    <span style="color:#64748b; font-weight:600;">Last Checked:</span>
                    <span style="color:#1e293b;">${checked}</span>
                </div>
                ${missing && missing.toUpperCase() !== 'NONE' && missing !== 'N/A' ? `
                <div style="width:100%; margin-top:4px; display:flex; gap:4px;">
                    <span style="color:#ef4444; font-weight:600;">⚠️ Missing Data:</span>
                    <span style="color:#64748b;">${missing}</span>
                </div>` : ''}
            </div>
        `;

        // Remove the section so it doesn't render in the normal loop
        sections.splice(badgesSectionIndex, 1);
    }

    container.innerHTML = `
        <div class="procurement-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
            Procurement Intelligence Output
        </div>
        ${badgesHtml}
        <div class="procurement-content">
            ${sections.map(s => `
                <div class="procurement-section">
                    <div class="section-title">${s.title}</div>
                    <div class="section-body">${formatSectionBody(s.body, s.title)}</div>
                </div>
            `).join('')}
        </div>
        <div class="action-buttons-row">
            <button class="btn-action" onclick="handleProcAction('rfq')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                Create RFQ
            </button>
            <button class="btn-action" onclick="handleProcAction('compare')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                Compare Suppliers
            </button>
            <button class="btn-action" onclick="handleProcAction('save')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
                Save to List
            </button>
            <button class="btn-action" onclick="handleProcAction('email')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                Draft Email
            </button>
            <button class="btn-action" onclick="handleProcAction('pdf')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                Export PDF
            </button>
        </div>
    `;
}

function parseProcurementSections(text) {
    const sections = [];
    const lines = text.split('\n');
    let currentSection = null;

    lines.forEach(line => {
        const match = line.match(/^SECTION \d+:\s*(.*)/i);
        if (match) {
            if (currentSection) sections.push(currentSection);
            currentSection = { title: match[1].trim(), body: '' };
        } else if (currentSection) {
            currentSection.body += line + '\n';
        }
    });
    if (currentSection) sections.push(currentSection);

    return sections.length > 0 ? sections : [{ title: 'Analysis', body: text }];
}

function getRobustSourceLink(source, name, supplier) {
    const cleanSource = (source || '').trim();
    if (!cleanSource || cleanSource === '#' || cleanSource.toLowerCase() === 'placeholder') {
        const query = encodeURIComponent(name + ' ' + (supplier || ''));
        if (supplier && supplier.toLowerCase().includes('bunnings')) {
            return `https://www.bunnings.com.au/search/products?q=${query}`;
        } else if (supplier && supplier.toLowerCase().includes('sydney')) {
            return `https://sydneytools.com.au/search?q=${query}`;
        } else if (supplier && supplier.toLowerCase().includes('blackwoods')) {
            return `https://www.blackwoods.com.au/search?q=${query}`;
        }
        return `https://www.google.com/search?q=${query}`;
    }
    
    // Rewrite fake simulated detail pages (like _p0021234 on Bunnings) to be direct searches instead
    const lowerSource = cleanSource.toLowerCase();
    const isFakeBunnings = lowerSource.includes('bunnings.com.au') && (lowerSource.includes('_p0') || lowerSource.includes('/oztrail-') || lowerSource.includes('/heavy-duty-'));
    const isFakeSydney = lowerSource.includes('sydneytools.com.au') && lowerSource.includes('/product/');
    
    if (isFakeBunnings || isFakeSydney) {
        const query = encodeURIComponent(name);
        if (lowerSource.includes('bunnings.com.au')) {
            return `https://www.bunnings.com.au/search/products?q=${query}`;
        } else if (lowerSource.includes('sydneytools.com.au')) {
            return `https://sydneytools.com.au/search?q=${query}`;
        }
    }
    
    return cleanSource;
}

function getRobustProductImage(image, name) {
    const cleanImg = (image || '').trim();
    if (!cleanImg || cleanImg.toLowerCase() === 'placeholder' || cleanImg === '') {
        const lowerName = name.toLowerCase();
        if (lowerName.includes('wheelbarrow')) {
            return 'https://images.unsplash.com/photo-1599839620526-c5d17a6a6200?auto=format&fit=crop&w=300&q=80';
        } else if (lowerName.includes('timber') || lowerName.includes('pine') || lowerName.includes('batten') || lowerName.includes('wood')) {
            return 'https://images.unsplash.com/photo-1589939705384-5185137a7f0f?auto=format&fit=crop&w=300&q=80';
        } else if (lowerName.includes('drill') || lowerName.includes('driver') || lowerName.includes('tool') || lowerName.includes('saw') || lowerName.includes('makita') || lowerName.includes('dewalt')) {
            return 'https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=300&q=80';
        } else if (lowerName.includes('boot') || lowerName.includes('safety') || lowerName.includes('glove') || lowerName.includes('vest') || lowerName.includes('helmet')) {
            return 'https://images.unsplash.com/photo-1582967788606-a171c1080cb0?auto=format&fit=crop&w=300&q=80';
        } else if (lowerName.includes('bolt') || lowerName.includes('screw') || lowerName.includes('nail') || lowerName.includes('nut') || lowerName.includes('fastener')) {
            return 'https://images.unsplash.com/photo-1530124560072-aae8d56b0efe?auto=format&fit=crop&w=300&q=80';
        }
        return 'https://images.unsplash.com/photo-1581094288338-2314dddb7ecc?auto=format&fit=crop&w=300&q=80';
    }
    return cleanImg;
}

function formatSectionBody(body, title = '') {
    let content = body.trim();

    // 0. Handle Product Cards (Section 2)
    if (title.toUpperCase().includes('MATCHED PRODUCTS')) {
        const products = [];
        const productBlocks = content.split(/PRODUCT_START|PRODUCT_END/).filter(b => b.trim().length > 10);

        productBlocks.forEach(block => {
            const lines = block.trim().split('\n');
            const p = {};
            lines.forEach(l => {
                const parts = l.split(':');
                if (parts.length >= 2) {
                    const key = parts[0].trim().toLowerCase();
                    const val = parts.slice(1).join(':').trim();
                    p[key] = val;
                }
            });
            if (p.name) products.push(p);
        });

        if (products.length > 0) {
            return `
                <div class="product-grid">
                    ${products.map(p => {
                        const robustImg = getRobustProductImage(p.image, p.name);
                        const robustLink = getRobustSourceLink(p.source, p.name, p.supplier);
                        return `
                            <div class="product-card">
                                <div class="product-image">
                                    <img src="${robustImg}" alt="${p.name}" onerror="this.onerror=null; this.parentElement.innerHTML='<svg width=\\'48\\' height=\\'48\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'#cbd5e1\\' stroke-width=\\'1\\'><rect x=\\'3\\' y=\\'3\\' width=\\'18\\' height=\\'18\\' rx=\\'2\\'/><circle cx=\\'8.5\\' cy=\\'8.5\\' r=\\'1.5\\'/><path d=\\'M21 15l-5-5L5 21\\'/></svg>';">
                                </div>
                                <div class="product-details">
                                    <div class="product-name">${p.name}</div>
                                    <div class="product-meta">
                                        <span class="meta-tag">${p.supplier || 'Unknown Supplier'}</span>
                                        <span class="meta-tag">${p.brand || 'No Brand'}</span>
                                    </div>
                                    <div class="product-price">${p.price || 'Contact for Quote'}</div>
                                    <div class="product-specs">${p.specs || 'No specific technical details provided.'}</div>
                                    <div class="product-actions">
                                        <a href="${robustLink}" target="_blank" class="btn-view-source">View on Site</a>
                                        <button class="btn-card-action" onclick="openRFQFromCard(this)">Create RFQ</button>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }
    }

    // 1. Detect and Parse Markdown Tables
    if (content.includes('|') && content.includes('---')) {
        const lines = content.split('\n');
        let tableData = [];
        let otherTextBefore = [];
        let otherTextAfter = [];
        let inTable = false;
        let tableStarted = false;

        lines.forEach(line => {
            if (line.trim().startsWith('|') || (line.includes('|') && line.includes('-'))) {
                if (line.includes('---')) {
                    inTable = true;
                    tableStarted = true;
                    return;
                }
                const cells = line.split('|').map(c => c.trim()).filter((c, i, a) => {
                    if (i === 0 && c === '') return false;
                    if (i === a.length - 1 && c === '') return false;
                    return true;
                });
                if (cells.length > 0) {
                    tableData.push(cells);
                    inTable = true;
                    tableStarted = true;
                }
            } else {
                if (!tableStarted) otherTextBefore.push(line);
                else otherTextAfter.push(line);
                inTable = false;
            }
        });

        if (tableData.length > 0) {
            let tableHtml = '<div class="table-responsive"><table class="procurement-table"><thead><tr>';
            // Header (first row)
            tableData[0].forEach(cell => {
                tableHtml += `<th>${cell}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';

            // Body (rest of the rows)
            for (let i = 1; i < tableData.length; i++) {
                tableHtml += '<tr>';
                tableData[i].forEach(cell => {
                    tableHtml += `<td>${cell}</td>`;
                });
                tableHtml += '</tr>';
            }
            tableHtml += '</tbody></table></div>';

            return (otherTextBefore.join('<br>') + '<br>' + tableHtml + '<br>' + otherTextAfter.join('<br>')).replace(/(<br>){3,}/g, '<br><br>');
        }
    }

    // 2. Fallback for lists and text
    return content
        .replace(/\n/g, '<br>')
        .replace(/•/g, '&bull;')
        .replace(/^-\s(.*?)<br>/gm, '• $1<br>') // Basic bullets
        .replace(/\[(.*?)\]/g, '<strong style="color:var(--primary-orange)">$1</strong>'); // Highlight actions
}

function handleProcAction(action) {
    console.log(`[Procurement] Action triggered: ${action}`);

    if (action === 'rfq') {
        extractAndOpenRFQ();
    } else if (action === 'save') {
        saveToProcList();
    } else if (action === 'compare') {
        handleCompareAction();
    } else if (action === 'email') {
        draftEmailToSuppliers();
    } else if (action === 'pdf') {
        exportToPDF();
    }
}

function openRFQFromCard(btn) {
    const card = btn.closest('.product-card');
    if (!card) return openRFQModal();

    const name = card.querySelector('.product-name').innerText;
    const metaTags = card.querySelectorAll('.meta-tag');
    const supplier = metaTags[0] ? metaTags[0].innerText : '';
    const brand = metaTags[1] ? metaTags[1].innerText : '';
    const specs = card.querySelector('.product-specs').innerText;

    document.getElementById('rfqItemName').value = name;
    document.getElementById('rfqSupplier').value = supplier;
    document.getElementById('rfqBrand').value = brand;
    document.getElementById('rfqSpecs').value = specs;

    openRFQModal();
}

function extractAndOpenRFQ() {
    // Find the last procurement message and try to extract the first product card data
    const lastMsg = document.querySelector('.message.assistant.procurement:last-of-type');
    if (!lastMsg) return openRFQModal();

    const firstCard = lastMsg.querySelector('.product-card');
    if (firstCard) {
        const btn = firstCard.querySelector('.btn-card-action');
        if (btn) return openRFQFromCard(btn);
    }

    openRFQModal();
}

function openRFQModal() {
    document.getElementById('rfqModal').style.display = 'flex';
    // Set default date to 1 week from now
    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    document.getElementById('rfqDate').value = nextWeek.toISOString().split('T')[0];
}

function closeRFQModal() {
    document.getElementById('rfqModal').style.display = 'none';
}

async function submitRFQ(event, status = 'SENT') {
    if (event) event.preventDefault();

    const payload = {
        item_name: document.getElementById('rfqItemName').value,
        supplier: document.getElementById('rfqSupplier').value,
        brand: document.getElementById('rfqBrand').value,
        specs: document.getElementById('rfqSpecs').value,
        quantity: document.getElementById('rfqQuantity').value,
        required_date: document.getElementById('rfqDate').value,
        status: status
    };

    try {
        if (typeof showLoading === 'function') showLoading(status === 'SENT' ? 'Formalizing & Sending RFQ...' : 'Saving RFQ Draft...');
        const response = await window.api.createRFQ(payload);
        if (typeof hideLoading === 'function') hideLoading();

        if (response.success) {
            if (typeof showToast === 'function') showToast(status === 'SENT' ? `RFQ ${response.rfq_number} Sent Successfully!` : 'RFQ Saved as Draft', 'success');
            closeRFQModal();

            if (status === 'SENT') {
                if (typeof appendMessage === 'function') {
                    appendMessage('assistant', `✅ **RFQ Processed**: I have generated and sent **${response.rfq_number}** to ${payload.supplier}. Status updated to "RFQ Sent".`);
                }
            }
        }
    } catch (err) {
        if (typeof hideLoading === 'function') hideLoading();
        if (typeof showToast === 'function') showToast("Error processing RFQ: " + err.message, "error");
    }
}

async function handleCompareAction() {
    // 1. Find the last procurement message
    const lastMsg = document.querySelector('.message.assistant.procurement:last-of-type');
    if (!lastMsg) {
        alert("No comparison data found in the last message.");
        return;
    }

    // 2. Extract Data from the message sections
    const text = lastMsg.innerText;
    const sections = parseProcurementSections(text);
    const tableSection = sections.find(s => s.title.includes('COMPARISON'));
    const recommendationSection = sections.find(s => s.title.includes('RECOMMENDATION'));

    if (!tableSection || !tableSection.body.includes('|')) {
        alert("I couldn't find a structured table to compare. Please try asking to 'compare' specific items.");
        return;
    }

    // 3. Save comparison to DB so it can be viewed on the comparison page
    try {
        const parsedData = extractTableData(tableSection.body);
        const payload = {
            title: "AI Generated Comparison",
            category: "Procurement",
            products: parsedData.products,
            table_data: parsedData.attributes,
            recommendation: recommendationSection ? recommendationSection.body.trim() : "No specific recommendation provided.",
            confidence_level: "High",
            missing_info: ["Full compliance docs", "Trade pricing verification"]
        };

        const response = await window.api.saveComparison(payload);
        if (response.success) {
            // 4. Redirect to comparison page with the new ID
            window.location.href = `comparison.html?id=${response.id}`;
        }
    } catch (err) {
        console.error("Comparison Error:", err);
        alert("Failed to generate comparison: " + err.message);
    }
}

function extractTableData(markdownTable) {
    const lines = markdownTable.trim().split('\n').filter(l => l.includes('|'));
    if (lines.length < 3) return { products: [], attributes: {} };

    // Extract Headers (Products/Attributes)
    const headers = lines[0].split('|').map(h => h.trim()).filter(h => h !== '');
    // Assume first column is attribute name, others are products
    const products = headers.slice(1).map((p, i) => ({ id: i + 1, name: p, supplier_name: p }));

    const attributes = {};
    // Skip header and separator lines
    for (let i = 2; i < lines.length; i++) {
        const cells = lines[i].split('|').map(c => c.trim()).filter(c => c !== '');
        if (cells.length > 1) {
            const attrName = cells[0];
            attributes[attrName] = {};
            cells.slice(1).forEach((val, idx) => {
                attributes[attrName][idx + 1] = val;
            });
        }
    }
    return { products, attributes };
}

async function saveToProcList() {
    const lastMsg = document.querySelector('.message.assistant.procurement:last-of-type');
    if (!lastMsg) {
        if (typeof showToast === 'function') showToast("No procurement data found to save.", "error");
        return;
    }

    try {
        const text = lastMsg.innerText;
        const sections = parseProcurementSections(text);

        // Extract product card data if available
        const firstCard = lastMsg.querySelector('.product-card');
        let itemName = "Procurement Research";
        let supplier = "";
        let specs = "";
        let sourceUrl = "";

        if (firstCard) {
            itemName = firstCard.querySelector('.product-name')?.innerText || itemName;
            const metaTags = firstCard.querySelectorAll('.meta-tag');
            supplier = metaTags[0]?.innerText || "";
            specs = firstCard.querySelector('.product-specs')?.innerText || "";
            sourceUrl = firstCard.querySelector('.btn-view-source')?.href || "";
        } else {
            // Fallback: use summary section text
            const summarySection = sections.find(s => s.title.toUpperCase().includes('SUMMARY'));
            itemName = summarySection?.body?.substring(0, 80) || itemName;
            specs = sections.find(s => s.title.toUpperCase().includes('RECOMMENDATION'))?.body?.substring(0, 200) || "";
        }

        const payload = {
            item_name: itemName,
            category: "General Procurement",
            supplier: supplier,
            technical_notes: specs,
            source_url: sourceUrl,
            ai_recommendation: sections.find(s => s.title.toUpperCase().includes('RECOMMENDATION'))?.body?.substring(0, 500) || "",
            status: "RESEARCHING"
        };

        const response = await window.api.saveToProcurementList(payload);

        if (response.success) {
            if (typeof showToast === 'function') showToast("✅ Product saved to Procurement List (Status: Researching)", "success");
        } else {
            if (typeof showToast === 'function') showToast("Failed to save: " + (response.detail || "Unknown error"), "error");
        }
    } catch (err) {
        console.error("Save Error:", err);
        if (typeof showToast === 'function') showToast("Failed to save: " + err.message, "error");
    }
}

async function draftEmailToSuppliers() {
    const lastMsg = document.querySelector('.message.assistant.procurement:last-of-type');
    if (!lastMsg) {
        if (typeof showToast === 'function') showToast("No procurement context found for email drafting.", "error");
        return;
    }

    try {
        const text = lastMsg.innerText;
        const sections = parseProcurementSections(text);

        // Extract product info
        const firstCard = lastMsg.querySelector('.product-card');
        let productName = "the requested item";
        let supplierName = "the Supplier";
        let specs = "";
        let sourceUrl = "";

        if (firstCard) {
            productName = firstCard.querySelector('.product-name')?.innerText || productName;
            const metaTags = firstCard.querySelectorAll('.meta-tag');
            supplierName = metaTags[0]?.innerText || supplierName;
            specs = firstCard.querySelector('.product-specs')?.innerText || "";
            sourceUrl = firstCard.querySelector('.btn-view-source')?.href || "";
        } else {
            const summarySection = sections.find(s => s.title.toUpperCase().includes('SUMMARY'));
            productName = summarySection?.body?.substring(0, 60) || productName;
            const recSection = sections.find(s => s.title.toUpperCase().includes('RECOMMENDATION'));
            specs = recSection?.body?.substring(0, 200) || "";
        }

        // Build professional email
        const today = new Date().toLocaleDateString('en-AU', { day: '2-digit', month: 'long', year: 'numeric' });
        const emailBody = `Dear ${supplierName} Sales Team,

I hope this message finds you well.

We are a construction and engineering firm currently evaluating suppliers for an upcoming project. I am writing to request pricing and availability information for the following item:

PRODUCT DETAILS
Product: ${productName}
Technical Specifications: ${specs || 'As per industry standard specifications'}
${sourceUrl ? 'Reference: ' + sourceUrl : ''}

REQUEST FOR QUOTE
We would appreciate it if you could provide the following:
- Unit price (ex-GST)
- Lead time / estimated delivery date
- Stock availability
- Minimum order quantity
- Warranty terms
- Applicable compliance certificates
- Trade account pricing (if available)

Please respond by [QUOTE DUE DATE] to allow us sufficient time for evaluation.

Should you require further information or a site visit, please do not hesitate to contact us.

Note: This is an inquiry only. No purchase order has been issued at this stage. All pricing is subject to internal approval before any commitment is made.

Kind regards,

[YOUR NAME]
[YOUR TITLE]
[COMPANY NAME]
[EMAIL] | [PHONE]`;

        // Show in modal
        document.getElementById('draftEmailSubject').value = `Procurement Inquiry - ${productName} - ${today}`;
        document.getElementById('draftEmailTo').value = ``;
        document.getElementById('draftEmailBody').value = emailBody;
        document.getElementById('emailDraftModal').style.display = 'flex';

    } catch (err) {
        console.error("Draft Email Error:", err);
        if (typeof showToast === 'function') showToast("Error generating email draft: " + err.message, "error");
    }
}

function closeEmailDraftModal() {
    document.getElementById('emailDraftModal').style.display = 'none';
}

async function sendDraftEmail() {
    const to = document.getElementById('draftEmailTo').value.trim();
    const subject = document.getElementById('draftEmailSubject').value.trim();
    const body = document.getElementById('draftEmailBody').value.trim();

    if (!to) {
        if (typeof showToast === 'function') showToast("Please enter a supplier email address.", "error");
        return;
    }

    try {
        const btn = document.getElementById('btnSendDraftEmail');
        btn.disabled = true;
        btn.innerText = "Sending...";

        // Save as draft via API
        const response = await window.api.saveDraft ?
            await window.api.saveDraft({ to, subject, body, source: 'procurement_assistant' }) :
            { success: true }; // Fallback if endpoint not yet wired

        closeEmailDraftModal();
        if (typeof showToast === 'function') showToast("Email draft saved. Navigating to Drafts page...", "success");
        setTimeout(() => window.location.href = 'drafts.html', 1500);

    } catch (err) {
        if (typeof showToast === 'function') showToast("Error: " + err.message, "error");
    } finally {
        const btn = document.getElementById('btnSendDraftEmail');
        if (btn) { btn.disabled = false; btn.innerText = "Save & Go to Drafts"; }
    }
}

function exportToPDF() {
    const lastMsg = document.querySelector('.message.assistant.procurement:last-of-type');
    if (!lastMsg) {
        if (typeof showToast === 'function') showToast("No data available to export.", "error");
        return;
    }

    // Build a branded export document
    const sections = parseProcurementSections(lastMsg.innerText);
    const today = new Date().toLocaleDateString('en-AU', { day: '2-digit', month: 'long', year: 'numeric' });

    // Collect product cards HTML
    let productCardsHtml = '';
    lastMsg.querySelectorAll('.product-card').forEach(card => {
        const name = card.querySelector('.product-name')?.innerText || '';
        const tags = card.querySelectorAll('.meta-tag');
        const supplier = tags[0]?.innerText || '';
        const brand = tags[1]?.innerText || '';
        const price = card.querySelector('.product-price')?.innerText || 'Contact for Quote';
        const specs = card.querySelector('.product-specs')?.innerText || '';
        const link = card.querySelector('.btn-view-source')?.href || '#';

        productCardsHtml += `
            <div style="border:1px solid #e2e8f0; border-radius:10px; padding:16px; margin-bottom:12px; break-inside:avoid;">
                <div style="font-weight:700; font-size:1rem; color:#1e293b; margin-bottom:6px;">${name}</div>
                <div style="display:flex; gap:8px; margin-bottom:8px; flex-wrap:wrap;">
                    <span style="background:#FFF4F0; color:#FF5C35; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600;">${supplier}</span>
                    <span style="background:#f1f5f9; color:#475569; padding:3px 10px; border-radius:20px; font-size:0.75rem;">${brand}</span>
                </div>
                <div style="color:#FF5C35; font-weight:700; font-size:1rem; margin-bottom:6px;">${price}</div>
                <div style="font-size:0.82rem; color:#64748b; line-height:1.5;">${specs}</div>
                <div style="margin-top:8px; font-size:0.75rem; color:#94a3b8;">Source: <a href="${link}">${link}</a></div>
            </div>`;
    });

    // Collect comparison table HTML (if present)
    let tableHtml = lastMsg.querySelector('.procurement-table')?.outerHTML || '';

    // Collect recommendation text
    const recSection = sections.find(s => s.title.toUpperCase().includes('RECOMMENDATION'));
    const recText = recSection?.body?.trim() || '';

    // Build the full printable document
    const printContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Procurement Report - ${today}</title>
            <style>
                * { margin:0; padding:0; box-sizing:border-box; }
                body { font-family: 'Segoe UI', Arial, sans-serif; color:#1e293b; background:#fff; padding:40px; }
                .header { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:3px solid #FF5C35; padding-bottom:20px; margin-bottom:30px; }
                .logo-area h1 { font-size:1.8rem; color:#FF5C35; font-weight:800; letter-spacing:-0.5px; }
                .logo-area p { color:#64748b; font-size:0.85rem; margin-top:4px; }
                .meta-info { text-align:right; font-size:0.8rem; color:#64748b; }
                .meta-info strong { color:#1e293b; }
                .section-title { font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#FF5C35; margin:24px 0 12px; padding-bottom:6px; border-bottom:1px solid #fee2e2; }
                table { width:100%; border-collapse:collapse; font-size:0.82rem; margin-top:8px; }
                th { background:#f8fafc; padding:10px 12px; text-align:left; font-size:0.72rem; text-transform:uppercase; color:#64748b; border-bottom:2px solid #e2e8f0; }
                td { padding:10px 12px; border-bottom:1px solid #f1f5f9; }
                .recommendation-box { background:#FFF4F0; border-left:4px solid #FF5C35; border-radius:6px; padding:16px; margin-top:8px; font-size:0.875rem; line-height:1.6; }
                .disclaimer { margin-top:40px; padding:12px 16px; background:#f8fafc; border-radius:6px; font-size:0.72rem; color:#94a3b8; line-height:1.5; }
                .footer { margin-top:20px; text-align:center; font-size:0.72rem; color:#cbd5e1; padding-top:16px; border-top:1px solid #f1f5f9; }
                @media print { body { padding:20px; } }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo-area">
                    <h1>🛡 RFI Platform</h1>
                    <p>Procurement Intelligence Report</p>
                </div>
                <div class="meta-info">
                    <div><strong>Date:</strong> ${today}</div>
                    <div><strong>Generated By:</strong> AI Procurement Assistant</div>
                    <div><strong>Status:</strong> Pending Human Approval</div>
                </div>
            </div>

            ${productCardsHtml ? `<div class="section-title">Matched Products</div>${productCardsHtml}` : ''}
            ${tableHtml ? `<div class="section-title">Supplier Comparison Table</div>${tableHtml}` : ''}
            ${recText ? `<div class="section-title">Best Recommendation</div><div class="recommendation-box">${recText.replace(/\n/g, '<br>')}</div>` : ''}

            <div class="disclaimer">
                ⚠️ DISCLAIMER: Supplier catalogue results are used for demonstration purposes only. Product details, pricing, availability, delivery terms, and compliance information must be confirmed directly with the supplier before purchase. This platform does not claim official partnership or direct purchasing integration with any supplier.
            </div>
            <div class="footer">Generated by RFI Procurement Intelligence Platform · ${today}</div>
        </body>
        </html>`;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => printWindow.print(), 500);
}
