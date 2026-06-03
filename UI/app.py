#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：ifrit API 自动化测试平台 Web UI
"""
import sys
from pathlib import Path

UI_DIR = Path(__file__).parent.absolute()
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

import json
import os
from typing import Any, Dict, List

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    send_file,
    stream_with_context,
)
from werkzeug.utils import secure_filename

from services.cli_runner import (
    build_ai_chat_command,
    build_ai_generate_command,
    build_clean_command,
    build_import_command,
    build_simple_command,
    build_test_command,
    process_manager,
)
from services.config_loader import (
    UNAVAILABLE,
    get_preset_status,
    get_remote_swagger_url,
    load_auth_summary,
    load_config,
    load_environment_options,
    load_environments,
    project_path,
)
from services.file_service import ACE_MODE_MAP, build_file_tree, read_file_content, save_file_content
from services.ifrit_paths import (
    dashboard_stats,
    list_api_docs,
    list_report_runs,
    list_test_files,
)

CONFIG: Dict[str, Any] = {}


def create_app() -> Flask:
    application = Flask(__name__)
    application.config["JSON_AS_ASCII"] = False
    register_routes(application)
    return application


def register_routes(app: Flask) -> None:
    @app.route("/")
    def dashboard():
        stats = dashboard_stats(CONFIG)
        auth = load_auth_summary(CONFIG)
        env_options = load_environment_options(CONFIG)
        base_url = env_options[0]["base_url"] if env_options else UNAVAILABLE
        return render_template(
            "dashboard.html",
            stats=stats,
            auth=auth,
            base_url=base_url,
            env_options=env_options,
            unavailable=UNAVAILABLE,
            presets=CONFIG.get("presets", {}),
        )

    @app.route("/execute")
    def execute_page():
        envs = load_environments(CONFIG)
        root = project_path(CONFIG, "fixtures")
        project_root = CONFIG["ifrit"]["root_path_resolved"]
        files = list_test_files(root, project_root=project_root)
        presets = CONFIG.get("presets", {})
        preset_status = get_preset_status(CONFIG)
        return render_template(
            "execute.html",
            environments=envs,
            files=files,
            presets=presets,
            preset_status=preset_status,
            auth=load_auth_summary(CONFIG),
            unavailable=UNAVAILABLE,
        )

    @app.route("/import")
    def import_page():
        root = CONFIG["ifrit"]["root_path_resolved"]
        sample_rel = "tests/fixtures/postman/ifrit_address_smoke.postman_collection.json"
        sample_path = sample_rel if (root / sample_rel).is_file() else None
        return render_template(
            "import.html",
            sample_path=sample_path,
        )

    @app.route("/ai")
    def ai_page():
        docs = list_api_docs(CONFIG)
        default_doc = docs[0]["relative"] if docs else None
        swagger_url = get_remote_swagger_url(CONFIG)
        root = CONFIG["ifrit"]["root_path_resolved"]
        output_dir = "fixtures/ai/csv"
        ai_csv = root / "fixtures" / "ai" / "csv"
        if ai_csv.is_dir():
            try:
                output_dir = str(ai_csv.relative_to(root)).replace("\\", "/")
            except ValueError:
                pass
        return render_template(
            "ai.html",
            docs=docs,
            default_doc=default_doc,
            swagger_url=swagger_url,
            default_output_dir=output_dir,
            auth=load_auth_summary(CONFIG),
            unavailable=UNAVAILABLE,
        )

    @app.route("/reports")
    def reports_page():
        runs = list_report_runs(CONFIG)
        return render_template("reports.html", runs=runs)

    @app.route("/advanced")
    def advanced_page():
        return render_template("advanced.html")

    @app.route("/reports/view/<run_id>")
    def view_report(run_id: str):
        runs_dir = project_path(CONFIG, "reports_runs")
        index_path = runs_dir / run_id / "html" / "index.html"
        if not index_path.is_file():
            return jsonify({"error": "报告不存在"}), 404
        return send_file(index_path)

    @app.route("/api/overview")
    def api_overview():
        env_options = load_environment_options(CONFIG)
        return jsonify(
            {
                "stats": dashboard_stats(CONFIG),
                "auth": load_auth_summary(CONFIG),
                "environments": load_environments(CONFIG),
                "environment_options": env_options,
                "swagger_url": get_remote_swagger_url(CONFIG),
                "presets": get_preset_status(CONFIG),
            }
        )

    @app.route("/api/files/list", methods=["POST"])
    def api_files_list():
        data = request.json or {}
        suite = data.get("suite", "all")
        root = CONFIG["ifrit"]["root_path_resolved"] / "fixtures"
        if suite == "manual":
            scan = root / "manual"
        elif suite == "ai":
            scan = root / "ai"
        elif suite == "smoke":
            scan = root / "smoke"
        else:
            scan = root
        return jsonify({"files": list_test_files(scan, project_root=CONFIG["ifrit"]["root_path_resolved"])})

    @app.route("/api/execute", methods=["POST"])
    def api_execute():
        data = request.json or {}
        params = data.get("params", {})
        cmd = build_test_command(CONFIG, params)
        process_id = process_manager.start(cmd, CONFIG["ifrit"]["root_path_resolved"], label="test_run")
        return jsonify({"process_id": process_id, "command": " ".join(cmd)})

    @app.route("/api/ai/generate", methods=["POST"])
    def api_ai_generate():
        data = request.json or {}
        cmd = build_ai_generate_command(CONFIG, data)
        if "--input-doc" not in cmd and "--input-url" not in cmd:
            return jsonify({"error": "请提供文档路径或 URL"}), 400
        process_id = process_manager.start(cmd, CONFIG["ifrit"]["root_path_resolved"], label="ai_generate")
        return jsonify({"process_id": process_id, "command": " ".join(cmd)})

    @app.route("/api/ai/chat", methods=["POST"])
    def api_ai_chat():
        data = request.json or {}
        chat_args = data.get("commands") or []
        if isinstance(chat_args, str):
            chat_args = chat_args.split()
        if not chat_args:
            return jsonify({"error": "请提供交互命令，如 doc api_docs/apispec_1.json endpoint /api/address generate"}), 400
        cmd = build_ai_chat_command(CONFIG, chat_args)
        process_id = process_manager.start(cmd, CONFIG["ifrit"]["root_path_resolved"], label="ai_chat")
        return jsonify({"process_id": process_id, "command": " ".join(cmd)})

    @app.route("/api/import", methods=["POST"])
    def api_import():
        root = CONFIG["ifrit"]["root_path_resolved"]
        import_rel = ""
        output_file = ""

        if request.files.get("file"):
            upload = request.files["file"]
            filename = secure_filename(upload.filename or "collection.json")
            if not filename.lower().endswith(".json"):
                return jsonify({"error": "仅支持 Postman JSON 文件"}), 400
            save_dir = root / "fixtures" / "import" / "postman"
            save_dir.mkdir(parents=True, exist_ok=True)
            save_path = save_dir / filename
            upload.save(save_path)
            import_rel = str(save_path.relative_to(root)).replace("\\", "/")
        else:
            source_path = (request.form.get("source_path") or "").strip()
            if not source_path:
                return jsonify({"error": "请上传 Postman 文件或指定 source_path"}), 400
            candidate = Path(source_path)
            if not candidate.is_absolute():
                candidate = root / source_path.replace("/", os.sep)
            if not candidate.is_file():
                return jsonify({"error": f"文件不存在: {source_path}"}), 400
            import_rel = str(candidate.relative_to(root)).replace("\\", "/")

        suite = request.form.get("suite", "manual")
        output = (request.form.get("output") or "").strip()
        dry_run = request.form.get("dry_run") in ("1", "true", "True", "on")
        ai_enhance = request.form.get("ai_enhance") in ("1", "true", "True", "on")

        params: Dict[str, Any] = {
            "import_file": import_rel,
            "format": request.form.get("format", "postman"),
            "suite": suite,
            "dry_run": dry_run,
            "ai_enhance": ai_enhance,
        }
        if output:
            out_path = Path(output)
            if not out_path.is_absolute():
                out_path = root / output.replace("/", os.sep)
            params["output"] = str(out_path.relative_to(root)).replace("\\", "/")
            if not dry_run:
                output_file = params["output"]

        try:
            cmd = build_import_command(CONFIG, params)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        process_id = process_manager.start(cmd, root, label="import_postman")
        return jsonify(
            {
                "process_id": process_id,
                "command": " ".join(cmd),
                "output_file": output_file,
            }
        )

    @app.route("/api/reports/generate", methods=["POST"])
    def api_reports_generate():
        cmd = build_simple_command(CONFIG, "--generate-report")
        process_id = process_manager.start(cmd, CONFIG["ifrit"]["root_path_resolved"], label="generate_report")
        return jsonify({"process_id": process_id})

    @app.route("/api/reports/serve", methods=["POST"])
    def api_reports_serve():
        cmd = build_simple_command(CONFIG, "--serve-report")
        process_id = process_manager.start(cmd, CONFIG["ifrit"]["root_path_resolved"], label="serve_report")
        return jsonify({"process_id": process_id})

    @app.route("/api/clean", methods=["POST"])
    def api_clean():
        data = request.json or {}
        target = data.get("target", "all")
        cmd = build_clean_command(
            CONFIG,
            target=target,
            keep_days=data.get("keep_days"),
            dry_run=data.get("dry_run", False),
        )
        process_id = process_manager.start(cmd, CONFIG["ifrit"]["root_path_resolved"], label="clean")
        return jsonify({"process_id": process_id, "command": " ".join(cmd)})

    @app.route("/api/process/<process_id>/status")
    def api_process_status(process_id: str):
        status = process_manager.get_status(process_id)
        if not status:
            return jsonify({"error": "进程不存在"}), 404
        return jsonify(status)

    @app.route("/api/process/<process_id>/stream")
    def api_process_stream(process_id: str):
        def generate():
            for chunk in process_manager.stream_events(process_id):
                yield chunk

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.route("/api/process/<process_id>/cancel", methods=["POST"])
    def api_process_cancel(process_id: str):
        if process_manager.cancel(process_id):
            return jsonify({"success": True})
        return jsonify({"error": "无法取消"}), 404

    @app.route("/api/files/tree", methods=["POST"])
    def api_file_tree():
        data = request.json or {}
        dir_key = data.get("dir_key", "fixtures")
        dir_path = project_path(CONFIG, dir_key)
        if not dir_path.is_dir():
            return jsonify({"error": f"目录不存在: {dir_path}"}), 404
        return jsonify({"success": True, "dir": str(dir_path), "tree": build_file_tree(dir_path)})

    @app.route("/api/files/read", methods=["POST"])
    def api_file_read():
        data = request.json or {}
        file_path = data.get("path")
        if not file_path:
            return jsonify({"error": "缺少 path"}), 400
        success, content, encoding = read_file_content(Path(file_path))
        if not success:
            return jsonify({"success": False, "error": content}), 400
        ext = Path(file_path).suffix.lower()
        return jsonify(
            {
                "success": True,
                "content": content,
                "encoding": encoding,
                "mode": ACE_MODE_MAP.get(ext, "text"),
                "path": file_path,
            }
        )

    @app.route("/api/files/save", methods=["POST"])
    def api_file_save():
        data = request.json or {}
        file_path = data.get("path")
        content = data.get("content")
        encoding = data.get("encoding", "utf-8")
        if not file_path or content is None:
            return jsonify({"error": "缺少参数"}), 400
        success, message = save_file_content(Path(file_path), content, encoding)
        if success:
            return jsonify({"success": True, "message": message})
        return jsonify({"success": False, "error": message}), 400

    @app.route("/api/dirs")
    def api_dirs():
        dirs = []
        for key, value in CONFIG["paths"].items():
            path = project_path(CONFIG, key)
            if path.exists():
                dirs.append({"key": key, "name": value, "path": str(path)})
        return jsonify({"dirs": dirs})


app = create_app()


def init_app_config() -> None:
    global CONFIG
    CONFIG = load_config()


init_app_config()


if __name__ == "__main__":
    try:
        init_app_config()
        server = CONFIG["server"]
        print("\n" + "=" * 60)
        print("ifrit API 自动化测试平台")
        print(f"项目: {CONFIG['ifrit']['root_path_resolved']}")
        print(f"访问: http://127.0.0.1:{server['port']}")
        print("=" * 60 + "\n")
        app.run(host=server["host"], port=server["port"], debug=server["debug"], threaded=True)
    except Exception as error:
        print(f"启动失败: {error}", file=sys.stderr)
        sys.exit(1)
