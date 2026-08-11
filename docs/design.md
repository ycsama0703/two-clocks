# 双时钟检索基准 — 立项状态

> 2026-08-10。从 alphagap 2026-08-10-MECH-AI-2 出发，经四轮承重验证后重新定位的结果。
> 每条结论都标了验证强度：**确认** = 读代码/数据实证；**未证伪** = 检索无近邻但未穷尽；**欠债** = 尚未验。

## 一句话

现有长上下文检索基准全部是 **uni-temporal**（只有 valid time）。真实的版本演化语料有**两个可以背离的时钟**，
我们用 SEC EDGAR 构建第一个 **bitemporal** 检索基准，并给出退化量的闭式预测。

## 论证链

1. 长上下文检索基准（BabiLong 等）隐含假设 **文本顺序 = 完整的时间信息**
2. 这在合成语料里必然成立 —— 语料就是按时间顺序生成的
3. 真实语料有 `(event time, availability time)` 两个轴，文本顺序只能编码其中一个
4. 因此基于相对位置的时间表示存在**不可消除的碰撞**（可证，见闭式解）
5. 而这类错误的后果与 uni-temporal 错误**性质不同**：
   - uni-temporal 失败 → 检索到时间不匹配的证据 → 答案可能错
   - **bitemporal 失败 → 用了当时不可知的信息 → 前视偏差 → 结论整体作废**

金融的不可替代性不是「应用场景」，是**唯一性**：SEC filing date 是法定、不可篡改、精确到日的披露时点。
维基编辑史没有法律意义上的可得时间，新闻没有同一事实的修订链，合成数据没有真实分布。

## 验证状态

| # | 断言 | 强度 | 证据 |
|---|---|---|---|
| 1 | BabiLong 是单时钟，两轴强制对齐 | **确认** | `retrieval_babilong.py:64` "Shuffles noise chunks with fact chunks **while keeping relative order of facts intact**"；论文 QA3 为 state-change/object-tracking，supersession 沿唯一故事轴 |
| 2 | Q-RAG scorer 不含绝对时间 | **确认** | `q_module.py:43-47` state 嵌入无 positions；action 仅经 RoPE 注入一个标量 |
| 3 | `interpolate_factor=1`、`step_size=20` | **确认** | 5 个 algo 配置 + 7 个 env 配置全部如此 |
| 4 | torch 整数量化是截断向零 | **确认** | 实测 `0.5→0, 1.5→1`，与 numpy 一致 |
| 5 | TDBench 是 uni-temporal | **确认** | 作者原文用 "uni-temporal"，明说无 transaction-time 维度 |
| 6 | TEMPO 不做 as-of | **确认** | HF `tempo26/Tempo` schema：`documents` 仅 `id`+`content`，**无任何时间戳字段**；hard negatives 靠"从正文读日期"区分而非按日期过滤；指标由 LLM-as-judge 计算。语料为 Stack Exchange 13 域。且其对比表自称是唯一在 temporal/reasoning/expert/step/cross 五列全打勾的基准 —— 最全面的时序检索基准仍无第二个时钟 |
| 7 | 无人做双时钟检索基准 | **未证伪** | FinTMMBench 不含 restatement；When Benchmarks Age 处理的是基准自身过时 |
| 8 | RoMem 加第二相位轴难不难 | **欠债** | 新 framing 下不再是承重墙（dual-clock 只作 upper bound，不主张为方法贡献） |

## 闭式解

### 支一 — 双时钟间隔（信息论层，通用）

恒等式（无假设）：

    E|a_j - a_i| = (P / C(k,2)) * sum_{i<j} (q_j - q_i)

等距格点 `q_i = i-1` 下化简为 `(k+1)P/3`。

- **适用范围**：`k ∈ {2,3}`，覆盖 78.5%（34,616 条序列）
- **参数**：`P ≈ 364–365 天`（364 单值占 30.9%，52 周财年；364 与 365 在 ±3 天容差下无法区分）
- **验证**：k=3 预测 485.33，实测中位 485。**注意 k=2 是循环的**（P 由 k=2 数据定义），不算独立验证
- **k≥4 失效及原因**：跨度被 comparative reporting 规则锁死在约 2 年（10-K 展示当年+前两年，10-Q 展示当季+去年同季），
  k 大只表示该数字同时出现在季报与年报链，版本在同一跨度内更密，first gap 从 364 天降到 74 天且不落任何单一格点

