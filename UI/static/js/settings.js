/**
 * 设置页
 */
(function() {
    function renderEffectiveBanner(effective) {
        const banner = document.getElementById('effectiveAiBanner');
        const text = document.getElementById('effectiveAiText');
        if (!banner || !text || !effective) return;
        banner.classList.remove('d-none');
        const keyHint = effective.api_key_set ? ` · Key ${effective.api_key_hint || '已设置'}` : ' · Key 未设置';
        text.textContent = `${effective.base_url || '-'} · 模型 ${effective.model || '-'}${keyHint}`;
    }

    async function loadSettings() {
        const res = await axios.get('/api/settings');
        const data = res.data;
        const ai = data.ai || {};
        const effective = data.effective_ai || {};
        renderEffectiveBanner(effective);
        const form = document.getElementById('aiForm');
        if (form) {
            form.base_url.value = ai.base_url || effective.base_url || '';
            form.model.value = ai.model || effective.model || '';
            form.timeout.value = ai.timeout || effective.timeout || '120';
            document.getElementById('keyHint').textContent =
                data.env_keys?.openai_api_key_set
                    ? '当前 Key: ' + (data.env_keys.openai_api_key_hint || '已设置')
                    : '未检测到 Key（本地 LLM 可留空；公网网关必填）';
        }
        renderEnvList(data.env_options || []);
        const prefs = data.ui_prefs || {};
        document.getElementById('ragDefaultOn').checked = !!prefs.rag_default_on;
        document.getElementById('autoIngestRag').checked = prefs.auto_ingest_rag !== false;
        const auth = data.auth || {};
        document.getElementById('authEnabled').checked = auth.enabled === 'true';
        const authForm = document.getElementById('authForm');
        if (auth.login_path && auth.login_path !== '获取不到') {
            authForm.login_path.value = auth.login_path;
        }
        if (auth.login_method) authForm.login_method.value = auth.login_method;
        if (auth.login_body) authForm.login_body.value = auth.login_body;
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

    async function testLlm() {
        const el = document.getElementById('llmTestResult');
        el.textContent = '测试中…';
        el.className = 'small text-muted ms-2';
        try {
            const res = await axios.post('/api/settings/health', { ping_llm: true });
            const llm = (res.data.checks || []).find(c => c.name === 'LLM 连通');
            if (llm && llm.ok) {
                el.textContent = '✓ ' + llm.message;
                el.className = 'small text-success ms-2';
            } else {
                el.textContent = '✗ ' + (llm?.message || '连通失败');
                el.className = 'small text-danger ms-2';
            }
        } catch (e) {
            el.textContent = '测试失败';
            el.className = 'small text-danger ms-2';
        }
    }

    document.getElementById('runHealthBtn').addEventListener('click', () => runHealth().catch(e => alert(e.message)));
    document.getElementById('testLlmBtn')?.addEventListener('click', () => testLlm());
    runHealth().catch(() => {});

    document.getElementById('aiForm').addEventListener('submit', async e => {
        e.preventDefault();
        const f = e.target;
        await axios.post('/api/settings/ai', {
            base_url: f.base_url.value,
            model: f.model.value,
            timeout: f.timeout.value,
            openai_api_key: f.openai_api_key.value,
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
