/**
 * ifrit-apitest Web UI 主逻辑 - 文件管理器+编辑器
 * 作者：孙文龙
 */

(function() {
    'use strict';

    var currentFile = null;
    var currentDir = 'fixtures';
    var editor = null;
    var originalContent = '';

    // DOM
    var dirSelect = document.getElementById('dirSelect');
    var refreshBtn = document.getElementById('refreshBtn');
    var fileTree = document.getElementById('fileTree');
    var fileName = document.getElementById('fileName');
    var filePath = document.getElementById('filePath');
    var fileSize = document.getElementById('fileSize');
    var fileModified = document.getElementById('fileModified');
    var fileStatus = document.getElementById('fileStatus');
    var editorPlaceholder = document.getElementById('editorPlaceholder');
    var aceEditor = document.getElementById('aceEditor');
    var saveBtn = document.getElementById('saveBtn');
    var reloadBtn = document.getElementById('reloadBtn');
    var saveStatus = document.getElementById('saveStatus');
    var appStatus = document.getElementById('appStatus');
    var toastContainer = document.getElementById('toastContainer');

    // 工具函数
    function formatSize(bytes) {
        if (bytes == null) return '-';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function getFileIconClass(ext) {
        var map = {
            '.csv': 'csv', '.xls': 'excel', '.xlsx': 'excel',
            '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
            '.ini': 'ini', '.py': 'py', '.md': 'md',
            '.txt': 'txt', '.log': 'log', '.html': 'html',
            '.js': 'js', '.css': 'css'
        };
        return map[ext] || '';
    }

    function showToast(message, type) {
        type = type || 'info';
        var toast = document.createElement('div');
        toast.className = 'toast ' + type;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(function() { toast.remove(); }, 3000);
    }

    function setLoading(isLoading) {
        appStatus.textContent = isLoading ? '加载中...' : '就绪';
    }

    // 文件树渲染
    function renderTree(nodes, container) {
        container.innerHTML = '';
        if (!nodes || nodes.length === 0) {
            container.innerHTML = '<div class="tree-loading">目录为空</div>';
            return;
        }

        nodes.forEach(function(node) {
            var nodeEl = document.createElement('div');
            nodeEl.className = 'tree-node';
            nodeEl.dataset.path = node.path;
            nodeEl.dataset.isDir = node.is_dir;

            var header = document.createElement('div');
            header.className = 'tree-node-header';

            var toggle = document.createElement('span');
            toggle.className = 'tree-toggle';
            if (node.is_dir) toggle.textContent = '▶';
            header.appendChild(toggle);

            var icon = document.createElement('span');
            icon.className = 'tree-icon';
            if (node.is_dir) {
                icon.classList.add('dir-icon');
            } else {
                icon.classList.add('file-icon');
                var iconClass = getFileIconClass(node.extension || '');
                if (iconClass) icon.classList.add(iconClass);
            }
            header.appendChild(icon);

            var label = document.createElement('span');
            label.className = 'tree-label';
            label.textContent = node.name;
            header.appendChild(label);

            if (!node.is_dir && !node.supported) {
                nodeEl.classList.add('file-unsupported');
            }

            nodeEl.appendChild(header);

            if (node.is_dir && node.children) {
                var children = document.createElement('div');
                children.className = 'tree-children collapsed';
                renderTree(node.children, children);
                nodeEl.appendChild(children);

                header.addEventListener('click', function(e) {
                    e.stopPropagation();
                    var isCollapsed = children.classList.contains('collapsed');
                    children.classList.toggle('collapsed');
                    toggle.textContent = isCollapsed ? '▼' : '▶';
                    icon.classList.toggle('open', isCollapsed);
                });
            }

            if (!node.is_dir) {
                header.addEventListener('click', function() {
                    document.querySelectorAll('.tree-node-header.selected').forEach(function(el) {
                        el.classList.remove('selected');
                    });
                    header.classList.add('selected');
                    if (node.supported) {
                        loadFile(node.path);
                    } else {
                        showToast('该文件格式暂不支持编辑', 'error');
                    }
                });
            }

            container.appendChild(nodeEl);
        });
    }

    function loadFileTree() {
        setLoading(true);
        fileTree.innerHTML = '<div class="tree-loading">加载中...</div>';

        fetch('/api/files/tree', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dir_key: currentDir })
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            setLoading(false);
            if (data.success) {
                renderTree(data.tree, fileTree);
            } else {
                fileTree.innerHTML = '<div class="tree-error">' + (data.error || '加载失败') + '</div>';
            }
        })
        .catch(function(err) {
            setLoading(false);
            fileTree.innerHTML = '<div class="tree-error">网络错误: ' + err.message + '</div>';
        });
    }

    // 文件读取
    function loadFile(fileFullPath) {
        setLoading(true);
        saveStatus.textContent = '';

        fetch('/api/files/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: fileFullPath })
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            setLoading(false);
            if (data.success) {
                currentFile = { path: data.path, mode: data.mode, encoding: data.encoding };
                originalContent = data.content;

                var parts = fileFullPath.split('/');
                var name = parts[parts.length - 1] || fileFullPath.split('\\').pop();
                fileName.textContent = name;
                filePath.textContent = fileFullPath;
                fileSize.textContent = formatSize(data.size);
                fileModified.textContent = '-';
                fileStatus.innerHTML = '<span style="color:#4ec9b0;">可编辑</span>';

                showEditor(data.content, data.mode);
                saveBtn.disabled = false;
                reloadBtn.disabled = false;
            } else {
                showToast(data.error || '读取失败', 'error');
                fileStatus.innerHTML = '<span style="color:#f48771;">' + (data.error || '错误') + '</span>';
            }
        })
        .catch(function(err) {
            setLoading(false);
            showToast('网络错误: ' + err.message, 'error');
        });
    }

    function showEditor(content, mode) {
        editorPlaceholder.style.display = 'none';
        aceEditor.style.display = 'block';

        if (!editor) {
            editor = ace.edit('aceEditor');
            editor.setTheme('ace/theme/monokai');
            editor.session.setMode('ace/mode/' + (mode || 'text'));
            editor.setOptions({
                fontSize: '13px',
                showPrintMargin: false,
                wrap: true,
                enableBasicAutocompletion: true
            });

            editor.session.on('change', function() {
                var isDirty = editor.getValue() !== originalContent;
                saveBtn.disabled = false;
                if (isDirty) {
                    saveStatus.textContent = '已修改';
                    saveStatus.className = 'save-status';
                }
            });
        } else {
            editor.session.setMode('ace/mode/' + (mode || 'text'));
        }

        editor.setValue(content, -1);
        editor.focus();
    }

    // 文件保存
    function saveFile() {
        if (!currentFile || !editor) return;

        var content = editor.getValue();
        saveStatus.textContent = '保存中...';
        saveStatus.className = 'save-status';

        fetch('/api/files/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: currentFile.path,
                content: content,
                encoding: currentFile.encoding || 'utf-8'
            })
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.success) {
                originalContent = content;
                saveStatus.textContent = '保存成功';
                saveStatus.className = 'save-status';
                showToast('保存成功', 'success');
            } else {
                saveStatus.textContent = '保存失败: ' + (data.error || '未知错误');
                saveStatus.className = 'save-status error';
                showToast('保存失败: ' + (data.error || '未知错误'), 'error');
            }
        })
        .catch(function(err) {
            saveStatus.textContent = '网络错误';
            saveStatus.className = 'save-status error';
            showToast('网络错误: ' + err.message, 'error');
        });
    }

    // 事件绑定
    dirSelect.addEventListener('change', function() {
        currentDir = this.value;
        loadFileTree();
    });

    refreshBtn.addEventListener('click', function() {
        loadFileTree();
    });

    saveBtn.addEventListener('click', saveFile);

    reloadBtn.addEventListener('click', function() {
        if (currentFile) loadFile(currentFile.path);
    });

    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            saveFile();
        }
    });

    // 初始化
    loadFileTree();

})();
