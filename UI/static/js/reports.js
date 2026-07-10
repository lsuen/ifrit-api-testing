/**
 * 报告中心
 */
(function() {
    const log = document.getElementById('reportLog');

    function runTask(url, body, reloadDelay) {
        if (log) log.innerHTML = '';
        return axios.post(url, body || {}).then(res => {
            IfritUI.streamLogs(res.data.process_id, log, () => {
                if (reloadDelay !== false) {
                    setTimeout(() => location.reload(), reloadDelay == null ? 2000 : reloadDelay);
                }
            });
        });
    }

    document.getElementById('genReportBtn')?.addEventListener('click', () => {
        runTask('/api/reports/generate').catch(e => alert(e.response?.data?.error || e.message));
    });

    document.getElementById('serveReportBtn')?.addEventListener('click', () => {
        runTask('/api/reports/serve', {}, false).catch(e => alert(e.response?.data?.error || e.message));
    });

    document.getElementById('cleanReportBtn')?.addEventListener('click', () => {
        if (confirm('确认按策略清理过期报告？')) {
            runTask('/api/clean', { target: 'reports' }).catch(e => alert(e.response?.data?.error || e.message));
        }
    });

    document.querySelectorAll('.btn-gen-run').forEach(btn => {
        btn.addEventListener('click', async () => {
            const runId = btn.dataset.runId;
            btn.disabled = true;
            try {
                const res = await axios.post('/api/reports/run/' + runId + '/generate');
                IfritUI.showToast('HTML 已生成', 'success');
                window.open(res.data.html_url, '_blank');
                setTimeout(() => location.reload(), 800);
            } catch (e) {
                alert(e.response?.data?.error || e.message);
                btn.disabled = false;
            }
        });
    });

    document.querySelectorAll('.btn-copy-run').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.runId;
            navigator.clipboard.writeText(id).then(() => {
                IfritUI.showToast('已复制 Run ID', 'success');
            }).catch(() => prompt('Run ID', id));
        });
    });

    document.querySelectorAll('.btn-del-run').forEach(btn => {
        btn.addEventListener('click', async () => {
            const runId = btn.dataset.runId;
            if (!confirm('确定删除 Run「' + runId + '」整个目录？此操作不可恢复。')) return;
            try {
                await axios.delete('/api/reports/run/' + runId);
                IfritUI.showToast('已删除', 'success');
                btn.closest('tr')?.remove();
            } catch (e) {
                alert(e.response?.data?.error || e.message);
            }
        });
    });
})();
