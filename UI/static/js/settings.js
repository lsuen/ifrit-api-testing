/**
 * 设置页
 */
(function() {
    async function loadSettings() {
        const res = await axios.get('/api/settings');
        const data = res.data;
        const ai = data.ai || {};
        const form = document.getElementById('aiForm');
        if (form) {
            form.base_url.value = ai.base_url || '';
            form.model.value = ai.model || '';
            form.timeout.value = ai.timeout || '120';
            form.openai_base_url_override.value = data.env_keys?.openai_base_url_override || '';
            form.openai_model_override.value = data.env_keys?.openai_model_override || '';
            document.getElementById('keyHint').textContent =
                data.env_keys?.openai_api_key_set
                    ? '当前 Key: ' + (data.env_keys.openai_api_key_hint || '已设置')
                    : '未检测到 Key（本地 LLM 可留空）';
        }
        renderEnvList(data.env_options || []);
        const prefs = data.ui_prefs || {};
        document.getElementById('ragDefaultOn').checked = !!prefs.rag_default_on;
        document.getElementById('autoIngestRag').checked = prefs.auto_ingest_rag !== false;
        const auth = data.auth || {};
        document.getElementById('authEnabled').checked = auth.enabled === 'true';
        if auth.login_path && auth.login_path !== '获取不到') {
            document.getElementById('authForm').login_path.value = auth.login_path;
        }
        if (auth.login_method) document.getElementById('authForm').login_method.value = auth.login_method;
        if (auth.login_body) document.getElementById('authForm').login_body.value = auth.login_body;
    }

    function renderEnvList(options) {
        const wrap = document.getElementById('envListWrap');
        if (!options.length) {
            wrap.innerHTML = '<p class="text-muted p-4 mb-0">暂无环境，请在上方添加</p>';
            return;
        }
        let html = '<table class="table-platform mb-0"><thead><tr><th>名称</th><th>Base URL</th></tr></thead><tbody>';
        options.forEach(o => {
            html += `<tr><td><code>${o.name}</code></td><td>${o.base_url}</td></tr>`;
        });
        html += '</tbody></table>';
        wrap.innerHTML = html;
    }

    async function runHealth() {
        const ping = document.getElementById('pingLlmCheck').checked;
        const res = await axios.post('/api/settings/health', { ping_llm: ping });
        const data = res.data;
        document.getElementById('healthSummary').textContent = data.summary || '';
        document.getElementById('healthSummary').className = data.ready ? 'mb-3 text-success' : 'mb-3 text-warning';
        const list = document.getElementById('healthList');
        list.innerHTML = (data.checks || []).map(c =>
            `<li class="list-group-item d-flex justify-content-between align-items-center">
                <span>${c.name}</span>
                <span><span class="badge ${c.ok ? 'bg-success' : (c.level === 'warn' ? 'bg-warning text-dark' : 'bg-danger')}">${c.ok ? 'OK' : '注意'}</span>
                <small class="text-muted ms-2">${c.message || ''}</small></span>
            </li>`
        ).join('');
    }

    document.getElementById('runHealthBtn').addEventListener('click', () => runHealth().catch(e => alert(e.message)));
    runHealth().catch(() => {});

    document.getElementById('aiForm').addEventListener('submit', async e => {
        e.preventDefault();
        const f = e.target;
        await axios.post('/api/settings/ai', {
            base_url: f.base_url.value,
            model: f.model.value,
            timeout: f.timeout.value,
            openai_api_key: f.openai_api_key.value,
            openai_base_url_override: f.openai_base_url_override.value,
            openai_model_override: f.openai_model_override.value,
        });
        IfritUI.showToast('AI 配置已保存', 'success');
        f.openai_api_key.value = '';
        loadSettings();
        runHealth();
    });

    document.getElementById('envForm').addEventListener('submit', async e => {
        e.preventDefault();
        const f = e.target;
        await axios.post('/api/settings/env', {
            name: f.name.value.trim(),
            base_url: f.base_url.value.trim(),
            timeout: f.timeout.value,
        });
        IfritUI.showToast('环境已保存', 'success');
        loadSettings();
        runHealth();
    });

    document.getElementById('authForm').addEventListener('submit', async e => {
        e.preventDefault();
        const f = e.target;
        await axios.post('/api/settings/auth', {
            enabled: f.enabled.checked,
            login_path: f.login_path.value,
            login_method: f.login_method.value,
            login_body: f.login_body.value,
        });
        IfritUI.showToast('鉴权已保存', 'success');
        runHealth();
    });

    document.getElementById('prefsForm').addEventListener('submit', async e => {
        e.preventDefault();
        const f = e.target;
        await axios.post('/api/settings/prefs', {
            rag_default_on: f.rag_default_on.checked,
            auto_ingest_rag: f.auto_ingest_rag.checked,
        });
        IfritUI.showToast('偏好已保存', 'success');
    });

    loadSettings().catch(() => {});
})();
