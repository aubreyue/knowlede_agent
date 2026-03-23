from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ingest import build_vectorstore, list_supported_files, vectorstore_exists
from qa_chain import build_context_preview, retrieve_documents, summarize_knowledge_base
from utils import DATA_DIR, get_settings


mcp = FastMCP(
    name="knowledge-base-mcp",
    instructions=(
        "一个围绕本地知识库的 MCP server，提供文档列表、向量库状态、检索和摘要能力。"
    ),
)


@mcp.tool(description="查看当前知识库中的本地文件列表和基础信息。")
def list_knowledge_files() -> list[dict]:
    return list_supported_files(DATA_DIR)


@mcp.tool(description="查看向量库和文档目录状态，用于 Agent 判断是否可以执行知识检索。")
def inspect_knowledge_base_status() -> dict:
    files = list_supported_files(DATA_DIR)
    return {
        "data_dir": str(DATA_DIR),
        "document_count": len(files),
        "vectorstore_ready": vectorstore_exists(),
        "files": files,
    }


@mcp.tool(description="重建知识库向量索引。当新增文档后，可调用此工具刷新向量库。")
def rebuild_knowledge_base() -> dict:
    settings = get_settings()
    chunk_count = build_vectorstore(settings)
    return {
        "status": "ok",
        "chunk_count": chunk_count,
        "message": f"向量库重建完成，共写入 {chunk_count} 个文本块。",
    }


@mcp.tool(description="在本地知识库中执行语义检索，返回最相关的文本片段。")
def search_knowledge_base(query: str, top_k: int = 4) -> dict:
    settings = get_settings()
    docs = retrieve_documents(query, settings, k=top_k)
    return {
        "query": query,
        "result_count": len(docs),
        "results": build_context_preview(docs),
    }


@mcp.tool(description="生成整个知识库的主题摘要，适合快速了解当前文档内容。")
def summarize_knowledge_base_tool() -> dict:
    settings = get_settings()
    summary = summarize_knowledge_base(settings)
    return {"summary": summary}


if __name__ == "__main__":
    mcp.run(transport="stdio")
