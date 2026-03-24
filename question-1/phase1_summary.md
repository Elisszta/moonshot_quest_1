# Phase 1: 搜索引擎实现总结

## 1. 目标与需求
实现一个基于关键词的文档搜索引擎，作为 On-Call 助手的基础设施。
- **环境要求**：使用 `uv` 管理依赖环境。
- **技术栈**：FastAPI + Python + BeautifulSoup + Jinja2。
- **功能点**：
  1. POST 接口支持录入并解析 HTML 文档，提取标题及纯文本内容（需忽略 `<script>` 和 `<style>` 等无用标签）。
  2. GET 接口基于关键词对保存的文档进行文本搜索，并且根据命中频率实现基础打分，返回查询及其匹配结果的片段（snippet）。
  3. 提供一个简单的前端搜索可视化页面（`/v1/` 返回页面资源）。

## 2. 核心架构与模块
代码分别抽离成了多个模块，确保可维护性及对 Phase 2 和 Phase 3 的前向兼容：
- `main.py`：应用入口，加载依赖并在启动时触发预处理任务，加载了多个路由前缀（`/v1`, `/v2`, `/v3`）。
- `api/v1/router.py`：Phase 1 的路由模块，提供 `/v1/documents`, `/v1/search` 及 `/v1/` 页面渲染。
- `services/html_parser.py`：HTML 解析服务，使用 BeautifulSoup4 提取文本、屏蔽异常标签内容及识别标题。
- `services/document_store.py`：内存文档数据库，提供在应用启动时自动加载 `data/` 目录中的 HTML SOP 初始化。
- `services/search_engine.py`：简单的搜索引擎逻辑，包含关键词匹配算法与打分、并生成带上下文的字符串片段（Snippet）。
- `templates/v1/index.html`：基础搜索入口的简单交互界面。

## 3. 实现与验证结果
全部功能已成功实现，并顺利通过本地通过了 README 指定的所有预设规则测试，测试情况如下：
- `GET /v1/search?q=OOM` -> 返回了由于内存溢出故障相关内容的 `sop-001` 等文档。
- `GET /v1/search?q=故障` -> 正确返回大量匹配故障关键词的 SOP（按照提及频率进行初步打分并排序）。
- `GET /v1/search?q=replication` -> 由于出现在 script 内，按需忽略并未返回。
- `GET /v1/search?q=CDN` -> 成功关联到前端以及网络加速相关 SOP，包含 `sop-003` 及 `sop-010`。
- `GET /v1/search?q=&` -> 成功通过 URL 编码方式找到了内含 `&` 字符的对应文件，例如 `sop-008` 等。

## 4. 后续规划
当前项目中已存在预留的 `/v2` （由 `api/v2/router.py` 支持的语义搜索）及 `/v3`（由 `api/v3/router.py` 支持的对答 Agent）的骨架模块，接下来只需直接在这两处模块内部进行对应需求的迭代即可。
