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
import mimetypes
import os
from typing import Any, Dict, List

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    redirect,
    send_file,
    stream_with_context,
)
from werkzeug.utils import secure_filename

from services.cli_runner import (
    build_ai_chat_command,
    build_ai_generate_command,
    build_clean_command,
    build_import_command,
    build_import_diagnose_command,
    build_console_exec_command,
    build_console_help_command,
    build_simple_command,
    build_skills_refresh_command,
    build_test_command,
    process_manager,
)
from services.console_service import load_console_policy, validate_console_line
from services.docs_service import get_cli_docs, get_manual_markdown, get_project_info
from services.import_bridge import get_project_context, preview_import, preview_postman, save_merged_cases
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
from services.skills_bridge import (
    add_repo_url,
    enable,
    get_actions_catalog,
    get_builtin_skills,
    get_catalog,
    get_repos,
    install,
    read_editor,
    remove_repo_by_id,
    save_editor,
    uninstall,
)
from services.ifrit_paths import (
    dashboard_stats,
    list_api_docs,
    delete_report_run,
    generate_run_html_report,
    list_report_runs,
    resolve_report_html_file,
    list_test_files,
)
from services.settings_service import (
    get_settings_payload,
    ingest_case_file_to_rag,
    run_health_check,
    save_ai_settings,
    save_auth_settings,
    save_env_entry,
    save_ui_prefs,
)
from services.agent_dialog_service import build_agent_plan, get_agent_context

CONFIG: Dict[str, Any] = {}