### 支二 — 分辨率坍缩（实现层，Q-RAG 特有）

    P_collide(Δi) = max(0, 1 - 18·Δi / (L-1))

- 段内位置铺在 `[0, 18]`，`t.type(torch.int32)` 截断后**只有 19 个可区分格**，与段长无关（L=20/100/1000/5000 实测均为 19）
- 相邻候选（Δi=1）：L=100 → 81.8%，L=1000 → 98.2%
- **现实取值**：多步检索 H=4–6 时段数为 m+1，平均段长约 1000/7≈143，碰撞率约 **87%**（不是 98%）
- **2026-08-10 终验（用 Q-RAG 真实 RoPE 层）**：三个数完全一致 —— 预测碰撞率 = 相邻同格率 =
  **RoPE 输出位级相同率**（L=50/200/1000 → 0.633/0.910/0.982），且 `same-bin ⟹ identical` 恒真。
  交叉检验 `ρ=12.1 vs 12.9 → max abs diff = 0.000e+00`（完全相同），`ρ=12.1 vs 13.1 → 1.876`。
  **不是分辨率不足，是位置通道的信息差严格为零。**

### 实现路径（最大风险已消除）

`PositionalRotaryEmbedding` 与 `RelativePositionProcessor` **可脱离训练流程独立驱动**，
因此 `relative-only` 配置**不需要复现 Q-RAG 的训练**：

```
任意 embedder 编码 chunk 文本 → RelativePositionProcessor 算 ρ → PositionalRotaryEmbedding 施加
```

依赖仅 `einops` + `rotary_embedding_torch`（876 KB）。
**装时务必 `--no-deps`** —— 否则 pip 拖入整个 CUDA 依赖树（实测 4.6 GB），而 luyao4 磁盘已 88% 满。
`RelativePositionProcessor` 只用 numpy，可直接摘抄，无需引入 `envs.text_env` 的其余依赖。

## 数据资产（luyao4 `~/repairable-experience`）

```
碰撞对          25,574 个（srd≥1%、window≥30d、rep_lag∈[0,400]、first_val≠0）
                50 家公司 / 1,774 个 concept / 2007-2026
原始数据        data/edgar/companyfacts  63 家 266 MB，含完整 a_i 序列
重建脚本        rebuild_series.py        4 秒，44,071 条多版本序列
体检脚本        dualclock_audit2.py / level0_leakage.py / level1_value_channel.py / level1_grouped.py
```

**注意**：25,574 是**候选**碰撞对。brief 意义上的碰撞还要求两版本在语料序列中足够接近（Δi 小），
这取决于 chunk 化与语料组织方式，**从 XBRL 数据无法验证**，目前是假设。

### 关键分布参数

```
P（版本间隔）           364 天，30.9% 落在单值上
reporting lag           10-K 中位 51 天（5–95%: 32–59）
                        10-Q 中位 30 天（5–95%: 20–40）
可修订寿命              约 2 年（comparative reporting 上限）
n_filings 分布          k=2 占 54.6%，k=3 占 25.2%
正式 /A 修订            仅 1.8% —— 主流是 comparative restatement 而非 amendment
```

## Phase-0 结果

| 检查 | 结果 |
|---|---|
| Level 0 元数据泄漏 | `fy` 97.2% / `accn` 100% / `frame` 76.6% 可区分版本 → **元数据必须屏蔽，漏一个字段实验作废** |
| Level 0 方向渠道 | 后来的值更小 54.9% → 接近随机，干净 |
| Level 1 数值渠道上界 | GroupKFold by concept **0.627**；by ticker 0.611；随机 CV 0.665（泄漏 +0.039） |

**floor = 0.62 必须画进主实验的对照图**，否则 relative-only 跑出 0.63 会被误读成位置编码有效。

## 语料（已构建，luyao4 `~/repairable-experience/bench/`）

```
chunks.jsonl    40,784   id / text / ticker / concept / event_time / avail_time / value
queries.jsonl   20,392   query / as_of / gold_id / distractor_id / window_days / n_versions
生成脚本        build_bench.py，10 秒
```

chunk 文本模板只含 event time：
`"{ticker} reported {label} of {value} {unit} for the period ended {period_end}."`

**碰撞不变量 20,392/20,392 全部成立**：gold 与 distractor 的 event_time 相同、avail_time 不同、
as_of 恰好使 gold 可得而 distractor 不可得、两者文本确实不同。

### 构建时踩到的泄漏（写进 dataset construction 章节）

