/**
 * Skill 管理：内置 / 发现 / 编辑器 / 流式日志
 */
const SkillsPage = (function() {
    let editor = null;
    let currentSkillId = '';
    let catalogItems = [];

    function log(msg) {
        IfritUI.appendLog(document.getElementById('skillsLog'), msg);
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text || '';
        return d.innerHTML;
    }

    async function streamTask(url, body) {
        const res = await axios.post(url, body || {});
        const logEl = document.getElementById('skillsLog');
        return new Promise((resolve, reject) => {
            IfritUI.streamLogs(res.data.process_id, logEl, status => {
                if (status.status === 'completed') resolve(status);
                else if (status.status === 'failed') reject(new Error('任务失败'));
            });
        });
    }

    function renderBuiltin(skills) {
        const wrap = document.getElementById('builtinWrap');
        if (!skills.length) {
            wrap.innerHTML = '<p class="text-muted">无内置技能</p>';
            return;
        }
        wrap.innerHTML = skills.map(s => `
            <div class="col-md-6 col-xl-4">
                <div class="card-panel h-100 p-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <code class="fw-bold">${escapeHtml(s.name)}</code>
                        <span class="badge bg-primary">builtin</span>
                    </div>
                    <p class="small text-muted mb-2">${escapeHtml(s.description || '')}</p>
                    <div class="small">${(s.actions || []).map(a =>
                        `<span class="badge bg-secondary me-1 mb-1">${escapeHtml(a.name)}</span>`
                    ).join('')}</div>
                </div>
            </div>`).join('');
    }

    function renderRepos(repos) {
        const wrap = document.getElementById('reposList');
        if (!repos.length) {
            wrap.innerHTML = '<p class="text-muted small mb-0">暂无仓库，将使用默认源</p>';
            return;
        }
        wrap.innerHTML = repos.map(r => `
            <div class="repo-item mb-2 p-2 border rounded">
                <div class="d-flex justify-content-between">
                    <strong class="small">${escapeHtml(r.label)}</strong>
                    <span class="badge ${r.cached ? 'bg-success' : 'bg-secondary'}">${r.cached ? '已缓存' : '未刷新'}</span>
                </div>
                <div class="small text-muted">${escapeHtml(r.host)} · ${escapeHtml(r.branch)} · ${r.skill_count || 0} 技能</div>
                ${r.last_error ? `<div class="small text-danger">${escapeHtml(r.last_error).slice(0, 120)}</div>` : ''}
                <div class="mt-2 d-flex gap-1">
                    <button class="btn btn-xs btn-outline-primary btn-sm refresh-repo-btn" data-id="${escapeHtml(r.id)}">刷新</button>
                    <button class="btn btn-xs btn-outline-danger btn-sm remove-repo-btn" data-id="${escapeHtml(r.id)}">删除</button>
                </div>
            </div>`).join('');
        wrap.querySelectorAll('.refresh-repo-btn').forEach(btn => {
            btn.addEventListener('click', () => refreshRepos(btn.dataset.id));
        });
        wrap.querySelectorAll('.remove-repo-btn').forEach(btn => {
            btn.addEventListener('click', () => removeRepo(btn.dataset.id));
        });
    }

    function renderCatalog(items) {
        catalogItems = items;
        const wrap = document.getElementById('catalogWrap');
        const datalist = document.getElementById('skillSuggestList');
        datalist.innerHTML = items.map(i => `<option value="${escapeHtml(i.name)}">`).join('');

        if (!items.length) {
            wrap.innerHTML = '<p class="text-muted p-4 mb-0">无技能，请先刷新仓库</p>';
            updateEditorSelect([]);
            return;
        }
        let html = '<table class="table-platform mb-0"><thead><tr><th>名称</th><th>仓库</th><th>状态</th><th>操作</th></tr></thead><tbody>';
        items.forEach(item => {
            const status = item.enabled ? '<span class="badge bg-success">已启用</span>'
                : item.staged ? '<span class="badge bg-info">已安装</span>' : '<span class="badge bg-secondary">可安装</span>';
            html += `<tr>
                <td><strong>${escapeHtml(item.name)}</strong><br><span class="small text-muted">${escapeHtml(item.description || '').slice(0, 80)}</span></td>
                <td class="small"><code>${escapeHtml(item.repo_label)}</code></td>
                <td>${status}</td>
                <td class="text-nowrap">
                    ${!item.staged ? `<button class="btn btn-sm btn-outline-primary install-btn" data-id="${escapeHtml(item.id)}">安装</button>` : ''}
                    ${item.staged && !item.enabled ? `<button class="btn btn-sm btn-outline-success enable-btn" data-id="${escapeHtml(item.id)}">启用</button>` : ''}
                    ${item.enabled ? `<button class="btn btn-sm btn-outline-warning disable-btn" data-id="${escapeHtml(item.id)}">禁用</button>` : ''}
                    ${item.staged ? `<button class="btn btn-sm btn-outline-secondary edit-btn" data-id="${escapeHtml(item.id)}">编辑</button>` : ''}
                </td>
            </tr>`;
        });
        html += '</tbody></table>';
        wrap.innerHTML = html;

        wrap.querySelectorAll('.install-btn').forEach(b => b.addEventListener('click', () => installSkill(b.dataset.id)));
        wrap.querySelectorAll('.enable-btn').forEach(b => b.addEventListener('click', () => setEnabled(b.dataset.id, true)));
        wrap.querySelectorAll('.disable-btn').forEach(b => b.addEventListener('click', () => setEnabled(b.dataset.id, false)));
        wrap.querySelectorAll('.edit-btn').forEach(b => b.addEventListener('click', () => openEditor(b.dataset.id)));

        updateEditorSelect(items.filter(i => i.staged));
    }

    function updateEditorSelect(staged) {
        const sel = document.getElementById('editorSkillSelect');
        const cur = sel.value;
        sel.innerHTML = '<option value="">选择已安装技能…</option>' +
            staged.map(i => `<option value="${escapeHtml(i.id)}">${escapeHtml(i.name)}</option>`).join('');
        if (cur && staged.some(i => i.id === cur)) sel.value = cur;
    }

    async function loadBuiltin() {
        const res = await axios.get('/api/skills/builtin');
        renderBuiltin(res.data.skills || []);
    }

    async function loadRepos() {
        const res = await axios.get('/api/skills/repos');
        renderRepos(res.data.repos || []);
    }

    async function loadCatalog(q) {
        const res = await axios.get('/api/skills/catalog', { params: { q: q || '' } });
        renderCatalog(res.data.items || []);
    }

    async function refreshRepos(repoId) {
        log(`[IFRIT] 开始刷新仓库 ${repoId || '全部'}…`);
        try {
            await streamTask('/api/skills/refresh', repoId ? { repo_id: repoId } : {});
            await loadRepos();
            await loadCatalog(document.getElementById('catalogSearch').value);
            IfritUI.showToast('刷新完成', 'success');
        } catch (e) {
            IfritUI.showToast(e.message || '刷新失败', 'error');
        }
    }

    async function addRepo() {
        const url = document.getElementById('repoUrlInput').value.trim();
        const branch = document.getElementById('repoBranchInput').value.trim() || 'main';
        if (!url) return alert('请输入仓库 URL');
        await axios.post('/api/skills/repos', { url, branch });
        document.getElementById('repoUrlInput').value = '';
        await loadRepos();
        IfritUI.showToast('仓库已添加', 'success');
    }

    async function removeRepo(repoId) {
        if (!confirm('删除仓库及本地缓存？')) return;
        await axios.delete('/api/skills/repos/' + encodeURIComponent(repoId));
        await loadRepos();
        await loadCatalog();
    }

    async function installSkill(skillId) {
        log(`[IFRIT] 安装技能 ${skillId}`);
        await axios.post('/api/skills/install', { skill_id: skillId });
        await loadCatalog(document.getElementById('catalogSearch').value);
        IfritUI.showToast('已安装', 'success');
    }

    async function setEnabled(skillId, enabled) {
        await axios.post('/api/skills/enable', { skill_id: skillId, enabled });
        await loadCatalog(document.getElementById('catalogSearch').value);
    }

    function initEditor() {
        if (!window.ace) return;
        editor = ace.edit('skillAceEditor');
        editor.setTheme('ace/theme/monokai');
        editor.session.setMode('ace/mode/text');
        editor.setOptions({ fontSize: '13px', showPrintMargin: false });
        editor.on('change', () => {
            document.getElementById('saveSkillBtn').disabled = !currentSkillId;
        });
    }

    async function openEditor(skillId) {
        if (!skillId) return;
        const res = await axios.get('/api/skills/editor/' + encodeURIComponent(skillId));
        currentSkillId = skillId;
        document.getElementById('editorSkillSelect').value = skillId;
        document.getElementById('editorPathLabel').textContent = res.data.path || '';
        editor.setValue(res.data.content || '', -1);
        document.getElementById('saveSkillBtn').disabled = !!res.data.readonly;
        bootstrap.Tab.getOrCreateInstance(document.querySelector('[data-bs-target="#tabEditor"]')).show();
    }

    async function saveEditor() {
        if (!currentSkillId) return;
        await axios.post('/api/skills/editor/' + encodeURIComponent(currentSkillId), {
            content: editor.getValue(),
        });
        IfritUI.showToast('已保存', 'success');
        await loadCatalog(document.getElementById('catalogSearch').value);
    }

    function bindEvents() {
        document.getElementById('refreshAllBtn').addEventListener('click', () => refreshRepos());
        document.getElementById('addRepoBtn').addEventListener('click', () => addRepo().catch(e => alert(e.response?.data?.error || e.message)));
        document.getElementById('discoverTabBtn').addEventListener('shown.bs.tab', () => {
            loadRepos().catch(() => {});
            loadCatalog().catch(() => {});
        });
        document.getElementById('catalogSearch').addEventListener('input', e => {
            loadCatalog(e.target.value).catch(() => {});
        });
        document.getElementById('editorSkillSelect').addEventListener('change', e => {
            if (e.target.value) openEditor(e.target.value).catch(err => alert(err.response?.data?.error || err.message));
        });
        document.getElementById('saveSkillBtn').addEventListener('click', () => saveEditor().catch(e => alert(e.response?.data?.error || e.message)));
    }

    function init() {
        initEditor();
        bindEvents();
        loadBuiltin().catch(e => log('加载内置技能失败: ' + e.message));
    }

    return { init };
})();

document.addEventListener('DOMContentLoaded', () => SkillsPage.init());
