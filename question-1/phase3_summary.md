# Phase 3：On-Call 助手 Agent 实现总结

## 1. 架构概览

Phase 3 的核心是在 `/v3` 路由下实现一个完全基于对话的智能 Agent。该 Agent 严格遵守题目限制，即**只拥有一个查阅本地文件内容的工具 `readFile`**，并且不允许使用列举目录或搜索的工具。

为了提供良好的用户体验，我们采用了**纯异步架构 + Server-Sent Events (SSE) 协议**，使前端不仅能实时看到 Agent 返回的文本，还能**可视化全过程监控** Agent 当下正在调用什么工具、读取了什么 SOP 文件。

### 技术栈选型
*   **后端 API**: FastAPI (`StreamingResponse`)
*   **大模型 SDK**: 官方原生 `openai` (版本 2.x) 的异步客户端 `AsyncOpenAI`
*   **前端 UI**: 原生 HTML + JavaScript (TextDecoder 解析 SSE 流) + TailwindCSS
*   **配置中心**: 项目根目录下引入 `config.json` 文件，支持动态热切换大模型接口（Base URL / API Key / Model）以及检索增强策略。

---

## 2. 核心流程与交互机制

### (1) 用户提问与前端发送
用户在浏览器输入问题，例如 _"数据库主从延迟超过 30 秒了，该如何排查？"_，前端将完整的对话历史封装为 JSON 提交到 `POST /v3/chat` 接口。

### (2) 智能上下文引导 (System Prompt Injection)
因为大模型工具 `readFile` 只能通过精确的文件名读取（如 `sop-002.html`），由于缺乏列目录的能力，大模型在最初无法凭空猜出文件全名。为此，我们设计了两种**文件清单发现机制**（可通过前端面板开关切换）：
1.  **静态兜底模式**：将整个 `data/` 目录的文件名清单通过 System Prompt 硬编码告知大模型。
2.  **向量辅助模式 (Phase 2 复用)**：服务端收到请求后，**静默调用 Phase 2 已预加载的 `VectorStore.search()`**，根据用户当前输入的最后一句话，获取最高相关的 Top-5 文档名称与标题。将这些高度相关的候选文件连同标题拼装进此轮对话的 System Prompt 中，例如："_根据你的判断，以下文档可能与问题相关：sop-002.html (数据库 DBA)_"，极大提高了大模型自主选择 `readFile` 参数的准确率。

### (3) 大模型推理与原生 Tool Calling (第一轮)
*   大模型收到上下文和工具定义后，通过内部推理逻辑（Thought Process），推断出自身需要调用工具，会在响应流 `delta` 中返回 `tool_calls`。
*   **SSE 实时下发状态**：一旦后端监听到 `tool_calls`，立即向前端抛出自定义事件 `event: tool_call`.
*   **前端渲染**：前端捕获到该事件后，在对话框气泡上方渲染出一个黄色的 `readFile("sop-002.html") 正在读取...` 的提示 Badge。

### (4) 本地执行 `readFile` 工具
*   待大模型第一次生成的流结束，后端会捕获其想要执行的所有工具参数。
*   在后端的 `agent.py` 中，执行本地函数 `read_file(fname)` 去 `data/` 目录下精确加载该 HTML 的文本内容，并做好前置的安全校验防范由于越权（如 `fname="../key.pem"`）产生的读取漏洞。
*   执行完成，将结果组装为 `{"role": "tool", "content": "..."}` 的形式。
*   **SSE 实时下发结果**：向前端发送 `event: tool_result`，前端此时将原本黄色的加载 Badge 变更为绿色的 `✓ 已读取`。

### (5) 综合总结与文本流式输出 (第二轮)
*   将查阅到的 SOP 长文原样塞回对话上下文，再次请求 `client.chat.completions.create`。
*   大模型综合刚获取到的真实流程规范，结合用户问题，开始逐字吐出最终的排查流程或建议。
*   后端捕获这些字符，以 `event: message` 将数据块不断推流到前端，实现打字机效果，直至输出 `[DONE]` 结束此轮会话。

---

## 3. 设计亮点与问题防范

- **Tool Call 流式拦截与分流**：使用原生的 `openai` 库结合手动 SSE 生成发生器，没有借助笨重的 LangChain。我们能够绝对精确地拦截到 tool 参数解析的时刻，直接下发前端。
- **防止流尾报错 (IndexError)**：在异步获取 `chunk` 的过程中，强化了 `if not chunk.choices: continue` 的空判断，防止部分模型底座在流截断的最后一帧 `finish_reason` 触发异常，提高了工程的鲁棒性。
- **配置与鉴权剥离**：使用 `config.json` 替代硬编码环境变量，并在页面提供便捷的抽屉配置入口。方便直接对接国产各类兼容模型的廉价接口。
