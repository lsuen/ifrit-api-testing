/**
 * ifrit 控制台：CLI / Chat 单行 + SSE 流式日志
 */
(function() {
    let policy = {};
    let warnConfirmed = false;

    function mode() {
        return document.querySelector('input[name="consoleMode"]:checked').value;
    }

    function logEl() { return document.getElementById('consoleLog'); }

    function updateHint() {
        const m = mode();
        document.getElementById('hintBox').innerHTML = m === 'cli'
            ? 'CLI：参数以 <code>--</code> 开头。例：<code>--file fixtures/smoke/csv/api_test_smoke.csv --generate-report</code>'
            : 'Chat：子命令 doc / url / endpoint / generate 等，等效 <code>main.py --chat</code>';
    }

    function renderRecipes() {
        const wrap = document.getElementById('quickRecipes');
        const items = policy.quick_recipes || [];
        if (!items.length) { wrap.innerHTML = ''; return; }
        wrap.innerHTML = '<p class="fw-semibold mb-1">快捷：</p>' + items.map(r =>
            `<button type="button" class="btn btn-link btn-sm p-0 d-block recipe-btn" data-mode="${r.mode}" data-line="${r.line.replace(/"/g, '&quot;')}">${r.label}</button>`
        ).join('');
        wrap.querySelectorAll('.recipe-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelector(`input[name="consoleMode"][value="${btn.dataset.mode}"]`).checked = true;
                updateHint();
                document.getElementById('consoleInput').value = btn.dataset.line;
            });
        });
    }

    function parseAssistFromLog(container) {
        const lines = [...container.querySelectorAll('.log-line')].map(el => el.textContent);
        for (const line of lines.reverse()) {
            const idx = line.indexOf('[IFRIT] TEST_ASSIST_JSON=');
            if (idx >= 0) {
                try { return JSON.parse(line.slice(idx + '[IFRIT] TEST_ASSIST_JSON='.length)); } catch (e) {}
            }
        }
        return null;
    }

    async function loadPolicy() {
        const res = await axios.get('/api/console/policy');
        policy = res.data.policy || {};
        renderRecipes();
        const suggest = document.getElementById('consoleSuggest');
        const opts = (policy.quick_recipes || []).map(r => `<option value="${r.line}">`);
        suggest.innerHTML = opts.join('');
    }

    async function runHelp() {
        IfritUI.appendLog(logEl(), '[IFRIT] 加载 help...');
        const res = await axios.post('/api/console/help', { mode: mode() });
        IfritUI.streamLogs(res.data.process_id, logEl());
    }

    async function runExec() {
        const line = document.getElementById('consoleInput').value.trim();
        if (!line) return alert('请输入命令');
        warnConfirmed = false;
        const check = await axios.post('/api/console/validate', { mode: mode(), line });
        if (!check.data.ok) return alert(check.data.message || '命令被拒绝');
        if (check.data.level === 'warn' && !confirm(check.data.message + '\n\n仍要执行？')) return;

        document.getElementById('execBtn').disabled = true;
        try {
            const res = await axios.post('/api/console/exec', { mode: mode(), line });
            IfritUI.streamLogs(res.data.process_id, logEl(), () => {
                document.getElementById('execBtn').disabled = false;
            });
        } catch (e) {
            alert(e.response?.data?.error || e.message);
            document.getElementById('execBtn').disabled = false;
        }
    }

    document.querySelectorAll('input[name="consoleMode"]').forEach(r => {
        r.addEventListener('change', updateHint);
    });
    document.getElementById('helpBtn').addEventListener('click', () => runHelp().catch(e => alert(e.message)));
    document.getElementById('execBtn').addEventListener('click', runExec);
    document.getElementById('consoleInput').addEventListener('keydown', e => {
        if (e.key === 'Enter') runExec();
        if (e.key === 'Tab') {
            const input = e.target;
            if (!input.value && policy.quick_recipes && policy.quick_recipes[0]) {
                e.preventDefault();
                input.value = policy.quick_recipes[0].line;
            }
        }
    });

    updateHint();
    loadPolicy().catch(() => {});
})();
