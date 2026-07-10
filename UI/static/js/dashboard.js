/**
 * 仪表盘：就绪检查 + 一键流水线
 */
(function() {
    const cfg = window.IFRIT_DASHBOARD || {};
    const logEl = document.getElementById('pipelineLog');
    let busy = false;

    function setBusy(on) {
        busy = on;
        const smokeBtn = document.getElementById('pipelineSmokeBtn');
        const aiBtn = document.getElementById('pipelineAiBtn');
        const importBtn = document.getElementById('pipelineImportBtn');
        if (smokeBtn) smokeBtn.disabled = on || !cfg.smokeFile;
        if (aiBtn) aiBtn.disabled = on || !cfg.defaultDoc;
        if (importBtn) importBtn.disabled = on || !cfg.sampleImport;
    }

    function parseImportOutputFromLog() {
        const lines = logEl.querySelectorAll('.log-line');
        for (let i = lines.length - 1; i >= 0; i--) {
            const m = lines[i].textContent.match(/输出=([^\s]+)/);
            if (m) return m[1].replace(/\\/g, '/');
        }
        return null;
    }

    async function runImport(params) {
        const fd = new FormData();
        fd.append('source_path', params.import_file);
        fd.append('format', params.format || 'postman');
        fd.append('suite', params.suite || 'manual');
        fd.append('output_format', params.output_format || 'csv');
        if (params.output) fd.append('output', params.output);
        const res = await axios.post('/api/import', fd);
        IfritUI.appendLog(logEl, '[IFRIT] 导入: ' + res.data.command);
        return waitProcess(res.data.process_id);
    }

    function waitProcess(processId) {
        return new Promise((resolve) => {
            IfritUI.streamLogs(processId, logEl, (status) => resolve(status));
        });
    }

    async function runExecute(params) {
        const res = await axios.post('/api/execute', { params });
        IfritUI.appendLog(logEl, '[IFRIT] 执行: ' + res.data.command);
        return waitProcess(res.data.process_id);
    }

    async function runGenerate(payload) {
        const res = await axios.post('/api/ai/generate', payload);
        IfritUI.appendLog(logEl, '[IFRIT] 生成: ' + res.data.command);
        return waitProcess(res.data.process_id);
    }

    function parseSavedPathFromLog() {
        const lines = logEl.querySelectorAll('.log-line');
        for (let i = lines.length - 1; i >= 0; i--) {
            const text = lines[i].textContent;
            const m = text.match(/\[IFRIT\] AI用例已保存=([^\s]+)/);
            if (m) return m[1];
        }
        return null;
    }

    async function maybeIngestRag(path) {
        if (!path) return;
        try {
            const res = await axios.post('/api/settings/rag/ingest-case', { path });
            if (res.data.ingested) {
                IfritUI.appendLog(logEl, '[IFRIT] 已写入知识库: ' + path);
            }
        } catch (e) { /* optional */ }
    }

    async function showLatestReport() {
        const latest = await IfritUI.showLatestReport(
            document.getElementById('pipelineReportLink'),
            document.getElementById('pipelineReportBox')
        );
        return latest;
    }

    async function loadReadiness() {
        const banner = document.getElementById('readinessBanner');
        const text = document.getElementById('readinessText');
        if (!banner || !text) return;
        try {
            const res = await axios.post('/api/settings/health', { ping_llm: false });
            const data = res.data;
            banner.classList.remove('d-none', 'alert-success', 'alert-warning', 'alert-secondary');
            if (data.ready) {
                banner.classList.add('alert-success');
                text.textContent = '✓ ' + (data.summary || '配置就绪，可以开始测试');
            } else {
                banner.classList.add('alert-warning');
                const failed = (data.checks || []).filter(c => !c.ok && c.level === 'required');
                const hint = failed.length ? failed.map(c => c.name).join('、') : '必要项未就绪';
                text.textContent = '请先完成设置：' + hint;
            }
        } catch (e) {
            banner.classList.remove('d-none');
            banner.classList.add('alert-secondary');
            text.textContent = '无法检查配置，请打开设置页手动确认';
        }
    }

    document.getElementById('pipelineSmokeBtn')?.addEventListener('click', async () => {
        if (busy || !cfg.smokeFile) return;
        setBusy(true);
        logEl.innerHTML = '';
        document.getElementById('pipelineReportBox').style.display = 'none';
        IfritUI.appendLog(logEl, '[IFRIT] 冒烟全流程开始…');
        try {
            const status = await runExecute({
                file: cfg.smokeFile,
                global_auth: true,
                generate_report: true,
            });
            if (status.status === 'completed') {
                IfritUI.showToast('冒烟测试完成', 'success');
                await showLatestReport();
            } else {
                IfritUI.showToast('冒烟测试失败，请查看日志', 'error');
            }
        } catch (e) {
            IfritUI.showToast(e.response?.data?.error || e.message, 'error');
        } finally {
            setBusy(false);
        }
    });

    document.getElementById('pipelineAiBtn')?.addEventListener('click', async () => {
        if (busy || !cfg.defaultDoc) return;
        setBusy(true);
        logEl.innerHTML = '';
        document.getElementById('pipelineReportBox').style.display = 'none';
        IfritUI.appendLog(logEl, '[IFRIT] AI 生成并执行开始…');
        try {
            let useRag = false;
            try {
                useRag = await IfritUI.shouldEnableRagDefault();
            } catch (e) { /* ignore */ }

            const genStatus = await runGenerate({
                input_doc: cfg.defaultDoc,
                format: 'csv',
                output_dir: cfg.aiOutputDir || 'fixtures/ai/csv',
                rag: useRag,
            });
            if (genStatus.status !== 'completed') {
                IfritUI.showToast('AI 生成失败', 'error');
                return;
            }
            const savedPath = parseSavedPathFromLog();
            await maybeIngestRag(savedPath);

            const runStatus = await runExecute({
                suite: 'ai',
                type: 'csv',
                global_auth: true,
                generate_report: true,
            });
            if (runStatus.status === 'completed') {
                IfritUI.showToast('生成并执行完成', 'success');
                await showLatestReport();
            } else {
                IfritUI.showToast('执行失败，请查看日志', 'error');
            }
        } catch (e) {
            IfritUI.showToast(e.response?.data?.error || e.message, 'error');
        } finally {
            setBusy(false);
        }
    });

    document.getElementById('pipelineImportBtn')?.addEventListener('click', async () => {
        if (busy || !cfg.sampleImport) return;
        setBusy(true);
        logEl.innerHTML = '';
        document.getElementById('pipelineReportBox').style.display = 'none';
        IfritUI.appendLog(logEl, '[IFRIT] 导入→执行流水线开始…');
        const outputPath = cfg.importOutput || 'fixtures/manual/csv/dashboard_import_run.csv';
        try {
            const importStatus = await runImport({
                import_file: cfg.sampleImport,
                format: 'postman',
                suite: 'manual',
                output_format: 'csv',
                output: outputPath,
            });
            if (importStatus.status !== 'completed') {
                IfritUI.showToast('导入失败', 'error');
                return;
            }
            const savedPath = parseImportOutputFromLog() || outputPath;
            await maybeIngestRag(savedPath);

            const runStatus = await runExecute({
                file: savedPath,
                global_auth: true,
                generate_report: true,
            });
            if (runStatus.status === 'completed') {
                IfritUI.showToast('导入并执行完成', 'success');
                await showLatestReport();
            } else {
                IfritUI.showToast('执行失败，请查看日志', 'error');
            }
        } catch (e) {
            IfritUI.showToast(e.response?.data?.error || e.message, 'error');
        } finally {
            setBusy(false);
        }
    });

    loadReadiness();
})();
