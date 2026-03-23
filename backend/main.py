from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from agent_runtime import run_agent
from ingest import build_vectorstore, list_supported_files, load_documents, vectorstore_exists
from qa_chain import answer_question, build_context_preview, build_source_labels, save_markdown, summarize_knowledge_base
from utils import DATA_DIR, OUTPUTS_DIR, ensure_directories, get_settings


def _cors_origins() -> list[str]:
    configured = os.getenv("FRONTEND_ORIGINS", "")
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    defaults = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    return origins or defaults


app = FastAPI(title="LangChain Knowledge QA API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_directories()


def _settings():
    return get_settings()


def _serialize_path(path: Path) -> str:
    return str(path.resolve())


def _save_upload(uploaded_file: UploadFile) -> str:
    target = DATA_DIR / uploaded_file.filename
    target.write_bytes(uploaded_file.file.read())
    return _serialize_path(target)


def _status_payload() -> dict[str, Any]:
    files = list_supported_files(DATA_DIR)
    return {
        "data_dir": _serialize_path(DATA_DIR),
        "outputs_dir": _serialize_path(OUTPUTS_DIR),
        "document_count": len(files),
        "vectorstore_ready": vectorstore_exists(),
        "chat_history_count": 0,
        "agent_history_count": 0,
        "files": files,
    }


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status")
def get_status() -> dict[str, Any]:
    return _status_payload()


@app.get("/api/documents")
def get_documents() -> dict[str, Any]:
    return {"documents": list_supported_files(DATA_DIR)}


@app.post("/api/uploads")
def upload_documents(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    saved = [_save_upload(file) for file in files if file.filename]
    return {
        "saved_count": len(saved),
        "saved_paths": saved,
        "documents": list_supported_files(DATA_DIR),
    }


@app.post("/api/vectorstore/rebuild")
def rebuild_store() -> dict[str, Any]:
    settings = _settings()
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="请先在 .env 中配置 OPENAI_API_KEY")

    try:
        chunk_count = build_vectorstore(settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"message": f"向量库构建完成，共写入 {chunk_count} 个文本块。", "chunk_count": chunk_count}


@app.post("/api/qa")
def qa(payload: dict[str, str]) -> dict[str, Any]:
    question = payload.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    settings = _settings()
    try:
        result = answer_question(question, settings)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    context_docs = result.get("context", [])
    source_labels = build_source_labels(context_docs)
    previews = build_context_preview(context_docs)
    answer = result.get("answer", "")

    output = (
        f"# 问答记录\n\n## 问题\n{question}\n\n## 回答\n{answer}\n\n## 引用来源\n"
        + ("\n".join(f"- `{source}`" for source in source_labels) or "- 无")
        + "\n"
    )
    output_path = save_markdown("latest_answer.md", output)

    return {
        "question": question,
        "answer": answer,
        "sources": source_labels,
        "source_previews": previews,
        "output_path": _serialize_path(output_path),
    }


@app.post("/api/summary")
def summary() -> dict[str, Any]:
    settings = _settings()
    try:
        result = summarize_knowledge_base(settings)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    output_path = save_markdown("knowledge_summary.md", result)
    return {"summary": result, "output_path": _serialize_path(output_path)}


@app.post("/api/agent/run")
def agent_run(payload: dict[str, str]) -> dict[str, Any]:
    task = payload.get("task", "").strip()
    if not task:
        raise HTTPException(status_code=400, detail="task is required")

    settings = _settings()
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="请先在 .env 中配置 OPENAI_API_KEY")

    try:
        result = run_agent(task, settings)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    answer = result.get("answer", "")
    traces = result.get("traces", [])

    output = f"# Agent 任务记录\n\n## 任务\n{task}\n\n## 输出\n{answer}\n"
    if traces:
        output += "\n## 工具调用轨迹\n" + "\n".join(f"- {trace}" for trace in traces) + "\n"
    output_path = save_markdown("latest_agent_run.md", output)

    return {
        "task": task,
        "answer": answer,
        "traces": traces,
        "output_path": _serialize_path(output_path),
    }


@app.get("/api/sample-prompts")
def sample_prompts() -> dict[str, list[str]]:
    return {
        "qa": [
            "这份文档的核心结论是什么？",
            "当前知识库里有哪些重要主题？",
        ],
        "agent": [
            "先检查知识库状态，如果本地资料不足，就联网搜索 MCP 是什么，并整理成中文总结。",
            "介绍一下红楼梦，然后总结并导出为 markdown。",
        ],
    }
