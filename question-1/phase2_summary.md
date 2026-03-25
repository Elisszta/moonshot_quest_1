# Phase 2：语义搜索 — 思路与流程

## 整体思路

Phase 2 在 Phase 1 关键词检索的基础上，引入**向量语义搜索**与**交叉编码器重排序**，实现语义匹配能力。最终通过 RRF（倒数排名融合）将多路搜索结果结合，并采用 **Top-K 平均评分** 与 **标题信号增强** 确保搜索结果的精准度。

---

## 技术选型

| 组件 | 选择 | 说明 |
|------|------|------|
| 向量编码模型 | `BAAI/bge-small-zh-v1.5` | 中文嵌入模型，维度 512 |
| 重排序模型 | `BAAI/bge-reranker-base` | Cross-Encoder，用于 Top-5 文档精排 |
| 混合策略 | RRF (Reciprocal Rank Fusion) | 关键词与语义双路融合，`vector_weight=0.8` |
| 持久化存储 | `vector_store.pkl` | 序列化存储向量、切片及文档元数据，实现毫秒级启动 |

---

## 数据流程

```
1. 文档初始化与持久化决策（load_initial_data）
        │
        ├──► 步骤 A：尝试加载 data/vector_store.pkl
        │    ├─── [成功] 内存中恢复所有已计算向量、切片及元数据（SOP ID 映射）
        │    └─── [失败] 内存中初始化为空字典
        │
        ├──► 步骤 B：扫描 data/ 目录下的所有 HTML 文件，对每个文档执行：
        │    ├─── [Case 1: pkl 已包含该 doc_id]
        │    │    └─── 直接从 pkl 加载，跳过推理（skip_embedding=True），实现秒开。
        │    └─── [Case 2: pkl 缺失该 doc_id (新增文件)]
        │         └─── 执行完整流水线：HTML 解析 → 400字切片 → BGE 推理生成向量。
        │
        └──► 步骤 C：保存成果
             └─── 若扫描过程中产生了任何 Case 2 的新增向量，则触发 vec_store.save()。

2. 查询处理（GET /v2/search?q=...）
        │
        ├──► [路径A] 关键词检索（search_v1）
        │         文本包含匹配 → 得到 kw_ranks
        │
        └──► [路径B] 语义检索（VectorStore.search）
                  query → encode → 计算所有 chunk embedding 的点积
                  评分机制：Top-K (K=3) 平均分 (Mean Pooling) ──► 得到 sem_ranks

3. RRF 融合
        score = 0.2 × (1 / (60 + kw_rank)) + 0.8 × (1 / (60 + sem_rank))
        按 combined_score 排序，取 Top-5

4. Cross-Encoder 重排序（reranker.py）
        对 Top-5 文档构造 [query, 增强后的doc_text] 对
        增强方式：标题重复 3 次拼接在头部，确保精排阶段标题信号显著
        CrossEncoder.predict() → 得到最终相关性分数并排序返回
```

---

## 关键代码位置

| 文件 | 职责 |
|------|------|
| `api/v2/router.py` | 路由入口，触发多路检索与 RRF |
| `services/embedding.py` | `VectorStore`：Top-K 平均评分逻辑、本地序列化（pkl）读写 |
| `services/search_engine.py` | `search_v2()`：实现 RRF 融合算法 |
| `services/reranker.py` | `rerank()`：实现标题信号增强与 Cross-Encoder 精排 |
| `services/document_store.py` | 启动时的增量加载控制逻辑 |

---

## 启动与存储分析

- **冷启动加速**：通过 `vector_store.pkl` 缓存，大规模文档下的服务启动时间从分钟级降低至**毫秒级**。
- **存储结构**：采用 `pickle` 序列化，内部包含：
    - `embeddings`: {doc_id: np.ndarray}
    - `chunks`: {doc_id: List[str]}
    - `metadata`: {doc_id: {"title": str}} (为 Phase 3 Agent 快速定位提供支持)
- **运行环境**：需安装 `protobuf` 依赖；离线环境需设置 `TRANSFORMERS_OFFLINE=1`。

---

## 验证结果

针对“服务器挂了”等口语化场景，通过**标题增强**与**Top-K 平均分**的联合作用，成功解决了评分偏见问题。

| 查询 | 期望 | 实际 Top-1 | 通过 |
|------|------|------------|------|
| `服务器挂了` | sop-001、sop-004 靠前 | **sop-001** (sop-004 #3) | ✅ |
| `黑客攻击` | sop-005 靠前 | sop-005 | ✅ |
| `机器学习模型出问题` | sop-008 靠前 | sop-008 | ✅ |

---

## 已解决的逻辑缺陷

1.  **评分偏见 (Max-Pooling Resolved)**：不再被单句极高相似度误导，采用 Top-3 Mean Pooling 更好地反映文档整体相关性。
2.  **冷启动延迟 (Persistence Implemented)**：实现了基于 pkl 的磁盘缓存，无需每次重启都进行重计算。
3.  **Phase 3 关联性**：持久化数据中显式保存了向量与对应 SOP ID、Title 的映射，Agent 可直接利用该文件进行快速知识库检索。
