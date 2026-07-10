/**
 * 知识库 RAG 管理页
 */
(function() {
    async function loadStats() {
        const res = await axios.get('/api/knowledge/stats');
        const stats = res.data.stats || {};
        document.getElementById('statDocs').textContent = stats.documents ?? 0;
        document.getElementById('statChunks').textContent = stats.chunks ?? 0;
        document.getElementById('statDb').textContent = stats.db_path || '-';
    }

    async function loadDocuments() {
        const res = await axios.get('/api/knowledge/documents');
        const docs = res.data.documents || [];
        const wrap = document.getElementById('docsTableWrap');
        if (!docs.length) {
            wrap.innerHTML = '<p class="text-muted p-4 mb-0">暂无索引，请先导入或重建</p>';
            return;
        }
        let html = '<table class="table-platform mb-0"><thead><tr><th>标题</th><th>类型</th><th>路径</th><th>片段</th><th></th></tr></thead><tbody>';
        docs.forEach(doc => {
            html += `<tr>
                <td>${escapeHtml(doc.title)}</td>
                <td><span class="badge bg-secondary">${escapeHtml(doc.source_type)}</span></td>
                <td><code class="small">${escapeHtml(doc.source_path)}</code></td>
                <td>${doc.chunk_count || 0}</td>
                <td><button class="btn btn-sm btn-outline-danger del-doc" data-id="${doc.id}">删除</button></td>
            </tr>`;
        });
        html += '</tbody></table>';
        wrap.innerHTML = html;
        wrap.querySelectorAll('.del-doc').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (!confirm('确定删除该文档索引？')) return;
                await axios.delete('/api/knowledge/documents/' + btn.dataset.id);
                loadDocuments();
                loadStats();
            });
        });
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text || '';
        return d.innerHTML;
    }

    document.getElementById('rebuildBtn').addEventListener('click', async () => {
        const logEl = document.getElementById('rebuildLog');
        logEl.innerHTML = '';
        document.getElementById('rebuildBtn').disabled = true;
        try {
            const res = await axios.post('/api/knowledge/rebuild');
            IfritUI.streamLogs(res.data.process_id, logEl, () => {
                document.getElementById('rebuildBtn').disabled = false;
                loadStats();
                loadDocuments();
            });
        } catch (e) {
            alert(e.response?.data?.error || e.message);
            document.getElementById('rebuildBtn').disabled = false;
        }
    });

    document.getElementById('uploadIngestBtn').addEventListener('click', async () => {
        const file = document.getElementById('ingestFile').files[0];
        if (!file) return alert('请选择文件');
        const fd = new FormData();
        fd.append('file', file);
        fd.append('source_type', document.getElementById('ingestSourceType').value);
        const res = await axios.post('/api/knowledge/ingest', fd);
        IfritUI.showToast('已入库: ' + res.data.path, 'success');
        loadStats();
        loadDocuments();
    });

    document.getElementById('pasteIngestBtn').addEventListener('click', async () => {
        const text = document.getElementById('pasteText').value.trim();
        if (!text) return alert('请粘贴内容');
        const res = await axios.post('/api/knowledge/ingest', {
            text,
            title: document.getElementById('pasteTitle').value.trim() || 'paste_input.md',
            source_type: document.getElementById('ingestSourceType').value,
        });
        IfritUI.showToast('已入库: ' + res.data.path, 'success');
        document.getElementById('pasteText').value = '';
        loadStats();
        loadDocuments();
    });

    document.getElementById('searchBtn').addEventListener('click', async () => {
        const query = document.getElementById('searchQuery').value.trim();
        if (!query) return;
        const res = await axios.post('/api/knowledge/search', { query, top_k: 8 });
        document.getElementById('searchResult').textContent =
            res.data.formatted || JSON.stringify(res.data.hits, null, 2);
    });

    loadStats().catch(() => {});
    loadDocuments().catch(() => {});
})();
