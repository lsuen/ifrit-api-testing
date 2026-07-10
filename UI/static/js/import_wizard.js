/**
 * 导入中心向导：预览 → 诊断 → 合并 → 保存
 */
const ImportWizard = (function() {
    const state = {
        importFile: '',
        sourcePath: '',
        originalRows: [],
        meta: {},
        suggestedCases: [],
        selectedSuggested: new Set(),
        diagnosis: [],
        summary: '',
    };

    function buildFormData(extra) {
        const fd = new FormData();
        const fileInput = document.getElementById('importFile');
        const file = fileInput.files[0];
        if (file) fd.append('file', file);
        else if (state.sourcePath) fd.append('source_path', state.sourcePath);
        else if (state.importFile) fd.append('source_path', state.importFile);
        fd.append('format', document.getElementById('importFormat').value);
        fd.append('suite', document.getElementById('importSuite').value);
        if (extra) Object.keys(extra).forEach(k => fd.append(k, extra[k]));
        return fd;
    }

    function renderTable(rows, containerId, highlightSource) {
        const wrap = document.getElementById(containerId);
        if (!rows.length) {
            wrap.innerHTML = '<p class="text-muted p-4 mb-0">无数据</p>';
            return;
        }
        let html = '<table class="table-platform mb-0"><thead><tr><th>#</th><th>名称</th><th>方法</th><th>URL</th><th>状态码</th>';
        if (highlightSource) html += '<th>来源</th>';
        html += '</tr></thead><tbody>';
        rows.forEach((row, i) => {
            const src = row._source || 'original';
            const cls = src === 'appended' || src === 'suggested' ? 'table-success' : '';
            html += `<tr class="${cls}"><td>${row.id || i+1}</td><td>${escapeHtml(row.name)}</td><td>${row.method}</td><td><code>${escapeHtml(row.url)}</code></td><td>${row.expected_status || '-'}</td>`;
            if (highlightSource) html += `<td>${src}</td>`;
            html += '</tr>';
        });
        html += '</tbody></table>';
        wrap.innerHTML = html;
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text || '';
        return d.innerHTML;
    }

    function renderDiagnosis(data) {
        const wrap = document.getElementById('diagnosisWrap');
        const parts = [];
        if (data.summary) parts.push(`<p><strong>摘要：</strong>${escapeHtml(data.summary)}</p>`);
        if (!data.diagnosis || !data.diagnosis.length) {
            wrap.innerHTML = parts.join('') + '<p class="text-muted mb-0">无诊断项</p>';
            return;
        }
        parts.push('<ul class="mb-0">');
        data.diagnosis.forEach(item => {
            parts.push(`<li><span class="badge bg-secondary">${item.category || 'other'}</span> <code>${escapeHtml(item.endpoint || '')}</code> — ${escapeHtml(item.detail || '')}</li>`);
        });
        parts.push('</ul>');
        wrap.innerHTML = parts.join('');
    }

    function renderSuggested(cases) {
        const wrap = document.getElementById('suggestedWrap');
        if (!cases.length) {
            wrap.innerHTML = '<p class="text-muted p-4 mb-0">LLM 未建议追加用例</p>';
            return;
        }
        let html = '<table class="table-platform mb-0"><thead><tr><th></th><th>名称</th><th>方法</th><th>URL</th><th>原因</th></tr></thead><tbody>';
        cases.forEach((row, i) => {
            const id = row.id || ('s'+i);
            const checked = state.selectedSuggested.has(id) ? 'checked' : '';
            html += `<tr><td><input type="checkbox" class="form-check-input suggest-check" data-id="${id}" ${checked}></td>`;
            html += `<td>${escapeHtml(row.name)}</td><td>${row.method}</td><td><code>${escapeHtml(row.url)}</code></td><td class="small">${escapeHtml(row._reason || '')}</td></tr>`;
        });
        html += '</tbody></table>';
        wrap.innerHTML = html;
        wrap.querySelectorAll('.suggest-check').forEach(cb => {
            cb.addEventListener('change', () => {
                if (cb.checked) state.selectedSuggested.add(cb.dataset.id);
                else state.selectedSuggested.delete(cb.dataset.id);
                updateMergedPreview();
            });
        });
    }

    function updateMergedPreview() {
        const append = state.suggestedCases.filter(row => state.selectedSuggested.has(row.id));
        const merged = state.originalRows.map(r => ({...r, _source: 'original'}));
        append.forEach(r => merged.push({...r, _source: 'appended'}));
        merged.forEach((r, i) => r.id = String(i + 1));
        renderTable(merged, 'mergedTableWrap', true);
        document.getElementById('saveBtn').disabled = !state.originalRows.length;
    }

    function parseMarkerFromLog(container, marker) {
        const lines = container.querySelectorAll('.log-line');
        for (const line of lines) {
            const text = line.textContent;
            const idx = text.indexOf(marker);
            if (idx >= 0) {
                try { return JSON.parse(text.slice(idx + marker.length)); } catch(e) {}
            }
        }
        return null;
    }

    function appendLog(msg) {
        const log = document.getElementById('importLog');
        IfritUI.appendLog(log, msg);
    }

    async function doPreview() {
        const fd = buildFormData();
        appendLog('[IFRIT] 开始解析预览...');
        const res = await axios.post('/api/import/preview', fd);
        state.originalRows = res.data.rows || [];
        state.meta = res.data.meta || {};
        state.importFile = res.data.import_file || '';
        state.suggestedCases = [];
        state.selectedSuggested.clear();
        renderTable(state.originalRows, 'previewTableWrap', false);
        document.getElementById('diagnoseBtn').disabled = !state.originalRows.length;
        document.getElementById('saveBtn').disabled = !state.originalRows.length;
        updateMergedPreview();
        appendLog(`[IFRIT] 预览完成 条数=${state.originalRows.length}`);
        IfritUI.showToast('预览完成', 'success');
    }

    async function doDiagnose() {
        const fd = buildFormData();
        if (document.getElementById('injectContextCheck').checked) fd.append('inject_project_context', '1');
        if (document.getElementById('ragCheck').checked) fd.append('rag', '1');
        appendLog('[IFRIT] 开始 AI 诊断...');
        document.getElementById('diagnoseBtn').disabled = true;
        const res = await axios.post('/api/import/diagnose', fd);
        const logEl = document.getElementById('importLog');
        IfritUI.streamLogs(res.data.process_id, logEl, (status) => {
            document.getElementById('diagnoseBtn').disabled = false;
            if (status.status === 'completed') {
                const data = parseMarkerFromLog(logEl, '[IFRIT] IMPORT_DIAGNOSE_JSON=');
                if (data) {
                    state.diagnosis = data.diagnosis || [];
                    state.summary = data.summary || '';
                    state.suggestedCases = data.suggested_cases || [];
                    state.suggestedCases.forEach(r => state.selectedSuggested.add(r.id));
                    renderDiagnosis(data);
                    renderSuggested(state.suggestedCases);
                    updateMergedPreview();
                    bootstrap.Tab.getOrCreateInstance(document.querySelector('[data-bs-target="#tabDiagnosis"]')).show();
                    IfritUI.showToast('诊断完成', 'success');
                } else {
                    IfritUI.showToast('诊断完成，请查看日志', 'success');
                }
            } else if (status.status === 'failed') {
                const lines = [...logEl.querySelectorAll('.log-line')].map(el => el.textContent);
                const errLine = [...lines].reverse().find(t =>
                    /诊断失败|模型「|LLM 请求失败|LLM 调用|model_not_found/i.test(t)
                );
                IfritUI.showToast(errLine ? errLine.replace(/^\[IFRIT\]\s*/, '') : '诊断失败，请查看日志', 'error');
            }
        });
    }

    async function doSave() {
        const append = state.suggestedCases.filter(row => state.selectedSuggested.has(row.id));
        const payload = {
            original_rows: state.originalRows,
            append_rows: append,
            suite: document.getElementById('importSuite').value,
            output_format: document.getElementById('outputFormat').value,
            output: document.getElementById('importOutput').value.trim(),
            collection_name: state.meta.collection_name || 'import',
        };
        appendLog('[IFRIT] 保存中...');
        const res = await axios.post('/api/import/save', payload);
        document.getElementById('saveResultPath').textContent = res.data.output_file;
        document.getElementById('saveResultBox').style.display = 'block';
        appendLog(`[IFRIT] 保存完成 输出=${res.data.output_file} 合计=${res.data.total}`);
        if (res.data.rag_ingested) {
            appendLog('[IFRIT] 已自动写入知识库');
        }
        IfritUI.showToast('保存成功', 'success');
    }

    function init(opts) {
        async function loadLibrary() {
            const wrap = document.getElementById('libraryTableWrap');
            if (!wrap) return;
            try {
                const res = await axios.get('/api/cases/catalog');
                const files = res.data.files || [];
                if (!files.length) {
                    wrap.innerHTML = '<p class="text-muted p-4 mb-0">fixtures 下暂无用例文件</p>';
                    return;
                }
                let html = '<table class="table-platform mb-0"><thead><tr><th>套件</th><th>文件</th><th>条数</th><th>路径</th></tr></thead><tbody>';
                files.forEach(f => {
                    html += `<tr><td>${f.suite}</td><td>${escapeHtml(f.name)}</td><td>${f.case_count ?? '-'}</td><td><code class="small">${escapeHtml(f.relative)}</code></td></tr>`;
                });
                html += '</tbody></table>';
                wrap.innerHTML = html;
            } catch (e) {
                wrap.innerHTML = '<p class="text-muted p-4 mb-0">加载失败</p>';
            }
        }

        if (opts.samplePath) {
            document.getElementById('useSampleBtn').addEventListener('click', e => {
                e.preventDefault();
                state.sourcePath = opts.samplePath;
                document.getElementById('importFile').value = '';
                IfritUI.showToast('已选用样例', 'success');
            });
        }
        document.getElementById('previewBtn').addEventListener('click', () => doPreview().catch(e => alert(e.response?.data?.error || e.message)));
        document.getElementById('diagnoseBtn').addEventListener('click', () => doDiagnose().catch(e => alert(e.response?.data?.error || e.message)));
        document.getElementById('saveBtn').addEventListener('click', () => doSave().catch(e => alert(e.response?.data?.error || e.message)));
        const refreshBtn = document.getElementById('refreshLibraryBtn');
        if (refreshBtn) refreshBtn.addEventListener('click', () => loadLibrary());
        loadLibrary();
        IfritUI.applyRagDefaultCheckbox('ragCheck');
    }

    return { init };
})();
