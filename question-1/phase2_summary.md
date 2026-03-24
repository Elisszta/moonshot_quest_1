# Phase 2：语义搜索 — 思路与流程

## 整体思路

Phase 2 在 Phase 1 关键词检索的基础上，引入**向量语义搜索**与**交叉编码器重排序**，实现"查询词不需要精确出现在文档中"的语义匹配能力。最终通过 RRF（倒数排名融合）将关键词结果与语义结果混合，再用 Cross-Encoder 对 top-5 做精细重排。

---

## 技术选型

| 组件 | 选择 | 说明 |
|------|------|------|
| 向量编码模型 | `BAAI/bge-small-zh-v1.5` | 中文小模型，速度快，适合本地部署 |
| 重排序模型 | `BAAI/bge-reranker-base` | Cross-Encoder，精度更高，用于 top-5 精排 |
| 混合策略 | RRF (Reciprocal Rank Fusion) | 关键词与语义双路融合，`vector_weight=0.8` |

---

## 数据流程

```
1. 文档入库（启动时自动加载 data/*.html）
        │
        ▼
   html_parser.py → 提取纯文本（去掉 script/style 标签）
        │
        ▼
   embedding.py::chunk_text()
        │  将文档分割为 400 字 chunk，重叠 50 字
        ▼
   SentenceTransformer.encode()
        │  对每个 chunk 生成归一化向量
        ▼
   VectorStore.doc_embeddings[doc_id] = np.ndarray

2. 查询处理（GET /v2/search?q=...）
        │
        ├──► [路径A] 关键词检索（search_v1）
        │         文本包含匹配 → 按出现次数评分 → 得到 kw_ranks
        │
        └──► [路径B] 语义检索（VectorStore.search）
                  query → encode → dot product 与所有 chunk embedding
                  取每篇文档的 max chunk similarity → 得到 sem_ranks

3. RRF 融合
        score = 0.2 × (1 / (60 + kw_rank))
              + 0.8 × (1 / (60 + sem_rank))
        按 combined_score 排序，取 top-5

4. Cross-Encoder 重排序（reranker.py）
        对 top-5 文档，构造 [query, doc_text] 对
        CrossEncoder.predict() → 精准相关性分数
        按新分数重新排列，返回最终结果
```

---

## 关键代码位置

| 文件 | 职责 |
|------|------|
| `api/v2/router.py` | 路由入口，调用 `search_v2(q, use_rrf=True, vector_weight=0.8)` |
| `services/embedding.py` | `VectorStore`：文档分块、向量编码、语义检索 |
| `services/search_engine.py` | `search_v2()`：RRF 融合逻辑 |
| `services/reranker.py` | `rerank()`：Cross-Encoder 精排 |
| `services/document_store.py` | 文档入库时同步写入 `VectorStore` |
| `services/html_parser.py` | HTML → 纯文本提取 |

---

## 启动注意事项

- 依赖 `protobuf` 包（`uv pip install protobuf`），否则 CrossEncoder tokenizer 加载报错
- 无外网环境需设置 `TRANSFORMERS_OFFLINE=1`，两个模型均已缓存在 `~/.cache/huggingface/`
- 启动命令：
  ```bash
  TRANSFORMERS_OFFLINE=1 .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
  ```

---

## 验证结果

| 查询 | 期望 | 实际 top-1 | 通过 |
|------|------|------------|------|
| `服务器挂了` | sop-001、sop-004 靠前 | sop-010（sop-001 #2，sop-004 #4） | ⚠️ 部分 |
| `黑客攻击` | sop-005 靠前 | sop-005（score 0.36） | ✅ |
| `机器学习模型出问题` | sop-008 靠前 | sop-008（score 0.88） | ✅ |
