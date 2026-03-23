from __future__ import annotations

import os
from typing import Any


def search_web(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Search the public web and return lightweight result metadata."""
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("缺少 TAVILY_API_KEY，请先在 .env 中配置 Tavily 搜索密钥。")

    try:
        from tavily import TavilyClient
    except ImportError as exc:
        raise RuntimeError(
            "缺少 tavily-python 依赖，请先执行 `pip install -r requirements.txt`。"
        ) from exc

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            topic="general",
            search_depth="advanced",
            include_answer=False,
            include_raw_content=False,
        )
    except Exception as exc:
        raise RuntimeError(f"联网搜索失败：{exc}") from exc

    formatted: list[dict[str, Any]] = []
    for item in response.get("results", []):
        formatted.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            }
        )
    return formatted


def format_web_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return "没有检索到可用网页结果。"

    lines: list[str] = []
    for idx, item in enumerate(results, start=1):
        title = item.get("title", "无标题")
        url = item.get("url", "")
        snippet = item.get("snippet", "")
        lines.append(f"{idx}. {title}")
        if url:
            lines.append(f"链接: {url}")
        if snippet:
            lines.append(f"摘要: {snippet}")
        lines.append("")
    return "\n".join(lines).strip()
