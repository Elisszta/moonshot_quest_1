# On-Call 智能助手项目文档 (Project README)

本项目是一个分阶段构建的智能化运维 SOP (Standard Operating Procedure) 检索与问答系统。它整合了传统的关键词搜索、现代的向量语义检索以及具备自主工具调用能力的 AI Agent。

---

## 1. 快速启动 (How to Start)

### 依赖环境
- **Python**: 3.9+
- **环境管理**: 推荐使用 `uv` (也可使用 `pip`)

### 安装依赖
```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 启动服务
```bash
# 启动后默认监听在 http://127.0.0.1:8000
uv run main.py
```

---

## 2. 网页入口与功能 (Web Interfaces)

启动服务后，可以通过浏览器访问以下路由：

- **主页控制中心 (`/`)**: 整合了三个阶段的视觉控制面板，提供一键跳转功能。
- **Phase 1: 基础检索 (`/v1/`)**: 提供纯关键词匹配的搜索页面。
- **Phase 2: 语义检索 (`/v2/`)**: 展示具备语义理解、重排序及标题增强能力的搜索界面。
- **Phase 3: 智能 Agent (`/v3/`)**: 对话式助手界面，支持查看 Agent 查阅 SOP 的全过程及 SSE 流式反馈。

---

## 3. 重要文档位置 (Core Documents)

### 阶段总结文档
- **阶段一总结**: `phase1_summary.md` (关键词搜索引擎实现)
- **阶段二总结**: `phase2_summary.md` (语义向量检索与 RRF 融合)
- **阶段三总结**: `phase3_summary.md` (基于 Tool Calling 的 On-Call 助手)

### 测试与分析报告
- **核心测试報告**: `test_report.md` (包含三阶段各功能的 QPS 压测与场景验证)
- **自动化测试脚本**: `test_suite.py` (支持功能验证与多线程并发负载测试)

---

## 4. 目录与文件组成 (Project Structure)

```text
.
├── main.py                 # 应用入口，整合路由与生命周期管理
├── config.json             # AI 服务配置（API Key, Base URL, 模型, 向量模式）
├── api/                    # 路由层
│   ├── v1/router.py        # Phase 1 关键词搜索端点
│   ├── v2/router.py        # Phase 2 语义搜索端点
│   └── v3/router.py        # Phase 3 Agent 对话与配置端点
├── services/               # 业务逻辑层
│   ├── document_store.py   # 文档内存商店及初始化加载
│   ├── html_parser.py      # SOP 文档解析服务
│   ├── search_engine.py    # 混合检索引擎核心算法 (Keyword + RRF)
│   ├── embedding.py        # 向量存储、BGE 模型推理与持久化 (pkl)
│   ├── reranker.py         # Cross-Encoder 重排序逻辑
│   └── agent.py            # Phase 3 Agent 工具调用与 SSE 流式生成器
├── templates/              # 前端模板 (Jinja2)
│   ├── index.html          # 主页控制中心
│   ├── v1/index.html       # Phase 1 搜索前端
│   ├── v2/index.html       # Phase 2 搜索前端
│   └── v3/index.html       # Phase 3 Agent 聊天前端 (支持可视化 Tool Call)
├── data/                   # 数据存储
│   ├── sop-*.html          # 10 份原始文档集
│   └── vector_store.pkl    # 向量索引持久化文件 (冷启动优化核心)
├── test_suite.py           # API 验证与压力测试套件
└── test_report.md          # 最终测试评估报告
```

---

## 5. 核心技术特性
- **高性能 (P1)**: 关键词检索 QPS 突破 1000+。
- **高精度 (P2)**: 引入 BGE 模型语义理解，解决口语化查询问题。
- **高透明度 (P3)**: Agent 对话过程完全可视化，通过 SSE 实时上报工具调用桩位。
- **秒级启动**: 依托 `.pkl` 持久化，无需重复计算长文档向量即刻提供语义搜索能力。
