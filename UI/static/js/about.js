/**
 * 关于页：项目信息 / 用户手册 / CLI 文档（只读渲染）
 */
(function() {
    const UNAVAILABLE = '获取不到';
    let manualLoaded = false;
    let cliLoaded = false;

    function fmtStat(val) {
        return val === null || val === undefined ? UNAVAILABLE : val;
    }

    function renderProjectInfo(data) {
        const wrap = document.getElementById('projectInfoWrap');
        const stats = data.stats || {};
        const envs = (data.environments || []).map(e =>
            `<li><code>${e.name}</code> — ${e.base_url || UNAVAILABLE}</li>`
        ).join('') || `<li class="text-muted">${UNAVAILABLE}</li>`;

        wrap.innerHTML = `
            <div class="row g-4">
                <div class="col-lg-6">
                    <h2 class="h5 mb-3">${data.name || 'ifrit'}</h2>
                    <p class="text-muted">${data.tagline || ''}</p>
                    <table class="table-platform">
                        <tr><th style="width:140px">版本</th><td><code>${data.version || UNAVAILABLE}</code></td></tr>
                        <tr><th>UI</th><td>v${data.ui_version || '2.0'}</td></tr>
                        <tr><th>项目根目录</th><td><code class="small">${data.project_root || UNAVAILABLE}</code></td></tr>
                        <tr><th>Python</th><td><code>${data.python_bin || 'python'}</code></td></tr>
                        <tr><th>全局鉴权</th><td>${data.auth && data.auth.available
                            ? `已配置 ${data.auth.login_path || ''} (${data.auth.username || ''})`
                            : UNAVAILABLE}</td></tr>
                    </table>
                </div>
                <div class="col-lg-6">
                    <h3 class="h6 text-muted mb-2">用例与报告</h3>
                    <table class="table-platform mb-3">
                        <tr><th>smoke</th><td>${fmtStat(stats.smoke_cases)} 条</td></tr>
                        <tr><th>manual</th><td>${fmtStat(stats.manual_cases)} 条</td></tr>
                        <tr><th>ai</th><td>${fmtStat(stats.ai_cases)} 条</td></tr>
                        <tr><th>报告 runs</th><td>${fmtStat(stats.report_runs)}</td></tr>
                        <tr><th>最近 run</th><td>${stats.latest_run
                            ? `<a href="/reports/view/${stats.latest_run}/">${stats.latest_run}</a>`
                            : UNAVAILABLE}</td></tr>
                    </table>
                    <h3 class="h6 text-muted mb-2">环境</h3>
                    <ul class="small mb-0">${envs}</ul>
                </div>
            </div>
            <hr class="my-4">
            <p class="small text-muted mb-0">文档源：
                <code>${(data.doc_sources && data.doc_sources.manual) || '用户详细使用手册.md'}</code> ·
                <code>${(data.doc_sources && data.doc_sources.cli_manual) || '__docs/ifrit命令手册.md'}</code> ·
                <code>${(data.doc_sources && data.doc_sources.cli_recipes) || '__docs/cli_recipes.yaml'}</code>
            </p>`;
    }

    function renderMarkdown(container, md, sourceLabel) {
        if (!md) {
            container.innerHTML = `<p class="text-muted mb-0">${UNAVAILABLE}</p>`;
            return;
        }
        if (typeof marked !== 'undefined') {
            marked.setOptions({ breaks: true, gfm: true });
            container.innerHTML = marked.parse(md);
        } else {
            container.innerHTML = `<pre class="mb-0">${md.replace(/</g, '&lt;')}</pre>`;
        }
        if (sourceLabel) {
            const el = document.getElementById(sourceLabel);
            if (el) el.textContent = container.closest('.card-panel') ? el.textContent.split('·')[0].trim() : el.textContent;
        }
    }

    function renderRecipes(groups) {
        const wrap = document.getElementById('cliRecipesWrap');
        if (!groups || !groups.length) {
            wrap.innerHTML = '<p class="text-muted mb-0">暂无组合案例</p>';
            return;
        }
        let html = '';
        groups.forEach(group => {
            html += `<h3 class="h6 mt-3 mb-2">${group.title || '未命名'}</h3><div class="row g-2">`;
            (group.items || []).forEach(item => {
                const cmd = item.command || '';
                html += `<div class="col-md-6"><div class="recipe-card p-3 h-100">
                    <div class="fw-semibold mb-1">${item.name || '命令'}</div>
                    <div class="small text-muted mb-2">${item.note || ''}</div>
                    <pre class="recipe-cmd mb-2"><code>python main.py ${cmd}</code></pre>
                    <button type="button" class="btn btn-sm btn-outline-secondary copy-recipe-btn" data-cmd="python main.py ${cmd.replace(/"/g, '&quot;')}">复制</button>
                </div></div>`;
            });
            html += '</div>';
        });
        wrap.innerHTML = html;
        wrap.querySelectorAll('.copy-recipe-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                navigator.clipboard.writeText(btn.dataset.cmd || '').then(() => {
                    IfritUI.showToast('已复制', 'success');
                }).catch(() => alert(btn.dataset.cmd));
            });
        });
    }

    async function loadInfo() {
        const res = await axios.get('/api/about/info');
        renderProjectInfo(res.data);
    }

    async function loadManual() {
        if (manualLoaded) return;
        const res = await axios.get('/api/about/manual');
        if (!res.data.success) {
            document.getElementById('manualContent').innerHTML =
                `<p class="text-muted">${res.data.error || UNAVAILABLE}</p>`;
            return;
        }
        document.getElementById('manualSourceLabel').textContent = res.data.source || '用户手册';
        renderMarkdown(document.getElementById('manualContent'), res.data.content);
        manualLoaded = true;
    }

    async function loadCli() {
        if (cliLoaded) return;
        const res = await axios.get('/api/about/cli');
        if (!res.data.success) {
            document.getElementById('cliRecipesWrap').innerHTML =
                `<p class="text-muted">${res.data.error || UNAVAILABLE}</p>`;
            return;
        }
        renderRecipes(res.data.recipes);
        if (res.data.manual_source) {
            document.getElementById('cliManualLabel').textContent =
                `命令手册 · ${res.data.manual_source}`;
        }
        renderMarkdown(document.getElementById('cliManualContent'), res.data.manual_content);
        cliLoaded = true;
    }

    document.getElementById('manualTabBtn').addEventListener('shown.bs.tab', () => {
        loadManual().catch(e => IfritUI.showToast(e.message, 'error'));
    });
    document.getElementById('cliTabBtn').addEventListener('shown.bs.tab', () => {
        loadCli().catch(e => IfritUI.showToast(e.message, 'error'));
    });
    document.getElementById('manualTopLink').addEventListener('click', e => {
        e.preventDefault();
        document.getElementById('manualContent').scrollIntoView({ behavior: 'smooth' });
    });

    loadInfo().catch(e => {
        document.getElementById('projectInfoWrap').innerHTML =
            `<p class="text-danger mb-0">加载失败: ${e.message}</p>`;
    });
})();
