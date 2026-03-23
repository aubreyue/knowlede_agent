from __future__ import annotations

import base64
import streamlit as st

from agent_runtime import run_agent
from ingest import build_vectorstore, list_supported_files, load_documents, vectorstore_exists
from qa_chain import answer_question, build_source_labels, save_markdown, summarize_knowledge_base
from utils import DATA_DIR, OUTPUTS_DIR, ensure_directories, get_settings


st.set_page_config(page_title="LangChain 本地知识库 + 联网搜索 Agent", page_icon="📚", layout="wide")

ensure_directories()
settings = get_settings()


def get_image_data_uri(path: str) -> str:
    image_bytes = open(path, "rb").read()
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f7f4ee;
            --surface: rgba(255, 255, 255, 0.82);
            --surface-strong: #fffdf8;
            --border: rgba(88, 67, 39, 0.14);
            --text: #2c241b;
            --muted: #75695c;
            --accent: #0d7a5f;
            --accent-soft: rgba(13, 122, 95, 0.10);
            --warm: #c7683d;
            --shadow: 0 18px 45px rgba(76, 55, 30, 0.10);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(199, 104, 61, 0.10), transparent 24%),
                radial-gradient(circle at top right, rgba(13, 122, 95, 0.12), transparent 28%),
                linear-gradient(180deg, #fbf8f2 0%, #f3eee5 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            letter-spacing: -0.02em;
            color: var(--text);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f2eadc 0%, #ece3d4 100%);
            border-right: 1px solid rgba(88, 67, 39, 0.08);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label {
            color: #3e3328;
        }

        [data-testid="stFileUploaderDropzone"],
        [data-testid="stForm"],
        [data-testid="stExpander"] {
            background: var(--surface);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 22px;
            box-shadow: var(--shadow);
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 0.8rem 1rem;
            box-shadow: var(--shadow);
        }

        button[kind="primary"], button[kind="secondary"] {
            border-radius: 999px !important;
            border: 1px solid rgba(88, 67, 39, 0.10) !important;
        }

        button[kind="primary"] {
            background: linear-gradient(135deg, #0d7a5f, #159a78) !important;
            color: white !important;
        }

        .hero-shell {
            background:
                linear-gradient(135deg, rgba(255, 253, 248, 0.96), rgba(249, 244, 236, 0.92)),
                linear-gradient(120deg, rgba(13, 122, 95, 0.06), rgba(199, 104, 61, 0.08));
            border: 1px solid var(--border);
            border-radius: 30px;
            box-shadow: var(--shadow);
            padding: 2rem 2rem 1.5rem 2rem;
            margin-bottom: 1.4rem;
            overflow: hidden;
            position: relative;
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            width: 220px;
            height: 220px;
            right: -60px;
            top: -80px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(13, 122, 95, 0.18), transparent 70%);
        }

        .hero-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
            gap: 1.5rem;
            align-items: stretch;
        }

        .hero-copy-grid {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 220px;
            gap: 1.4rem;
            align-items: center;
        }

        .eyebrow {
            display: inline-block;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            background: var(--accent-soft);
            color: var(--accent);
            font-size: 0.88rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }

        .hero-title {
            font-size: 3.5rem;
            line-height: 1.02;
            font-weight: 800;
            margin: 0;
            max-width: 11ch;
        }

        .hero-subtitle {
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.8;
            max-width: 60ch;
            margin-top: 0.9rem;
            margin-bottom: 0;
        }

        .hero-illustration {
            width: min(100%, 205px);
            margin-left: auto;
            margin-right: auto;
        }

        .hero-illustration img {
            width: 100%;
            display: block;
            border-radius: 26px;
            box-shadow: 0 16px 34px rgba(76, 55, 30, 0.10);
            object-fit: cover;
        }

        .section-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 1rem 1.1rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .section-label {
            color: var(--warm);
            font-size: 0.84rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }

        .section-copy {
            color: var(--muted);
            margin: 0;
            line-height: 1.75;
        }

        .hero-visual {
            min-height: 100%;
            background:
                radial-gradient(circle at top right, rgba(13, 122, 95, 0.18), transparent 28%),
                linear-gradient(145deg, rgba(255,255,255,0.92), rgba(244, 238, 227, 0.9));
            border: 1px solid rgba(88, 67, 39, 0.10);
            border-radius: 26px;
            padding: 1.2rem;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.6), var(--shadow);
            position: relative;
            overflow: hidden;
        }

        .visual-orbit {
            position: absolute;
            inset: 18px;
            border-radius: 24px;
            border: 1px dashed rgba(13, 122, 95, 0.16);
            pointer-events: none;
        }

        .visual-stack {
            display: grid;
            gap: 0.9rem;
            position: relative;
            z-index: 2;
        }

        .visual-node {
            border-radius: 20px;
            padding: 0.95rem 1rem;
            border: 1px solid rgba(88, 67, 39, 0.10);
            background: rgba(255, 253, 248, 0.94);
            box-shadow: 0 10px 28px rgba(76, 55, 30, 0.08);
        }

        .visual-node strong {
            display: block;
            font-size: 1rem;
            color: var(--text);
            margin-bottom: 0.2rem;
        }

        .visual-node span {
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.55;
        }

        .visual-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.9rem;
        }

        .node-accent {
            background: linear-gradient(135deg, rgba(13, 122, 95, 0.13), rgba(255,255,255,0.95));
        }

        .node-warm {
            background: linear-gradient(135deg, rgba(199, 104, 61, 0.12), rgba(255,255,255,0.95));
        }

        .visual-footer {
            margin-top: 0.2rem;
            border-radius: 18px;
            padding: 0.9rem 1rem;
            background: rgba(44, 36, 27, 0.04);
            color: #55473a;
            font-size: 0.92rem;
            line-height: 1.6;
        }

        @media (max-width: 980px) {
            .hero-grid {
                grid-template-columns: 1fr;
            }

            .hero-copy-grid {
                grid-template-columns: 1fr;
            }

            .hero-title {
                font-size: 2.8rem;
                max-width: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    sheep_image = get_image_data_uri("/Users/aubreyue/STUDY/AI Agent/langchain_knowledge_qa/pics/sheep.png")
    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="hero-grid">
                <div>
                    <div class="eyebrow">RAG + Agent + MCP + Web Search</div>
                    <div class="hero-copy-grid">
                        <h1 class="hero-title">LangChain本地知识库➕联网协同Agent</h1>
                        <div class="hero-illustration">
                            <img src="{sheep_image}" alt="sheep hero" />
                        </div>
                    </div>
                    <p class="hero-subtitle">
                        一个用于学习现代 AI Agent 架构的交互式项目：本地知识库负责可控检索，
                        Agent 负责任务编排，MCP 负责工具接入，联网搜索在信息不足时提供补充。
                    </p>
                </div>
                <div class="hero-visual">
                    <div class="visual-orbit"></div>
                    <div class="visual-stack">
                        <div class="visual-node node-accent">
                            <strong>Agent Core</strong>
                            <span>负责理解任务、决定调用哪些工具，并整合最终回答。</span>
                        </div>
                        <div class="visual-row">
                            <div class="visual-node">
                                <strong>Local RAG</strong>
                                <span>文档切分、向量检索、引用片段回显。</span>
                            </div>
                            <div class="visual-node node-warm">
                                <strong>Web Search</strong>
                                <span>Tavily 联网搜索，在本地知识不足时兜底补充。</span>
                            </div>
                        </div>
                        <div class="visual-row">
                            <div class="visual-node">
                                <strong>MCP Tools</strong>
                                <span>通过协议标准化暴露知识库状态、重建索引、检索等能力。</span>
                            </div>
                            <div class="visual-node">
                                <strong>Workspace UI</strong>
                                <span>Streamlit 页面负责上传文件、运行任务和查看调用轨迹。</span>
                            </div>
                        </div>
                        <div class="visual-footer">
                            设计目标：让一个学习型项目同时覆盖“检索、工具编排、协议接入、可视化演示”四层能力。
                        </div>
                    </div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_overview_cards() -> None:
    files = list_supported_files(DATA_DIR)
    vector_ready = vectorstore_exists()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("知识文件", len(files))
    col2.metric("向量库", "已构建" if vector_ready else "未构建")
    col3.metric("问答历史", len(st.session_state["chat_history"]))
    col4.metric("Agent 记录", len(st.session_state["agent_history"]))


def initialize_state() -> None:
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("agent_history", [])
    st.session_state.setdefault("latest_sources", [])
    st.session_state.setdefault("latest_answer", "")


def save_uploaded_file(uploaded_file):
    target = DATA_DIR / uploaded_file.name
    target.write_bytes(uploaded_file.getbuffer())
    return target


def render_chat_history() -> None:
    st.markdown("### 对话历史")
    if not st.session_state["chat_history"]:
        st.info("还没有问答记录，可以先问一个问题试试。")
        return

    for item in reversed(st.session_state["chat_history"]):
        with st.container(border=True):
            st.markdown(f"**问题**：{item['question']}")
            st.markdown(f"**回答**：{item['answer']}")
            with st.expander("查看引用来源"):
                for idx, source in enumerate(item["sources"], start=1):
                    st.markdown(f"{idx}. `{source}`")


def rebuild_vectorstore(show_message: bool = True) -> None:
    if not settings.openai_api_key:
        st.sidebar.error("请先在 .env 中配置 OPENAI_API_KEY")
        return

    try:
        with st.spinner("正在处理文档并构建向量库..."):
            chunk_count = build_vectorstore(settings)
    except ValueError as exc:
        st.sidebar.error(str(exc))
        return

    if show_message:
        st.sidebar.success(f"向量库构建完成，共写入 {chunk_count} 个文本块。")


def render_document_table() -> None:
    files = list_supported_files(DATA_DIR)
    if not files:
        st.info("当前 data/ 目录里还没有可用文档。")
        return

    st.markdown("### 文档清单")
    st.dataframe(files, width="stretch", hide_index=True)


def render_latest_result() -> None:
    if not st.session_state["latest_answer"]:
        return

    st.markdown("### 最新结果")
    st.write(st.session_state["latest_answer"])

    if st.session_state["latest_sources"]:
        st.markdown("### 最新引用")
        for idx, source in enumerate(st.session_state["latest_sources"], start=1):
            st.markdown(f"{idx}. `{source}`")


def render_sidebar() -> None:
    st.sidebar.title("项目操作")
    st.sidebar.caption("这是一个从 RAG 扩展到 Agent + MCP 的学习型项目。")

    st.sidebar.write(f"数据目录: `{DATA_DIR}`")
    st.sidebar.write(f"输出目录: `{OUTPUTS_DIR}`")
    st.sidebar.write(f"向量库状态: `{'已构建' if vectorstore_exists() else '未构建'}`")

    uploaded_files = st.sidebar.file_uploader(
        "上传知识文件",
        type=["md", "txt", "pdf"],
        accept_multiple_files=True,
        help="上传后文件会直接保存到 data/ 目录中。",
    )
    auto_rebuild = st.sidebar.checkbox("上传后自动重建向量库", value=True)
    if uploaded_files:
        saved_paths = [save_uploaded_file(file) for file in uploaded_files]
        st.sidebar.success(f"已保存 {len(saved_paths)} 个文件到 data/ 目录。")
        if auto_rebuild:
            rebuild_vectorstore(show_message=True)

    docs = load_documents(DATA_DIR)
    st.sidebar.write(f"已发现文档数: `{len(docs)}`")

    if st.sidebar.button("构建 / 更新向量库", width="stretch"):
        rebuild_vectorstore(show_message=True)

    if st.sidebar.button("清空对话历史", width="stretch"):
        st.session_state["chat_history"] = []
        st.session_state["agent_history"] = []
        st.session_state["latest_answer"] = ""
        st.session_state["latest_sources"] = []
        st.sidebar.success("已清空当前对话历史。")

    st.sidebar.markdown("### 学习重点")
    st.sidebar.markdown("- RAG 检索与引用")
    st.sidebar.markdown("- LangChain Agent 工具调用")
    st.sidebar.markdown("- MCP server 协议接入")
    st.sidebar.markdown("- 本地知识库 + 联网搜索混合问答")
    st.sidebar.markdown("- Streamlit 应用封装")


def render_qa_tab() -> None:
    st.subheader("知识库问答")
    render_chat_history()
    st.caption("这里是纯本地 RAG 问答，只会基于你导入并完成向量化的知识库内容回答。")
    question = st.chat_input("例如：这份文档的核心结论是什么？")

    if question:
        with st.chat_message("user"):
            st.write(question)

        try:
            with st.spinner("正在检索并生成回答..."):
                result = answer_question(question, settings)
        except FileNotFoundError as exc:
            st.error(str(exc))
            return

        answer = result.get("answer", "")
        context_docs = result.get("context", [])

        with st.chat_message("assistant"):
            st.write(answer)

        source_lines = build_source_labels(context_docs)
        for idx, doc in enumerate(context_docs, start=1):
            source_label = source_lines[idx - 1]
            with st.expander(source_label, expanded=False):
                st.write(doc.page_content)

        st.session_state["chat_history"].append(
            {
                "question": question,
                "answer": answer,
                "sources": source_lines,
            }
        )
        st.session_state["latest_answer"] = answer
        st.session_state["latest_sources"] = source_lines

        sources_markdown = "\n".join(f"- `{source}`" for source in source_lines) or "- 无"
        output = (
            f"# 问答记录\n\n## 问题\n{question}\n\n## 回答\n{answer}\n\n## 引用来源\n{sources_markdown}\n"
        )
        output_path = save_markdown("latest_answer.md", output)
        st.success(f"回答已保存到 `{output_path}`")

    render_latest_result()


def render_agent_tab() -> None:
    st.subheader("Agent 工作台")
    st.caption("这里的 Agent 会优先查本地知识库；如果信息不足，或问题具有时效性，则会联网搜索补充。")

    if st.session_state["agent_history"]:
        st.markdown("### Agent 历史")
        for item in reversed(st.session_state["agent_history"]):
            with st.container(border=True):
                st.markdown(f"**任务**：{item['task']}")
                st.markdown(f"**Agent 输出**：{item['answer']}")
                if item["traces"]:
                    with st.expander("查看工具调用轨迹"):
                        for trace in item["traces"]:
                            st.markdown(f"- {trace}")

    with st.form("agent_form", clear_on_submit=False):
        task = st.text_area(
            "给 Agent 一个任务",
            placeholder="例如：先检查知识库状态，如果本地没有西游记资料，就联网搜索西游记简介并整理成 markdown；如果有本地资料则优先使用本地内容。",
            height=120,
        )
        submitted = st.form_submit_button("运行 Agent", width="stretch")

    if submitted and task.strip():
        if not settings.openai_api_key:
            st.error("请先在 .env 中配置 OPENAI_API_KEY")
            return

        try:
            with st.spinner("Agent 正在规划并调用工具..."):
                result = run_agent(task.strip(), settings)
        except Exception as exc:
            st.error(f"Agent 执行失败：{exc}")
            return

        answer = result.get("answer", "")
        traces = result.get("traces", [])
        st.write(answer)

        if traces:
            with st.expander("查看工具调用轨迹", expanded=True):
                for trace in traces:
                    st.markdown(f"- {trace}")

        st.session_state["agent_history"].append(
            {
                "task": task.strip(),
                "answer": answer,
                "traces": traces,
            }
        )

        output = f"# Agent 任务记录\n\n## 任务\n{task.strip()}\n\n## 输出\n{answer}\n"
        if traces:
            output += "\n## 工具调用轨迹\n" + "\n".join(f"- {trace}" for trace in traces) + "\n"
        output_path = save_markdown("latest_agent_run.md", output)
        st.success(f"Agent 运行记录已保存到 `{output_path}`")


def render_summary_tab() -> None:
    st.subheader("知识库摘要")
    if st.button("生成摘要", width="stretch"):
        try:
            with st.spinner("正在生成摘要..."):
                summary = summarize_knowledge_base(settings)
        except FileNotFoundError as exc:
            st.error(str(exc))
            return

        st.write(summary)
        output_path = save_markdown("knowledge_summary.md", summary)
        st.success(f"摘要已保存到 `{output_path}`")


def render_documents_tab() -> None:
    st.subheader("文档管理")
    st.caption("这里展示当前知识库中可被索引的本地文件。")
    render_document_table()


initialize_state()

inject_styles()
render_hero()
render_overview_cards()

render_sidebar()

tab_qa, tab_agent, tab_summary, tab_docs = st.tabs(["问答", "Agent", "摘要", "文档"])

with tab_qa:
    render_qa_tab()

with tab_agent:
    render_agent_tab()

with tab_summary:
    render_summary_tab()

with tab_docs:
    render_documents_tab()
