/**
 * ifrit 平台通用 UI 逻辑
 */
const IfritUI = (function() {
    function appendLog(container, line) {
        if (container.querySelector('.text-muted')) {
            container.innerHTML = '';
        }
        const div = document.createElement('div');
        div.className = 'log-line';
        if (line.includes('[IFRIT]')) div.classList.add('ifrit');
        if (/error|fail|ERROR/i.test(line)) div.classList.add('error');
        if (/PASS|success|成功/i.test(line)) div.classList.add('success');
        div.textContent = line;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    function streamLogs(processId, container, onComplete) {
        const es = new EventSource('/api/process/' + processId + '/stream');
        es.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'log') appendLog(container, data.line);
                if (data.type === 'status' && onComplete) onComplete(data);
                if (data.type === 'done') es.close();
            } catch (e) { /* ignore */ }
        };
        es.onerror = function() { es.close(); };
        return es;
    }

    function showToast(message, type) {
        const el = document.createElement('div');
        el.className = 'alert alert-' + (type === 'success' ? 'success' : 'danger');
        el.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;min-width:200px;';
        el.textContent = message;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 3000);
    }

    function showLatestReport(linkEl, boxEl) {
        return fetch('/api/overview')
            .then(r => r.json())
            .then(data => {
                const runId = data.stats && data.stats.latest_run;
                const runs = (data.stats && data.stats.latest_runs) || [];
                const latest = runs.find(r => r.run_id === runId) || runs[0];
                if (latest && linkEl && boxEl) {
                    const url = latest.has_html
                        ? (latest.html_url || ('/reports/view/' + latest.run_id + '/'))
                        : '/reports/view/' + latest.run_id + '/';
                    linkEl.href = url;
                    linkEl.textContent = latest.has_html ? '打开 HTML 报告' : '查看 Run（可生成报告）';
                    boxEl.style.display = 'block';
                }
                return latest;
            })
            .catch(() => null);
    }

    function initMobileSidebar() {
        const sidebar = document.getElementById('appSidebar');
        const backdrop = document.getElementById('sidebarBackdrop');
        const toggle = document.getElementById('sidebarToggle');
        if (!sidebar || !toggle) return;

        function close() {
            sidebar.classList.remove('open');
            backdrop?.classList.remove('show');
        }
        function open() {
            sidebar.classList.add('open');
            backdrop?.classList.add('show');
        }

        toggle.addEventListener('click', () => {
            sidebar.classList.contains('open') ? close() : open();
        });
        backdrop?.addEventListener('click', close);
        sidebar.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 992) close();
            });
        });
    }

    document.addEventListener('DOMContentLoaded', initMobileSidebar);

    async function shouldEnableRagDefault() {
        const [statsRes, settingsRes] = await Promise.all([
            fetch('/api/knowledge/stats').then(r => r.json()),
            fetch('/api/settings').then(r => r.json()),
        ]);
        const chunks = statsRes.stats?.chunks || 0;
        const prefs = settingsRes.ui_prefs || {};
        return chunks > 0 && prefs.rag_default_on !== false;
    }

    async function applyRagDefaultCheckbox(checkboxId) {
        const el = document.getElementById(checkboxId);
        if (!el) return;
        try {
            el.checked = await shouldEnableRagDefault();
        } catch (e) { /* ignore */ }
    }

    async function ingestCaseToRag(relativePath) {
        if (!relativePath) return null;
        const res = await fetch('/api/settings/rag/ingest-case', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: relativePath }),
        });
        return res.json();
    }

    return {
        appendLog, streamLogs, showToast, showLatestReport,
        shouldEnableRagDefault, applyRagDefaultCheckbox, ingestCaseToRag,
    };
})();
