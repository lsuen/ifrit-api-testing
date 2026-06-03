#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CLI 进程管理与 SSE 日志流。"""
import json
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Dict, Generator, List, Optional


@dataclass
class ProcessRecord:
    process_id: str
    command: List[str]
    label: str
    cwd: Path
    process: subprocess.Popen
    queue: Queue = field(default_factory=Queue)
    status: str = "running"
    exit_code: Optional[int] = None
    started_at: float = field(default_factory=time.time)
    output_lines: int = 0
    report_path: Optional[str] = None


class ProcessManager:
    """管理 subprocess 生命周期与日志队列。"""

    def __init__(self):
        self._records: Dict[str, ProcessRecord] = {}
        self._lock = threading.Lock()

    def start(self, command: List[str], cwd: Path, label: str = "task") -> str:
        process_id = uuid.uuid4().hex[:12]
        proc = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        record = ProcessRecord(
            process_id=process_id,
            command=command,
            label=label,
            cwd=cwd,
            process=proc,
        )
        with self._lock:
            self._records[process_id] = record

        thread = threading.Thread(target=self._read_output, args=(record,), daemon=True)
        thread.start()
        watcher = threading.Thread(target=self._watch_process, args=(record,), daemon=True)
        watcher.start()
        return process_id

    @staticmethod
    def _read_output(record: ProcessRecord) -> None:
        if record.process.stdout is None:
            return
        for line in record.process.stdout:
            text = line.rstrip("\n\r")
            record.output_lines += 1
            record.queue.put({"type": "log", "line": text})

    def _watch_process(self, record: ProcessRecord) -> None:
        exit_code = record.process.wait()
        record.exit_code = exit_code
        record.status = "completed" if exit_code == 0 else "failed"
        record.queue.put(
            {
                "type": "status",
                "status": record.status,
                "exit_code": exit_code,
            }
        )
        record.queue.put({"type": "done"})

    def get_status(self, process_id: str) -> Optional[Dict[str, Any]]:
        record = self._records.get(process_id)
        if not record:
            return None
        return {
            "process_id": process_id,
            "label": record.label,
            "status": record.status,
            "exit_code": record.exit_code,
            "output_lines": record.output_lines,
            "command": " ".join(record.command),
            "started_at": record.started_at,
            "report_path": record.report_path,
        }

    def cancel(self, process_id: str) -> bool:
        record = self._records.get(process_id)
        if not record or record.status != "running":
            return False
        record.process.terminate()
        try:
            record.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            record.process.kill()
        record.status = "cancelled"
        record.queue.put({"type": "status", "status": "cancelled", "exit_code": -1})
        record.queue.put({"type": "done"})
        return True

    def stream_events(self, process_id: str, timeout: float = 0.5) -> Generator[str, None, None]:
        record = self._records.get(process_id)
        if not record:
            yield f"data: {json.dumps({'type': 'error', 'message': '进程不存在'}, ensure_ascii=False)}\n\n"
            return

        while True:
            try:
                event = record.queue.get(timeout=timeout)
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event.get("type") == "done":
                    break
            except Empty:
                if record.process.poll() is not None and record.queue.empty():
                    yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                    break
                yield f": keepalive\n\n"


process_manager = ProcessManager()


def build_python_cmd(config: Dict[str, Any]) -> List[str]:
    python_bin = config["ifrit"].get("python_bin", "python")
    return [python_bin]


def build_main_script(config: Dict[str, Any]) -> Path:
    root = config["ifrit"]["root_path_resolved"]
    return root / config["ifrit"].get("cli_script", "main.py")


def build_test_command(config: Dict[str, Any], params: Dict[str, Any]) -> List[str]:
    root = config["ifrit"]["root_path_resolved"]
    cmd = build_python_cmd(config) + [str(build_main_script(config))]

    test_file = params.get("file")
    suite = params.get("suite")
    test_type = params.get("type")

    if test_file:
        rel = Path(test_file)
        if rel.is_absolute():
            try:
                test_file = str(rel.relative_to(root))
            except ValueError:
                test_file = str(rel)
        cmd.extend(["--file", test_file.replace("\\", "/")])
    elif test_type:
        cmd.extend(["--type", test_type])
        if suite:
            cmd.extend(["--suite", suite])

    env = params.get("env")
    if env:
        cmd.extend(["--env", env])

    if params.get("global_auth"):
        cmd.append("--global-auth")

    if params.get("generate_report"):
        cmd.append("--generate-report")

    return cmd


def build_ai_generate_command(config: Dict[str, Any], params: Dict[str, Any]) -> List[str]:
    cmd = build_python_cmd(config) + [str(build_main_script(config)), "--ai-generate"]

    input_doc = params.get("input_doc")
    input_url = params.get("input_url")
    if input_url:
        cmd.extend(["--input-url", input_url])
    elif input_doc:
        root = config["ifrit"]["root_path_resolved"]
        path = Path(input_doc)
        if path.is_absolute():
            try:
                input_doc = str(path.relative_to(root)).replace("\\", "/")
            except ValueError:
                input_doc = str(path)
        cmd.extend(["--input-doc", input_doc])

    for endpoint in params.get("endpoints") or []:
        if endpoint.strip():
            cmd.extend(["--swagger-endpoint", endpoint.strip()])

    output_format = params.get("format", "csv")
    cmd.extend(["--output-format", output_format])

    output_dir = params.get("output_dir")
    if output_dir:
        cmd.extend(["--output-dir", output_dir.replace("\\", "/")])

    skill = params.get("skill")
    if skill:
        cmd.extend(["--skill", skill])

    return cmd


def build_ai_chat_command(config: Dict[str, Any], chat_args: List[str]) -> List[str]:
    cmd = build_python_cmd(config) + [str(build_main_script(config)), "--chat"]
    if chat_args:
        cmd.extend(chat_args)
    return cmd


def build_simple_command(config: Dict[str, Any], flag: str) -> List[str]:
    return build_python_cmd(config) + [str(build_main_script(config)), flag]


def build_clean_command(config: Dict[str, Any], target: str, keep_days: Optional[int] = None, dry_run: bool = False) -> List[str]:
    cmd = build_python_cmd(config) + [str(build_main_script(config)), "--clean", target]
    if keep_days is not None:
        cmd.extend(["--keep-days", str(keep_days)])
    if dry_run:
        cmd.append("--dry-run")
    return cmd


def build_import_command(config: Dict[str, Any], params: Dict[str, Any]) -> List[str]:
    root = config["ifrit"]["root_path_resolved"]
    import_file = params.get("import_file")
    if not import_file:
        raise ValueError("缺少 import_file")

    rel = Path(import_file)
    if rel.is_absolute():
        try:
            import_file = str(rel.relative_to(root)).replace("\\", "/")
        except ValueError:
            import_file = str(rel).replace("\\", "/")
    else:
        import_file = str(import_file).replace("\\", "/")

    cmd = build_python_cmd(config) + [
        str(build_main_script(config)),
        "--import",
        import_file,
        "--import-format",
        params.get("format", "postman"),
        "--import-suite",
        params.get("suite", "manual"),
    ]
    if params.get("output"):
        cmd.extend(["--import-output", str(params["output"]).replace("\\", "/")])
    if params.get("dry_run"):
        cmd.append("--import-dry-run")
    if params.get("ai_enhance"):
        cmd.append("--import-ai-enhance")
    return cmd
