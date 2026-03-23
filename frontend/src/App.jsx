import { useEffect, useState } from "react";
import sheepImage from "./assets/sheep.png";

const API_BASE = (import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api").replace(/\/$/, "");
const TABS = ["问答", "Agent", "摘要", "文档"];

async function apiGet(path) {
  const response = await fetch(`${API_BASE}${path}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "请求失败");
  }
  return data;
}

async function apiPost(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "请求失败");
  }
  return data;
}

async function uploadFiles(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const response = await fetch(`${API_BASE}/uploads`, {
    method: "POST",
    body: formData,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "上传失败");
  }
  return data;
}

function MetricCard({ label, value }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
    </div>
  );
}

function ResultPanel({ title, children }) {
  return (
    <section className="result-panel">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState("问答");
  const [status, setStatus] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [autoRebuild, setAutoRebuild] = useState(true);
  const [qaQuestion, setQaQuestion] = useState("");
  const [qaResult, setQaResult] = useState(null);
  const [agentTask, setAgentTask] = useState("介绍一下红楼梦，然后总结并导出为 markdown。");
  const [agentResult, setAgentResult] = useState(null);
  const [summaryResult, setSummaryResult] = useState(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const refreshStatus = async () => {
    const [statusData, docsData] = await Promise.all([
      apiGet("/status"),
      apiGet("/documents"),
    ]);
    setStatus(statusData);
    setDocuments(docsData.documents);
  };

  useEffect(() => {
    refreshStatus().catch((err) => setError(err.message));
  }, []);

  const handleUpload = async (event) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;
    setBusy("正在上传文件...");
    setError("");
    setNotice("");
    try {
      const result = await uploadFiles(files);
      if (autoRebuild) {
        const rebuild = await apiPost("/vectorstore/rebuild", {});
        setNotice(`已上传 ${result.saved_count} 个文件，并完成向量库更新。${rebuild.message}`);
      } else {
        setNotice(`已上传 ${result.saved_count} 个文件。`);
      }
      await refreshStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy("");
      event.target.value = "";
    }
  };

  const handleRebuild = async () => {
    setBusy("正在构建向量库...");
    setError("");
    setNotice("");
    try {
      const result = await apiPost("/vectorstore/rebuild", {});
      setNotice(result.message);
      await refreshStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy("");
    }
  };

  const handleAsk = async () => {
    if (!qaQuestion.trim()) return;
    setBusy("正在执行知识库问答...");
    setError("");
    setNotice("");
    try {
      const result = await apiPost("/qa", { question: qaQuestion });
      setQaResult(result);
      setNotice(`问答结果已保存到 ${result.output_path}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy("");
    }
  };

  const handleAgent = async () => {
    if (!agentTask.trim()) return;
    setBusy("Agent 正在规划并调用工具...");
    setError("");
    setNotice("");
    try {
      const result = await apiPost("/agent/run", { task: agentTask });
      setAgentResult(result);
      setNotice(`Agent 运行记录已保存到 ${result.output_path}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy("");
    }
  };

  const handleSummary = async () => {
    setBusy("正在生成摘要...");
    setError("");
    setNotice("");
    try {
      const result = await apiPost("/summary", {});
      setSummaryResult(result);
      setNotice(`知识库摘要已保存到 ${result.output_path}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy("");
    }
  };

  const handleClearHistory = () => {
    setQaResult(null);
    setAgentResult(null);
    setSummaryResult(null);
    setNotice("已清空当前前端会话中的问答与 Agent 结果。");
    setError("");
  };

  return (
    <div className={sidebarOpen ? "page-shell" : "page-shell collapsed"}>
      {!sidebarOpen ? (
        <button
          className="sidebar-toggle collapsed"
          onClick={() => setSidebarOpen(true)}
          aria-label="展开侧边栏"
          title="展开侧边栏"
        >
          »
        </button>
      ) : null}
      <aside className="sidebar">
        <div className="sidebar-panel">
          <button
            className="sidebar-toggle in-sidebar"
            onClick={() => setSidebarOpen(false)}
            aria-label="收起侧边栏"
            title="收起侧边栏"
          >
            «
          </button>
          <div className="sidebar-title">项目控制台</div>
          <p className="sidebar-copy">
            这是一个从 RAG 扩展到 Agent + MCP 的学习型项目。
          </p>
          <div className="sidebar-meta">
            <div>
              <span>数据目录</span>
              <strong>{status?.data_dir || "-"}</strong>
            </div>
            <div>
              <span>输出目录</span>
              <strong>{status?.outputs_dir || "-"}</strong>
            </div>
          </div>
          <div className="status-row">
            <span>向量库状态</span>
            <strong className={status?.vectorstore_ready ? "status-badge ready" : "status-badge"}>
              {status?.vectorstore_ready ? "已构建" : "未构建"}
            </strong>
          </div>
          <label className="upload-box">
            <span className="upload-title">上传知识文件</span>
            <span className="upload-copy">Drag and drop files here</span>
            <span className="upload-hint">Limit 200MB per file • MD, TXT, PDF</span>
            <input type="file" multiple accept=".md,.txt,.pdf" onChange={handleUpload} />
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={autoRebuild}
              onChange={(event) => setAutoRebuild(event.target.checked)}
            />
            <span>上传后自动重建向量库</span>
          </label>
          <div className="status-row">
            <span>已发现文档数</span>
            <strong className="count-badge">{documents.length}</strong>
          </div>
          <button className="primary-button" onClick={handleRebuild} disabled={!!busy}>
            构建 / 更新向量库
          </button>
          <button className="secondary-button" onClick={handleClearHistory} disabled={!!busy}>
            清空对话历史
          </button>
          {busy ? <div className="status-info">{busy}</div> : null}
          {notice ? <div className="status-success">{notice}</div> : null}
          {error ? <div className="status-error">{error}</div> : null}
        </div>
      </aside>

      <main className="main-panel">
        <section className="hero">
          <div className="hero-layout">
            <div className="hero-main">
              <div className="hero-copy">
                <div className="eyebrow">RAG + Agent + MCP + Web Search</div>
                <div className="hero-copy-grid">
                  <h1>
                    <span>LangChain本地知识库</span>
                    <span className="hero-plus-line">+</span>
                    <span>联网协同Agent</span>
                  </h1>
                  <div className="hero-image-wrap">
                    <img src={sheepImage} alt="sheep illustration" className="hero-image" />
                  </div>
                </div>
                <p>
                  一个用于学习现代 AI Agent 架构的交互式项目：本地知识库负责可控检索，Agent 负责任务编排，MCP 负责工具接入，联网搜索在信息不足时提供补充。
                </p>
              </div>
            </div>
            <div className="hero-visual">
              <div className="visual-orbit"></div>
              <div className="visual-stack">
                <div className="visual-node node-accent">
                  <strong>Agent Core</strong>
                  <span>负责理解任务、决定调用哪些工具，并整合最终回答。</span>
                </div>
                <div className="visual-row">
                  <div className="visual-node">
                    <strong>Local RAG</strong>
                    <span>文档切分、向量检索、引用片段回显。</span>
                  </div>
                  <div className="visual-node node-warm">
                    <strong>Web Search</strong>
                    <span>Tavily 联网搜索，在本地知识不足时兜底补充。</span>
                  </div>
                </div>
                <div className="visual-row">
                  <div className="visual-node">
                    <strong>MCP Tools</strong>
                    <span>通过协议标准化暴露知识库状态、重建索引、检索等能力。</span>
                  </div>
                  <div className="visual-node">
                    <strong>Workspace UI</strong>
                    <span>React 页面负责上传文件、运行任务和查看调用轨迹。</span>
                  </div>
                </div>
                <div className="visual-footer">
                  设计目标：让一个学习型项目同时覆盖“检索、工具编排、协议接入、可视化演示”四层能力。
                </div>
              </div>
            </div>
          </div>
          <div className="hero-grid">
            <MetricCard label="知识文件" value={status?.document_count ?? 0} />
            <MetricCard label="向量库" value={status?.vectorstore_ready ? "已构建" : "未构建"} />
            <MetricCard label="前端页签" value={TABS.length} />
            <MetricCard label="文档清单" value={documents.length} />
          </div>
        </section>

        <nav className="tab-row">
          {TABS.map((tab) => (
            <button
              key={tab}
              className={tab === activeTab ? "tab active" : "tab"}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </nav>

        {activeTab === "问答" ? (
          <section className="content-card">
            <h2>知识库问答</h2>
            <p className="content-copy">这里是纯本地 RAG 问答，只会使用知识库中已经向量化的内容。</p>
            <textarea
              className="task-box"
              value={qaQuestion}
              onChange={(event) => setQaQuestion(event.target.value)}
              placeholder="例如：这份文档的核心结论是什么？"
            />
            <button className="primary-button" onClick={handleAsk} disabled={!!busy}>
              运行问答
            </button>
            {qaResult ? (
              <div className="stack">
                <ResultPanel title="回答">{qaResult.answer}</ResultPanel>
                <ResultPanel title="引用来源">
                  <ul className="clean-list">
                    {qaResult.sources.map((source) => (
                      <li key={source}>{source}</li>
                    ))}
                  </ul>
                </ResultPanel>
                <ResultPanel title="片段预览">
                  <div className="stack">
                    {qaResult.source_previews.map((item) => (
                      <div className="trace-item" key={item.label}>
                        <strong>{item.label}</strong>
                        <span>{item.snippet}</span>
                      </div>
                    ))}
                  </div>
                </ResultPanel>
              </div>
            ) : null}
          </section>
        ) : null}

        {activeTab === "Agent" ? (
          <section className="content-card">
            <h2>Agent 工作台</h2>
            <p className="content-copy">优先查本地知识库，信息不足或具时效性时自动联网搜索。</p>
            <textarea
              className="task-box"
              value={agentTask}
              onChange={(event) => setAgentTask(event.target.value)}
              placeholder="例如：介绍一下红楼梦，然后总结并导出为 markdown。"
            />
            <button className="primary-button" onClick={handleAgent} disabled={!!busy}>
              运行 Agent
            </button>
            {agentResult ? (
              <div className="stack">
                <ResultPanel title="Agent 输出">{agentResult.answer}</ResultPanel>
                <ResultPanel title="工具调用轨迹">
                  <div className="stack">
                    {agentResult.traces.map((trace, index) => (
                      <div className="trace-item" key={`${trace}-${index}`}>
                        <span>{trace}</span>
                      </div>
                    ))}
                  </div>
                </ResultPanel>
              </div>
            ) : null}
          </section>
        ) : null}

        {activeTab === "摘要" ? (
          <section className="content-card">
            <h2>知识库摘要</h2>
            <p className="content-copy">面向整个知识库做整体总结，适合快速了解当前资料主题。</p>
            <button className="primary-button" onClick={handleSummary} disabled={!!busy}>
              生成摘要
            </button>
            {summaryResult ? <ResultPanel title="摘要内容">{summaryResult.summary}</ResultPanel> : null}
          </section>
        ) : null}

        {activeTab === "文档" ? (
          <section className="content-card">
            <h2>文档管理</h2>
            <p className="content-copy">展示当前本地知识库中已纳入管理的文件。</p>
            <div className="doc-grid">
              {documents.map((doc) => (
                <article className="doc-card" key={doc.path}>
                  <strong>{doc.name}</strong>
                  <span>{doc.suffix}</span>
                  <span>{doc.size_kb} KB</span>
                  <code>{doc.path}</code>
                </article>
              ))}
            </div>
          </section>
        ) : null}
      </main>
    </div>
  );
}
