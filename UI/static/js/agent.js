/**
 * Agent 对话页：自然语言 → 计划 → CLI 执行
 */
(function() {
    const historyEl = document.getElementById('chatHistory');
    const logEl = document.getElementById('agentLog');
    const planBox = document.getElementById('planBox');
    const inputEl = document.getElementById('agentInput');
    let busy = false;

    function appendMsg(role, text, extraClass) {
        const div = document.createElement('div');
        div.className = 'agent-msg ' + role + (extraClass ? ' ' + extraClass : '');
        div.innerHTML = `<div class="role">${role === 'user' ? '你' : 'Agent'}</div><div class="agent-msg-body">${formatMsg(text)}</div>`;
        historyEl.appendChild(div);
        historyEl.scrollTop = historyEl.scrollHeight;
        return div;
    }

    function formatMsg(t) {
        return escapeHtml(t || '').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
    }

    function renderSuggestions(list) {
        let wrap = document.getElementById('agentSuggestions');
        if (!wrap) {
            wrap = document.createElement('div');
            wrap.id = 'agentSuggestions';
            wrap.className = 'd-flex flex-wrap gap-2 mt-2';
            historyEl.parentElement.appendChild(wrap);
        }
        wrap.innerHTML = '';
        (list || []).forEach(text => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-sm btn-outline-secondary';
            btn.textContent = text;
            btn.addEventListener('click', () => {
                inputEl.value = text;
                handleSend(text);
            });
            wrap.appendChild(btn);
        });
    }

    function escapeHtml(t) {
        const d = document.createElement('div');
        d.textContent = t || '';
        return d.innerHTML;
    }

    function getForm() {
        const endpoints = document.getElementById('agentEndpoints').value.split('\n').map(s => s.trim()).filter(Boolean);
        return {
            input_doc: document.getElementById('agentDoc').value || undefined,
            endpoints,
            rag: document.getElementById('agentRag').checked,
            run_after: document.getElementById('agentRunAfter').checked,
            skill: document.getElementById('agentSkill').value || undefined,
            no_auto_skill: false,
        };
    }

    function renderSkillPreview(preview) {
        const box = document.getElementById('skillPreviewBox');
        if (!preview) {
            box.innerHTML = '<span class="text-muted">无 Skill 预览</span>';
            return;
        }
        box.innerHTML = `<strong>${escapeHtml(preview.skill_name)}</strong>
            <span class="badge bg-secondary ms-1">${preview.source || 'rule'}</span>
            <p class="mb-0 mt-1 text-muted">${escapeHtml(preview.reason || '')}</p>`;
    }

    function waitProcess(processId) {
        return new Promise(resolve => {
            IfritUI.streamLogs(processId, logEl, status => resolve(status));
        });
    }

    async function startStep(step) {
        if (step.type === 'execute') {
            const res = await axios.post('/api/execute', { params: step.params });
            IfritUI.appendLog(logEl, `[IFRIT] ${step.label}: ${res.data.command}`);
            return { status: await waitProcess(res.data.process_id), output: null };
        }
        if (step.type === 'generate') {
            const res = await axios.post('/api/ai/generate', step.params);
            IfritUI.appendLog(logEl, `[IFRIT] ${step.label}: ${res.data.command}`);
            const status = await waitProcess(res.data.process_id);
            const output = parseGenerateOutput();
            return { status, output };
        }
        if (step.type === 'import') {
            const fd = new FormData();
            fd.append('source_path', step.params.import_file);
            fd.append('format', step.params.format || 'postman');
            fd.append('suite', step.params.suite || 'manual');
            fd.append('output_format', step.params.output_format || 'csv');
            if (step.params.output) fd.append('output', step.params.output);
            const res = await axios.post('/api/import', fd);
            IfritUI.appendLog(logEl, `[IFRIT] ${step.label}: ${res.data.command}`);
            const status = await waitProcess(res.data.process_id);
            const output = parseImportOutput() || step.params.output || res.data.output_file;
            return { status, output };
        }
        if (step.type === 'cli') {
            const res = await axios.post('/api/console/exec', { mode: 'cli', line: step.line });
            IfritUI.appendLog(logEl, `[IFRIT] CLI: ${res.data.command}`);
            return { status: await waitProcess(res.data.process_id), output: null };
        }
        if (step.type === 'chat') {
            const res = await axios.post('/api/ai/chat', { commands: step.tokens });
            IfritUI.appendLog(logEl, `[IFRIT] Chat: ${res.data.command}`);
            return { status: await waitProcess(res.data.process_id), output: parseGenerateOutput() };
        }
        if (step.type === 'rag_ingest') {
            const path = step._path;
            if (!path) return { status: { status: 'completed' }, output: null };
            try {
                const res = await axios.post('/api/settings/rag/ingest-case', { path });
                if (res.data.ingested) IfritUI.appendLog(logEl, `[IFRIT] 已写入知识库: ${path}`);
            } catch (e) { /* optional */ }
            return { status: { status: 'completed' }, output: path };
        }
        throw new Error('未知步骤类型: ' + step.type);
    }

    function parseGenerateOutput() {
        const lines = [...logEl.querySelectorAll('.log-line')].map(el => el.textContent);
        for (let i = lines.length - 1; i >= 0; i--) {
            const m = lines[i].match(/\[IFRIT\] AI用例已保存=([^\s]+)/);
            if (m) return m[1];
        }
        return null;
    }

    function parseImportOutput() {
        const lines = [...logEl.querySelectorAll('.log-line')].map(el => el.textContent);
        for (let i = lines.length - 1; i >= 0; i--) {
            const m = lines[i].match(/输出=([^\s]+)/);
            if (m) return m[1].replace(/\\/g, '/');
        }
        return null;
    }

    async function runPlan(plan) {
        planBox.classList.remove('d-none');
        planBox.textContent = '执行中：' + plan.summary;
        let lastOutput = null;
        for (const step of plan.steps) {
            if (step.path_from === 'generate_output' && lastOutput) {
                step._path = lastOutput;
            }
            if (step.path_from === 'import_output' && lastOutput) {
                step._path = lastOutput;
            }
            if (step.after_import && lastOutput) {
                step.params = { ...step.params, file: lastOutput };
            }
            const result = await startStep(step);
            if (result.status.status === 'failed') {
                planBox.className = 'alert alert-danger small mb-3';
                planBox.textContent = `步骤失败：${step.label}`;
                IfritUI.showToast(`${step.label} 失败`, 'error');
                return false;
            }
            if (result.output) lastOutput = result.output;
        }
        planBox.className = 'alert alert-success small mb-3';
        planBox.textContent = '✓ 全部步骤完成：' + plan.summary;
        IfritUI.showToast('Agent 任务完成', 'success');
        return true;
    }

    async function handleSend(message) {
        if (busy || !message.trim()) return;
        busy = true;
        document.getElementById('agentSendBtn').disabled = true;
        appendMsg('user', message);
        inputEl.value = '';

        try {
            const thinking = appendMsg('bot', '思考中…', 'agent-thinking');
            const res = await axios.post('/api/agent/plan', {
                message: message.trim(),
                form: getForm(),
            });
            thinking.remove();
            const plan = res.data;

            if (plan.mode === 'converse' || plan.intent === 'converse') {
                planBox.classList.add('d-none');
                renderSkillPreview(null);
                let replyText = plan.reply || '你好！';
                if (plan.reply_source === 'llm') {
                    appendMsg('bot', replyText, 'agent-llm-reply');
                } else {
                    appendMsg('bot', replyText);
                    if (plan.llm_error) {
                        IfritUI.showToast('LLM 未连通，当前为离线引导', 'error');
                    }
                }
                renderSuggestions(plan.suggestions);
                return;
            }

            renderSkillPreview(plan.skill_preview);
            appendMsg('bot', plan.summary + '\n步骤：' + plan.steps.map(s => s.label).join(' → '));
            renderSuggestions([]);
            await runPlan(plan);
        } catch (e) {
            const err = e.response?.data?.error || e.message;
            appendMsg('bot', '无法执行：' + err);
            IfritUI.showToast(err, 'error');
        } finally {
            busy = false;
            document.getElementById('agentSendBtn').disabled = false;
        }
    }

    document.getElementById('agentSendBtn').addEventListener('click', () => handleSend(inputEl.value));
    inputEl.addEventListener('keydown', e => {
        if (e.key === 'Enter') handleSend(inputEl.value);
    });
    document.querySelectorAll('.agent-quick').forEach(btn => {
        btn.addEventListener('click', () => {
            inputEl.value = btn.dataset.msg;
            handleSend(btn.dataset.msg);
        });
    });
    document.getElementById('agentClearLog').addEventListener('click', () => { logEl.innerHTML = ''; });

    IfritUI.applyRagDefaultCheckbox('agentRag');
    appendMsg('bot',
        '你好！我是 **ifrit 接口自动化测试助手**。\n\n'
        + '可以帮你跑测试、AI 生成用例、导入 Postman，也可以回答项目使用问题。\n'
        + '试试下方快捷按钮，或直接输入「如何配置环境？」');
    renderSuggestions(['跑冒烟测试并出报告', '如何配置鉴权和环境？', '生成 /api/address 用例']);
})();