def _resolve_import_file(root: Path) -> str:
    import_format = "postman"
    if request.form:
        import_format = (request.form.get("format") or "postman").lower()
    body = request.get_json(silent=True) or {}
    if body.get("format"):
        import_format = str(body.get("format")).lower()

    allowed_suffix = {".json"} if import_format == "postman" else {".json", ".csv"}
    subdir = "postman" if import_format == "postman" else "native"

    if request.files.get("file"):
        upload = request.files["file"]
        filename = secure_filename(upload.filename or "import.json")
        suffix = Path(filename).suffix.lower()
        if suffix not in allowed_suffix:
            raise ValueError(f"当前格式 {import_format} 不支持该扩展名: {suffix}")
        save_dir = root / "fixtures" / "import" / subdir
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / filename
        upload.save(save_path)
        return str(save_path.relative_to(root)).replace("\\", "/")

    source_path = (request.form.get("source_path") or "").strip() if request.form else ""
    if not source_path:
        source_path = str(body.get("source_path") or body.get("import_file") or "").strip()
    if not source_path:
        raise ValueError("请上传文件或指定 source_path")
    candidate = Path(source_path)
    if not candidate.is_absolute():
        candidate = root / source_path.replace("/", os.sep)
    if not candidate.is_file():
        raise ValueError(f"文件不存在: {source_path}")
    return str(candidate.relative_to(root)).replace("\\", "/")


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
        docs = list_api_docs(CONFIG)
        default_doc = docs[0]["relative"] if docs else None
        root = CONFIG["ifrit"]["root_path_resolved"]
        default_output_dir = "fixtures/ai/csv"
        ai_csv = root / "fixtures" / "ai" / "csv"
        if ai_csv.is_dir():
            try:
                default_output_dir = str(ai_csv.relative_to(root)).replace("\\", "/")
            except ValueError:
                pass
        sample_import = "tests/fixtures/postman/ifrit_address_smoke.postman_collection.json"
        if not (root / sample_import).is_file():
            sample_import = None
        return render_template(
            "dashboard.html",
            stats=stats,
            auth=auth,
            base_url=base_url,
            env_options=env_options,
            unavailable=UNAVAILABLE,
            presets=CONFIG.get("presets", {}),
            preset_status=get_preset_status(CONFIG),
            default_doc=default_doc,
            default_output_dir=default_output_dir,
            sample_import=sample_import,
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

    @app.route("/about")
    def about_page():
        return render_template("about.html")

    @app.route("/skills")
    def skills_page():
        return render_template("skills.html")

    @app.route("/console")
    def console_page():
        return render_template("console.html")

    @app.route("/knowledge")
    def knowledge_page():
        return render_template("knowledge.html")

    @app.route("/settings")
    def settings_page():
        return render_template("settings.html")

    @app.route("/agent")
    def agent_page():
        docs = list_api_docs(CONFIG)
        default_doc = docs[0]["relative"] if docs else None
        return render_template(
            "agent.html",
            docs=docs,
            default_doc=default_doc,
            builtin_skills=get_builtin_skills(),
        )

    @app.route("/api/agent/plan", methods=["POST"])
    def api_agent_plan():
        data = request.json or {}
        try:
            plan = build_agent_plan(CONFIG, data)
            return jsonify(plan)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/agent/context")
    def api_agent_context():
        return jsonify(get_agent_context(CONFIG))

    @app.route("/api/settings")
    def api_settings_get():
        try:
            return jsonify(get_settings_payload(CONFIG))
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/settings/health", methods=["POST"])
    def api_settings_health():
        data = request.json or {}
        ping_llm = bool(data.get("ping_llm"))
        try:
            return jsonify(run_health_check(CONFIG, ping_llm=ping_llm))
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/settings/ai", methods=["POST"])
    def api_settings_ai():
        data = request.json or {}
        try:
            save_ai_settings(CONFIG, data)
            return jsonify({"success": True})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/settings/env", methods=["POST"])
    def api_settings_env():
        data = request.json or {}
        name = (data.get("name") or "").strip()
        base_url = (data.get("base_url") or "").strip()
        if not name or not base_url:
            return jsonify({"error": "请填写环境名与 Base URL"}), 400
        try:
            save_env_entry(CONFIG, name, base_url, str(data.get("timeout") or "30"))
            return jsonify({"success": True})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/settings/auth", methods=["POST"])
    def api_settings_auth():
        data = request.json or {}
        try:
            save_auth_settings(CONFIG, data)
            return jsonify({"success": True})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/settings/prefs", methods=["POST"])
    def api_settings_prefs():
        data = request.json or {}
        try:
            prefs = save_ui_prefs(CONFIG, data)
            return jsonify({"success": True, "ui_prefs": prefs})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/settings/rag/ingest-case", methods=["POST"])
    def api_settings_rag_ingest_case():
        data = request.json or {}
        rel_path = (data.get("path") or "").strip()
        if not rel_path:
            return jsonify({"error": "缺少 path"}), 400
        try:
            doc_id = ingest_case_file_to_rag(CONFIG, rel_path)
            return jsonify({"success": True, "doc_id": doc_id, "ingested": doc_id is not None})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    def _core_knowledge():
        root = CONFIG["ifrit"]["root_path_resolved"]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from core.rag.service import KnowledgeService

        return KnowledgeService(str(root))

    @app.route("/api/knowledge/stats")
    def api_knowledge_stats():
        try:
            return jsonify({"success": True, "stats": _core_knowledge().stats()})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/knowledge/documents")
    def api_knowledge_documents():
        try:
            limit = int(request.args.get("limit", 100))
            return jsonify({"success": True, "documents": _core_knowledge().list_documents(limit)})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/knowledge/search", methods=["POST"])
    def api_knowledge_search():
        data = request.json or {}
        query = (data.get("query") or "").strip()
        if not query:
            return jsonify({"error": "缺少 query"}), 400
        try:
            service = _core_knowledge()
            top_k = int(data.get("top_k", 5))
            hits = service.search(query, top_k=top_k, source_types=data.get("source_types"))
            from core.rag.retrieve import format_hits

            return jsonify({"success": True, "hits": hits, "formatted": format_hits(hits)})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/knowledge/rebuild", methods=["POST"])
    def api_knowledge_rebuild():
        root = CONFIG["ifrit"]["root_path_resolved"]
        cmd = build_simple_command(CONFIG, "--rag-rebuild")
        cmd.extend(["--project-root", str(root).replace("\\", "/")])
        process_id = process_manager.start(cmd, root, label="rag_rebuild")
        return jsonify({"process_id": process_id, "command": " ".join(cmd)})

    @app.route("/api/knowledge/ingest", methods=["POST"])
    def api_knowledge_ingest():
        root = CONFIG["ifrit"]["root_path_resolved"]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from core.rag.service import KnowledgeService

        service = KnowledgeService(str(root))
        source_type = "requirement"
        try:
            if request.files.get("file"):
                upload = request.files["file"]
                filename = secure_filename(upload.filename or "doc.md")
                content = upload.read().decode("utf-8", errors="ignore")
                source_type = request.form.get("source_type", "requirement")
                doc_id, rel = service.ingest_upload(filename, content, source_type=source_type)
                return jsonify({"success": True, "doc_id": doc_id, "path": rel})
            data = request.get_json(silent=True) or {}
            text = (data.get("text") or "").strip()
            if not text:
                return jsonify({"error": "请上传文件或提供 text"}), 400
            title = (data.get("title") or "paste_input.md").strip()
            source_type = data.get("source_type", "requirement")
            doc_id, rel = service.ingest_upload(title, text, source_type=source_type)
            return jsonify({"success": True, "doc_id": doc_id, "path": rel})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/knowledge/documents/<int:doc_id>", methods=["DELETE"])
    def api_knowledge_delete(doc_id: int):
        try:
            _core_knowledge().delete_document(doc_id)
            return jsonify({"success": True})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/cases/catalog")
    def api_cases_catalog():
        root = CONFIG["ifrit"]["root_path_resolved"]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from core.case_catalog import list_case_files

        suite = request.args.get("suite")
        try:
            files = list_case_files(root, suite=suite or None)
            return jsonify({"success": True, "files": files})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/console/policy")
    def api_console_policy():
        policy = load_console_policy()
        return jsonify({"success": True, "policy": policy})

    @app.route("/api/console/validate", methods=["POST"])
    def api_console_validate():
        data = request.json or {}
        mode = data.get("mode", "cli")
        line = data.get("line", "")
        ok, level, message = validate_console_line(mode, line)
        return jsonify({"ok": ok, "level": level, "message": message})

    @app.route("/api/console/help", methods=["POST"])
    def api_console_help():
        data = request.json or {}
        mode = data.get("mode", "cli")
        root = CONFIG["ifrit"]["root_path_resolved"]
        cmd = build_console_help_command(CONFIG, mode)
        process_id = process_manager.start(cmd, root, label="console_help")
        return jsonify({"process_id": process_id, "command": " ".join(cmd)})

    @app.route("/api/console/exec", methods=["POST"])
    def api_console_exec():
        data = request.json or {}
        mode = data.get("mode", "cli")
        line = (data.get("line") or "").strip()
        ok, level, message = validate_console_line(mode, line)
        if not ok:
            return jsonify({"error": message}), 400
        root = CONFIG["ifrit"]["root_path_resolved"]
        try:
            cmd = build_console_exec_command(CONFIG, mode, line)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        process_id = process_manager.start(cmd, root, label="console_exec")
        return jsonify({
            "process_id": process_id,
            "command": " ".join(cmd),
            "warn": message if level == "warn" else "",
        })

    @app.route("/api/test/assist", methods=["POST"])
    def api_test_assist():
        """根据日志文本做 AI 辅助分析（不自动保存）。"""
        import sys
        from pathlib import Path as _Path

        root = CONFIG["ifrit"]["root_path_resolved"]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from core.test_assist import analyze_test_output

        data = request.json or {}
        log_text = data.get("log_text") or ""
        if not log_text.strip():
            return jsonify({"error": "缺少 log_text"}), 400
        try:
            result = analyze_test_output(
                log_text,
                "",
                run_id=data.get("run_id"),
                suite=data.get("suite"),
            )
            return jsonify({"success": True, "assist": result, "retain_decision": "user"})
        except Exception as error:
            return jsonify({"error": str(error)}), 400

    @app.route("/api/test/assist/save", methods=["POST"])
    def api_test_assist_save():
        """用户确认留存 AI 辅助建议。"""
        import sys

        root = CONFIG["ifrit"]["root_path_resolved"]
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from core.test_assist import save_assist_report

        data = request.json or {}
        run_id = (data.get("run_id") or "").strip()
        payload = data.get("assist")
        if not payload:
            return jsonify({"error": "缺少 assist 数据"}), 400
        try:
            path = save_assist_report(str(root), run_id, payload)
            return jsonify({"success": True, "path": path})
        except Exception as error:
            return jsonify({"error": str(error)}), 400

    @app.route("/api/skills/builtin")
    def api_skills_builtin():
        return jsonify({"success": True, "skills": get_builtin_skills()})

    @app.route("/api/skills/repos")
    def api_skills_repos():
        root = CONFIG["ifrit"]["root_path_resolved"]
        return jsonify({"success": True, "repos": get_repos(root)})

    @app.route("/api/skills/repos", methods=["POST"])
    def api_skills_add_repo():
        root = CONFIG["ifrit"]["root_path_resolved"]
        data = request.json or {}
        url = (data.get("url") or "").strip()
        branch = (data.get("branch") or "main").strip()
        if not url:
            return jsonify({"error": "请提供仓库 URL"}), 400
        try:
            repo = add_repo_url(root, url, branch)
            return jsonify({"success": True, "repo": repo})
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    @app.route("/api/skills/repos/<repo_id>", methods=["DELETE"])
    def api_skills_remove_repo(repo_id: str):
        root = CONFIG["ifrit"]["root_path_resolved"]
        if remove_repo_by_id(root, repo_id):
            return jsonify({"success": True})
        return jsonify({"error": "仓库不存在"}), 404

    @app.route("/api/skills/catalog")
    def api_skills_catalog():
        root = CONFIG["ifrit"]["root_path_resolved"]
        query = request.args.get("q", "")
        return jsonify({"success": True, "items": get_catalog(root, query=query)})

    @app.route("/api/skills/refresh", methods=["POST"])
    def api_skills_refresh():
        root = CONFIG["ifrit"]["root_path_resolved"]
        data = request.json or {}
        cmd = build_skills_refresh_command(CONFIG, repo_id=data.get("repo_id"))
        process_id = process_manager.start(cmd, root, label="skills_refresh")
        return jsonify({"process_id": process_id, "command": " ".join(cmd)})

    @app.route("/api/skills/install", methods=["POST"])
    def api_skills_install():
        root = CONFIG["ifrit"]["root_path_resolved"]
        data = request.json or {}
        skill_id = (data.get("skill_id") or "").strip()
        if not skill_id:
            return jsonify({"error": "缺少 skill_id"}), 400
        try:
            path = install(root, skill_id)
            return jsonify({"success": True, "path": path})
        except Exception as error:
            return jsonify({"error": str(error)}), 400

    @app.route("/api/skills/uninstall", methods=["POST"])
    def api_skills_uninstall():
        root = CONFIG["ifrit"]["root_path_resolved"]
        data = request.json or {}
        skill_id = (data.get("skill_id") or "").strip()
        if not skill_id:
            return jsonify({"error": "缺少 skill_id"}), 400
        uninstall(root, skill_id)
        return jsonify({"success": True})

    @app.route("/api/skills/enable", methods=["POST"])
    def api_skills_enable():
        root = CONFIG["ifrit"]["root_path_resolved"]
        data = request.json or {}
        skill_id = (data.get("skill_id") or "").strip()
        enabled = bool(data.get("enabled"))
        if not skill_id:
            return jsonify({"error": "缺少 skill_id"}), 400
        try:
            enable(root, skill_id, enabled)
            return jsonify({"success": True})
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    @app.route("/api/skills/editor/<skill_id>")
    def api_skills_editor_read(skill_id: str):
        root = CONFIG["ifrit"]["root_path_resolved"]
        try:
            data = read_editor(root, skill_id)
            return jsonify({"success": True, **data})
        except FileNotFoundError as error:
            return jsonify({"error": str(error)}), 404

    @app.route("/api/skills/editor/<skill_id>", methods=["POST"])
    def api_skills_editor_save(skill_id: str):
        root = CONFIG["ifrit"]["root_path_resolved"]
        data = request.json or {}
        content = data.get("content")
        if content is None:
            return jsonify({"error": "缺少 content"}), 400
        try:
            save_editor(root, skill_id, content)
            return jsonify({"success": True})
        except FileNotFoundError as error:
            return jsonify({"error": str(error)}), 404

    @app.route("/api/skills/actions")
    def api_skills_actions():
        return jsonify({"success": True, "actions": get_actions_catalog()})

    @app.route("/api/about/info")
    def api_about_info():
        return jsonify(get_project_info(CONFIG))

    @app.route("/api/about/manual")
    def api_about_manual():
        data = get_manual_markdown(CONFIG)
        if not data.get("success"):
            return jsonify(data), 404
        return jsonify(data)

    @app.route("/api/about/cli")
    def api_about_cli():
        data = get_cli_docs(CONFIG)
        if not data.get("success"):
            return jsonify(data), 404
        return jsonify(data)

    @app.route("/reports/view/<run_id>")
    def view_report_redirect(run_id: str):
        return redirect(f"/reports/view/{run_id}/", code=302)

    @app.route("/reports/view/<run_id>/")
    @app.route("/reports/view/<run_id>/<path:subpath>")
    def view_report(run_id: str, subpath: str = None):
        file_path = resolve_report_html_file(CONFIG, run_id, subpath)
        if not file_path:
            run_dir = project_path(CONFIG, "reports_runs") / run_id
            allure_dir = run_dir / "allure-results"
            has_allure = allure_dir.is_dir() and any(allure_dir.iterdir())
            return (
                render_template("report_missing.html", run_id=run_id, has_allure=has_allure),
                404,
            )
        mime, _ = mimetypes.guess_type(str(file_path))
        return send_file(file_path, mimetype=mime or "application/octet-stream")

    @app.route("/api/reports/run/<run_id>", methods=["DELETE"])
    def api_reports_delete_run(run_id: str):
        if not delete_report_run(CONFIG, run_id):
            return jsonify({"error": "Run 不存在或无法删除"}), 404
        return jsonify({"success": True, "run_id": run_id})

    @app.route("/api/reports/run/<run_id>/generate", methods=["POST"])
    def api_reports_generate_run(run_id: str):
        result = generate_run_html_report(CONFIG, run_id)
        if not result.get("ok"):
            return jsonify({"error": result.get("error", "生成失败")}), 400
        return jsonify({"success": True, **result})

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

    @app.route("/api/import/preview", methods=["POST"])
    def api_import_preview():
        root = CONFIG["ifrit"]["root_path_resolved"]
        try:
            import_rel = _resolve_import_file(root)
            import_format = "postman"
            if request.form:
                import_format = request.form.get("format", "postman")
            body = request.get_json(silent=True) or {}
            if body.get("format"):
                import_format = body.get("format")
            data = preview_import(root, import_rel, import_format)
            data["import_file"] = import_rel
            return jsonify({"success": True, **data})
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        except Exception as error:
            return jsonify({"error": f"预览失败: {error}"}), 400

    @app.route("/api/import/project-context", methods=["GET"])
    def api_import_project_context():
        root = CONFIG["ifrit"]["root_path_resolved"]
        try:
            return jsonify({"success": True, "context": get_project_context(root)})
        except Exception as error:
            return jsonify({"error": str(error)}), 500

    @app.route("/api/import/diagnose", methods=["POST"])
    def api_import_diagnose():
        root = CONFIG["ifrit"]["root_path_resolved"]
        try:
            import_rel = _resolve_import_file(root)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        inject = request.form.get("inject_project_context") in ("1", "true", "True", "on")
        use_rag = request.form.get("rag") in ("1", "true", "True", "on")
        if request.is_json and request.json:
            inject = bool(request.json.get("inject_project_context", inject))
            use_rag = bool(request.json.get("rag", use_rag))

        params = {
            "import_file": import_rel,
            "format": request.form.get("format", "postman"),
            "inject_project_context": inject,
            "rag": use_rag,
            "rag_top_k": request.form.get("rag_top_k", 5),
        }
        try:
            cmd = build_import_diagnose_command(CONFIG, params)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        process_id = process_manager.start(cmd, root, label="import_diagnose")
        return jsonify({"process_id": process_id, "command": " ".join(cmd), "import_file": import_rel})

    @app.route("/api/import/save", methods=["POST"])
    def api_import_save():
        root = CONFIG["ifrit"]["root_path_resolved"]
        data = request.json or {}
        original = data.get("original_rows") or []
        append = data.get("append_rows") or []
        if not original:
            return jsonify({"error": "缺少 original_rows"}), 400
        suite = data.get("suite", "manual")
        output_format = data.get("output_format", "csv")
        output_rel = (data.get("output") or "").strip()
        collection_name = data.get("collection_name") or "import"
        try:
            saved = save_merged_cases(
                root,
                original,
                append,
                suite=suite,
                output_format=output_format,
                output_rel=output_rel,
                collection_name=collection_name,
            )
            rag_doc_id = ingest_case_file_to_rag(CONFIG, saved)
            payload = {"success": True, "output_file": saved, "total": len(original) + len(append)}
            if rag_doc_id is not None:
                payload["rag_ingested"] = True
                payload["rag_doc_id"] = rag_doc_id
            return jsonify(payload)
        except Exception as error:
            return jsonify({"error": str(error)}), 400

    @app.route("/api/import", methods=["POST"])
    def api_import():
        root = CONFIG["ifrit"]["root_path_resolved"]
        try:
            import_rel = _resolve_import_file(root)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        suite = request.form.get("suite", "manual")
        output = (request.form.get("output") or "").strip()
        dry_run = request.form.get("dry_run") in ("1", "true", "True", "on")
        output_format = request.form.get("output_format", "csv")

        params: Dict[str, Any] = {
            "import_file": import_rel,
            "format": request.form.get("format", "postman"),
            "suite": suite,
            "dry_run": dry_run,
            "output_format": output_format,
        }
        output_file = ""
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
                "import_file": import_rel,
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
    root = CONFIG["ifrit"]["root_path_resolved"]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from config.loader import reload_dotenv
        reload_dotenv(str(root / ".env"))
    except Exception:
        pass


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
