/**
 * RFQ Progress Stepper Logic — PRD v2.1
 * Can be attached to any dashboard or rfq page to show workflow state.
 */

async function renderRFQStepperByTopic(topicId, containerElementId) {
    const container = document.getElementById(containerElementId);
    if (!container) return;

    container.innerHTML = '<p style="color:var(--text-muted); font-size: 0.8rem;">Loading progress...</p>';

    try {
        const listRes = await fetch(`/api/rfq-workflows`);
        const listData = await listRes.json();
        const workflows = listData.data || [];
        const w = workflows.find(x => x.topic_id == topicId);

        if (!w) {
            container.innerHTML = '<p style="color:var(--text-muted); font-size: 0.8rem;">No active workflow tracking for this project.</p>';
            return;
        }

        const res = await fetch(`/api/rfq-workflows/${w.id}`);
        const data = await res.json();

        if (!data.success) {
            container.innerHTML = `<p style="color:red; font-size:0.8rem;">Failed to load workflow state</p>`;
            return;
        }

        const steps = data.data.steps_completed;
        const status = data.data.status; 

        // Define steps sequence
        const flow = [
            { key: 'email_received', label: '1. Intake' },
            { key: 'topic_assigned', label: '2. Resolved' },
            { key: 'market_research', label: '3. Research' },
            { key: 'drafts_ready', label: '4. Drafts' },
            { key: 'sent_to_vendors', label: '5. Sent' }
        ];

        let html = `<div style="display: flex; gap: 10px; align-items: center; margin-top: 10px;">`;
        
        flow.forEach((s, idx) => {
            const isDone = steps[s.key] === true;
            let bgColor = isDone ? '#dcfce7' : '#f1f5f9';
            let textColor = isDone ? '#15803d' : '#94a3b8';
            let icon = isDone ? '✓' : '•';
            
            // Highlight current in-progress state if not done but previous is done
            if (!isDone && (idx === 0 || steps[flow[idx-1].key] === true)) {
                if (status === 'triage' && s.key === 'topic_assigned') {
                    bgColor = '#fee2e2'; // Red for triage required
                    textColor = '#991b1b';
                    icon = '⚠️';
                } else {
                    bgColor = '#dbeafe'; // Blue for active
                    textColor = '#1d4ed8';
                    icon = '⏳';
                }
            }

            html += `
                <div style="flex: 1; text-align: center; padding: 6px; border-radius: 6px; background: ${bgColor}; color: ${textColor}; font-size: 0.7rem; font-weight: 600;">
                    ${icon} ${s.label}
                </div>
            `;
        });

        html += `</div>`;
        container.innerHTML = html;

    } catch (e) {
        console.error('Error rendering stepper:', e);
        container.innerHTML = `<p style="color:red; font-size:0.8rem;">Error loading progress.</p>`;
    }
}