SEC 的 concept label 自带 **`(Deprecated YYYY-MM-DD)`** 废弃标记。一个 tag 在某日被废弃，
意味着使用它的 filing 必然早于该日——**废弃日期给出 availability 的绝对上界**。
首次构建有 1,532 个 chunk（3.8%）携带此类日期，其中 5 个直接印出了自己的 `avail_time`
（MSFT `Revenue, Net (Deprecated 2018-01-31)` 的 avail_time 恰为 2018-01-31）。
现已在 `humanise()` 里剥除，重建后 `event_time 以外的日期 = 0`。

**教训：双时钟语料的泄漏可以从元数据的元数据进来。** 泄漏检查必须用词边界——首版用子串匹配，
`"fy"` 命中 `Quali`**fy**`ing`，报了 148 个假阳性，差点掩盖 1,532 个真问题。

**结构性保证**：gold 与 distractor 同 concept、同 period，label 逐字相同，因此 label 渠道
在构造上无法区分两者；唯一差异是数值，其可分性上界已由 Level 1 测定为 0.62。

## Baseline 清单

| 系统 | 处理什么 | 角色 |
|---|---|---|
| Q-RAG (`MS9nWFY7LG`) | 相对位置编码的长上下文多步检索，BabiLong SOTA | 主 baseline |
| RoMem (2604.11544) | 连续相位旋转处理 valid-time 时效，已零样本测过金融 | 单时钟对照 |
| TOKI (2606.06240) | bitemporal 算子代数，LLM-agent 记忆写时并发控制 | 符号路线对照 |
| 2606.26511 | valid_from/valid_to/superseded_by 的符号 as-of 层 | 符号路线对照 |
| TDBench / TEMPO | uni-temporal 检索基准 | 定位对比，非直接 baseline |

四个 baseline 全部退化 → 是一类机制的边界；只有 Q-RAG 退化 → 是一个实现的问题。

## 欠债

1. **S2 API key 未配** —— novelty probe 的 hits 排序失效（citations 全 0），文献检索可靠性打折。
   需本人去 semanticscholar.org/product/api 申请，填进 `.env` 已有的空位 `S2_API_KEY=`
2. **chunk 化方案未定** —— 一个决策同时卡住两件事：
   - 25,574 对能否构成真正的**段内**碰撞（位置相邻性）
   - 段长 L 的分布 → 支二的效应量（L=143 时约 87%，L=1000 时 98.2%）
   这是基准设计的第一个实质决策，不是验证问题

**已还清**：TEMPO 全文（改用 HF schema 验证，比读 59 页 PDF 更直接且更硬）

## 下一步

主实验（brief 原设计）：约 500 对，四种输入 `no-time / relative-only / absolute / dual-clock`，
对照 floor=0.62。GO 条件见 `~/workspace/projects/alphagap/briefs/2026-08-10-MECH-AI-2.md` §6。

最大不确定性不在数据（数据齐了），在**复现 Q-RAG 的 scorer**（代码在 `github.com/griver/Q-RAG`，3.5 MB）。


## 复核记录（2026-08-10）

对 Phase-0 六项做了一次事后复核，发现两个实质问题、三个次要观察。

**问题 1 — floor 测错了样本集（已修正）。**
`level1_grouped.py` 在 25,574 对上测得 0.627，但实际语料是 `build_bench.py`
额外加了 `n_filings in {2,3}` 之后的 20,392 对。在真正的语料上重测：

```
GroupKFold by concept   0.6162  (+/- 0.0054)   <- 红线
GroupKFold by ticker    0.6016  (+/- 0.0179)
```

预注册上界 0.62 侥幸仍然成立，但依据是错的。**天花板必须在实验实际要跑的那个集合上测。**

**问题 2 — 项③ 采样偏向近期（未修）。**
`phase0_item3.py` 按 `filed` 倒序取样，且只在 SEC submissions 的 `recent`
（最近 1000 条）里匹配，59 条样本全部落在 2024-2026。语料跨 2007-2026，
EDGAR 早期的 acceptance 行为未经检验。**当前结论只对近期 filing 成立**，
补测需要拉 submissions 的分片历史文件。

**次要观察**
- 项② 做了代码审计与规则恢复实测，但 brief 要求的"逐字段画出 scorer 可见信息"
  未落成系统文档
- 项⑥ dual-clock 得 0.9987 而非确定性规则的 1.0000，这 0.13% 的差距未解释
- 项⑤ TF-IDF 仅跑 6,000 样本子集，未全量


