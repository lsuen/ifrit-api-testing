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
        el.textContent = message;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 3000);
    }

    return { appendLog, streamLogs, showToast };
})();
