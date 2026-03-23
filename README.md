# LangChain 本地知识库 + 联网搜索 Agent

这是一个面向 AI Agent 学习的前后端分离项目：

- 后端：`FastAPI`
- 前端：`React + Vite`
- 核心能力：`RAG + LangChain Agent + MCP + Tavily 搜索`

项目保留了原来的 Python 能力层，并把原本由 Streamlit 页面完成的交互迁移成了：

- `backend/` 提供 API
- `frontend/` 提供真实前端页面

## 当前架构

```text
langchain_knowledge_qa/
├── backend/
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
├── agent_runtime.py
├── ingest.py
├── mcp_server.py
├── qa_chain.py
├── web_tools.py
├── utils.py
├── data/
├── outputs/
├── vectorstore/
└── app.py
```

说明：

- `app.py` 仍保留，作为旧版 Streamlit demo
- 日常开发和展示建议使用 `React + FastAPI`

## 功能说明

### 1. 本地知识库 RAG

- 支持导入 `.md`、`.txt`、`.pdf`
- 文档切分、向量化、写入 `FAISS`
- 基于本地知识库做检索问答
- 返回引用来源和片段预览

### 2. Agent 工作台

- 使用 `LangChain create_agent`
- 优先查询本地知识库
- 本地知识不足时调用联网搜索
- 展示工具调用轨迹
- 导出 Agent 结果为 Markdown

### 3. MCP 工具接入

项目内置本地 `MCP server`，暴露：

- `list_knowledge_files`
- `inspect_knowledge_base_status`
- `rebuild_knowledge_base`
- `search_knowledge_base`
- `summarize_knowledge_base_tool`

### 4. 前后端分离

后端 API 示例：

- `GET /api/status`
- `GET /api/documents`
- `POST /api/uploads`
- `POST /api/vectorstore/rebuild`
- `POST /api/qa`
- `POST /api/summary`
- `POST /api/agent/run`

前端页面包含：

- 项目控制台
- 问答页
- Agent 页
- 摘要页
- 文档页

## 环境变量

后端参考 [`.env.example`](/Users/aubreyue/STUDY/AI%20Agent/langchain_knowledge_qa/.env.example)。
前端参考 [frontend/.env.example](/Users/aubreyue/STUDY/AI%20Agent/langchain_knowledge_qa/frontend/.env.example)。

当前至少需要：

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
CHAT_MODEL=
EMBEDDING_MODEL=
TAVILY_API_KEY=
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

前端本地开发环境变量：

```env
VITE_API_BASE=http://127.0.0.1:8000/api
```

## 启动方式

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端

在项目根目录运行：

```bash
uvicorn backend.main:app --reload
```

默认地址：

- [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 3. 启动前端

进入前端目录：

```bash
cd frontend
npm install
npm run dev
```

默认地址：

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

## 公网部署

推荐最省事的组合：

- 前端：`Vercel`
- 后端：`Render`

### 1. 部署 FastAPI 到 Render

1. 把整个项目推到 GitHub。
2. 登录 Render，新建 `Web Service`，选择这个仓库。
3. Root Directory 留空，或者直接指向仓库根目录。
4. Build Command：

```bash
pip install -r requirements.txt
```

5. Start Command：

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

6. 环境变量至少配置：

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
CHAT_MODEL=
EMBEDDING_MODEL=
TAVILY_API_KEY=
FRONTEND_ORIGINS=https://你的-vercel-前端域名
```

7. 部署完成后，你会拿到一个后端公网地址，例如：

```text
https://langchain-knowledge-qa-api.onrender.com
```

说明：

- 仓库里已经提供了 [render.yaml](/Users/aubreyue/STUDY/AI%20Agent/langchain_knowledge_qa/render.yaml)，你也可以用 Render Blueprint 直接导入。
- `data/`、`outputs/`、`vectorstore/` 在 Render 默认是临时磁盘，服务重启后可能丢失。学习演示可以先这样用，后续如果要长期保存，再加持久化磁盘或对象存储。

### 2. 部署 React 前端到 Vercel

1. 登录 Vercel，新建项目，导入同一个 GitHub 仓库。
2. Framework 选 `Vite`。
3. Root Directory 设为：

```text
frontend
```

4. Build Command 保持默认，或者填写：

```bash
npm run build
```

5. Output Directory：

```text
dist
```

6. 配置前端环境变量：

```env
VITE_API_BASE=https://你的-render-后端域名/api
```

例如：

```env
VITE_API_BASE=https://langchain-knowledge-qa-api.onrender.com/api
```

7. 部署完成后，你会拿到前端公网地址，例如：

```text
https://langchain-knowledge-qa.vercel.app
```

### 3. 回填跨域域名

当前端 Vercel 域名确定后，回到 Render，把：

```env
FRONTEND_ORIGINS=https://你的-vercel-前端域名
```

改成真实地址，然后重新部署后端。

如果你有多个前端域名，可以用英文逗号分隔：

```env
FRONTEND_ORIGINS=https://你的正式域名,https://你的-vercel-预览域名
```

### 4. 最终访问

部署完成后，直接打开你的 Vercel 域名即可，用户不再需要本地终端命令。

## 旧版 Streamlit

如果你还想继续看原型版本，也可以运行：

```bash
streamlit run app.py
```

不过当前推荐的主入口是：

- `FastAPI` 后端
- `React` 前端

## 适合学习的知识点

### RAG

- 文档加载与切分
- 向量化与 FAISS 检索
- 基于上下文回答
- 引用来源展示

### Agent

- LangChain Agent
- Tool calling
- 工具轨迹记录
- 本地检索与联网搜索协同

### MCP

- MCP server 定义工具
- 使用 `langchain-mcp-adapters` 接入工具
- 协议化工具访问

### 工程化

- 前后端分离
- FastAPI API 设计
- React 页面状态管理
- 文件上传与异步交互

## 后续建议

如果你想把它继续打磨成更强的简历项目，优先建议：

1. 给 Agent 输出增加更清晰的来源分区
2. 增加对话历史持久化
3. 增加检索评测或简单 benchmark
4. 增加第二类工具，例如 SQL 或浏览器
5. 引入 LangSmith 做链路观测