## v2 语料重建（2026-08-10）

Phase-0 项③ 的分层补测（n=136，覆盖 2007-2026 三个年代）发现：
`companyfacts.filed` 与 `SEC.filingDate` **136/136 完全一致**，但有 1 例
EDGAR 的 acceptance 晚于法定 filing date **36 天**
（ABT `0001104659-10-033097`：filed 2010-05-04，accepted 2010-06-09）。
按 `filed` 标注可得性，会在那 36 天里把一份尚不可见的文档标为已可得
—— 正是本基准要检出的错误类型，出现在自己的 gold label 里。

**修正**：`avail_time = max(filingDate, acceptanceDate)`。
拉取 63 家公司全部 submissions 分片，得 462,345 个 accession 的映射
（`data/acceptance.json`），1,657 个 fact entry 的可得时间因此后移。
`build_bench.py` 同时改为自包含 —— 直接从 companyfacts 计算碰撞对，
不再依赖用旧语义算出的 `revisions.csv`。

| | v1 (filed) | v2 (max) |
|---|---|---|
| queries / chunks | 20,392 / 40,784 | **21,268 / 42,536** |
| tickers | 50 | **62** |
| floor by concept | 0.6162 | **0.6128** |
| floor by ticker | 0.6016 | 0.5978 |
| Phase-0 [6] dual-clock | 0.9987 | **1.0000** |
| Phase-0 [6] relative | 0.5014 | 0.5065 |
| Phase-0 [4] | 1.0000 / 1.0000 | 1.0000 / 1.0000 |
| Phase-0 [5] raw / masked | 0.509 / 0.506 | 0.508 / 0.509 |
| 碰撞窗口中位 | 364 | 364（k=2 有 91.8% 落在 364±7） |

**复核时那个未解释的 0.13% 缺口，就是前视偏差污染本身。**
项⑥ 的确定性规则 `as_of >= avail_time` 在 v1 下对少数样本是错的，
所以 GBM 学不到 1.0000；换成 `max()` 后归零。这反过来确认了新语义正确。

预注册区间 `[0.50, 0.62]` 在 v2 下仍然成立，未作改动。


## Reproducing Q-RAG's trained encoder (E1's fifth system)

Five checkpoints are published under the `Q-RAG` org on HuggingFace. **Only one
is usable for this benchmark:**

```
qrag-ft-contriever-on-babilong_qa3     positions_processor: relative   <- USE THIS
qrag-ft-contriever-on-babilong_qa2     (babilong, also relative)
qrag-ft-e5-on-hotpotqa                 positions_processor: none
qrag-ft-e5-on-musique                  none
qrag-ft-gte-on-hotpotqa_musique        none
```

The HotpotQA/MuSiQue configs set `positions_processor: none`, so rho_t was never
trained in them. Evaluating those would measure a model that has never seen the
positional mechanism under test — the result would look like evidence and mean
nothing.

The BabiLong QA3 config confirms the two facts the closed form depends on:
`positions_processor: relative` and `interpolate_factor: 1` (so positions are
truncated to int32 and a segment holds at most 19 distinguishable slots).

### Loading it

The checkpoint is a raw training dict, not an HF model directory:

```
critic / policy / random_policy / v_net_target / action_embed_target /
critic_optim / scheduler / alpha
```

`action_embed_target` is the candidate tower. 204 tensors, of which 199 sit under
`action_embed.model.model.` in standard BERT layout. The other five are
telling:

```
action_embed.model.cls_token
action_embed.model.sep_token
action_embed.model.head.weight / head.bias
action_embed.rotary_emb.freqs        <- the rho_t frequency table itself
```

`facebook/contriever` publishes only `.bin`, and transformers >= 4.56 refuses to
`torch.load` a `.bin` on torch < 2.6 (CVE-2025-32434). Do not downgrade
transformers: contriever's published weights are not needed. Contriever is
architecturally BERT, so instantiate an empty `BertModel` from an inferred config
and load the 199 tensors into it (`src/qrag_encoder.py`). Dimensions are read off
the weights: vocab 30522, hidden 768, 12 layers, intermediate 3072.

The load must be strict on the encoder body. A partial load still runs and still
produces plausible numbers — `missing` must be zero apart from `pooler.*`, which
mean-pooling does not use.

### An immediate observation

Two collision candidates differing only in their numeric value embed at
**cos = 0.9995** under this encoder. That is the microscopic reason the `no-time`
baseline sits near chance: the text channel barely separates them at all.
