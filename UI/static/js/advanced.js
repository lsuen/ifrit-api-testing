/**
 * 高级模式 · 文件编辑器
 */
(function() {
    'use strict';
    var currentFile = null;
    var currentDir = 'fixtures';
    var editor = null;
    var originalContent = '';

    var dirSelect = document.getElementById('dirSelect');
    var refreshBtn = document.getElementById('refreshBtn');
    var fileTree = document.getElementById('fileTree');
    var fileName = document.getElementById('fileName');
    var editorPlaceholder = document.getElementById('editorPlaceholder');
    var aceEditor = document.getElementById('aceEditor');
    var saveBtn = document.getElementById('saveBtn');
    var saveStatus = document.getElementById('saveStatus');

    function renderTree(nodes, container) {
        container.innerHTML = '';
        if (!nodes || !nodes.length) {
            container.innerHTML = '<div class="text-muted p-2">目录为空</div>';
            return;
        }
        nodes.forEach(function(node) {
            var wrap = document.createElement('div');
            wrap.style.paddingLeft = '8px';
            if (node.is_dir) {
                var folder = document.createElement('div');
                folder.className = 'text-warning py-1';
                folder.innerHTML = '<i class="bi bi-folder"></i> ' + node.name;
                wrap.appendChild(folder);
                if (node.children) {
                    var child = document.createElement('div');
                    renderTree(node.children, child);
                    wrap.appendChild(child);
                }
            } else {
                var file = document.createElement('div');
                file.className = 'py-1 text-light';
                file.style.cursor = node.supported ? 'pointer' : 'not-allowed';
                file.style.opacity = node.supported ? '1' : '0.5';
                file.innerHTML = '<i class="bi bi-file-earmark"></i> ' + node.name;
                if (node.supported) {
                    file.addEventListener('click', function() { loadFile(node.path); });
                }
                wrap.appendChild(file);
            }
            container.appendChild(wrap);
        });
    }

    function loadDirOptions() {
        fetch('/api/dirs').then(function(r) { return r.json(); }).then(function(data) {
            dirSelect.innerHTML = '';
            if (!data.dirs || !data.dirs.length) {
                dirSelect.innerHTML = '<option value="">获取不到可用目录</option>';
                fileTree.innerHTML = '<div class="text-muted p-2">获取不到</div>';
                return;
            }
            data.dirs.forEach(function(d, i) {
                var opt = document.createElement('option');
                opt.value = d.key;
                opt.textContent = d.name;
                dirSelect.appendChild(opt);
                if (i === 0) currentDir = d.key;
            });
            loadFileTree();
        }).catch(function() {
            dirSelect.innerHTML = '<option value="">获取不到</option>';
            fileTree.innerHTML = '<div class="text-muted p-2">目录列表加载失败</div>';
        });
    }

    function loadFileTree() {
        if (!currentDir) return;
        fileTree.innerHTML = '<div class="text-muted p-2">加载中...</div>';
        fetch('/api/files/tree', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dir_key: currentDir })
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (data.success) renderTree(data.tree, fileTree);
            else fileTree.innerHTML = '<div class="text-danger p-2">' + data.error + '</div>';
        });
    }

    function loadFile(path) {
        fetch('/api/files/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (!data.success) return alert(data.error);
            currentFile = data;
            originalContent = data.content;
            fileName.textContent = path.split(/[/\\]/).pop();
            showEditor(data.content, data.mode);
            saveBtn.disabled = false;
        });
    }

    function showEditor(content, mode) {
        editorPlaceholder.style.display = 'none';
        aceEditor.style.display = 'block';
        if (!editor) {
            editor = ace.edit('aceEditor');
            editor.setTheme('ace/theme/monokai');
            editor.setOptions({ fontSize: '13px', showPrintMargin: false, wrap: true });
        }
        editor.session.setMode('ace/mode/' + (mode || 'text'));
        editor.setValue(content, -1);
    }

    function saveFile() {
        if (!currentFile || !editor) return;
        fetch('/api/files/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: currentFile.path,
                content: editor.getValue(),
                encoding: currentFile.encoding || 'utf-8'
            })
        }).then(function(r) { return r.json(); }).then(function(data) {
            saveStatus.textContent = data.success ? '已保存' : data.error;
            if (data.success) originalContent = editor.getValue();
        });
    }

    dirSelect.addEventListener('change', function() { currentDir = this.value; loadFileTree(); });
    refreshBtn.addEventListener('click', loadFileTree);
    saveBtn.addEventListener('click', saveFile);
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); saveFile(); }
    });
    loadDirOptions();
})();
