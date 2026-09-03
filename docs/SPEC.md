# PlotLoop Hub — Loop 契约规范 v0.2

> 定义一个 loop 在 Hub 里长什么样。核心目标：**让接收方的 Agent 读完就能把它搭起来。**
>
> **v0.2 变更**（2026-09-04，据一轮竞品与开源调研修订）：新增运行证据规范 §5、防腐烂重放 §6、`pull_request_target` 安全红线 §7、GitHub Actions 硬约束 §8；`runs/` 结构改为带 manifest；默认可见性改为私有；proof-of-work 口径从"不可伪造"降级为"可审计"。

---

## 0. 设计原则

1. 🔴 **`LOOP.md` 是给 Agent 读的契约，不是给人读的文档。** 人读 `README.md`。小节固定、缺一不可——接收方 Agent 依赖固定结构来知道该问用户要什么。
2. 🔴 **声明，不是代码。** `LOOP.md` 描述"要做什么"，不含可执行脚本。执行方式由接收方的 Agent 和运行时决定——这是运行时无关的前提。
3. 🔴 **凭证零容忍。** 任何 key / token / cookie / 内部 URL 都不得出现，只能在「需要你提供」里声明**名字和用途**。
4. 🔴 **默认私有，公开是逐字段显式选择。** *(v0.2 新增)* 依据：StravaLeaks 中被监测一年后仅约 7% 的人改为私密——**默认值就是绝大多数人的最终值**。工作 loop 泄露的客户、项目、竞争意图比跑步路线敏感得多。
5. 🔴 **上架必须带运行证据，不是提交一个 prompt。** *(v0.2 新增)* 依据：myExperiment 92 个工作流复跑近 80% 失败、仅约 5% 用户上传过。只收定义会同时重演 myExperiment（腐烂）和 GPT Store（供给泛滥）。
6. **公共情报型有 `runs/`，私域工作流型只有 `samples/`。**

---

## 1. 目录结构

```
loops/<slug>/
  LOOP.md                          # 必需 · 给 Agent 读的安装契约
  loop.yaml                        # 必需 · 结构化元数据
  README.md                        # 必需 · 给人读的介绍（含隐私等级）
  adapters/                        # 可选 · claude-code / codex / orca / n8n 转换说明
  runs/YYYY/MM/YYYY-MM-DD-<id>/    # kind: public-feed 必需 · 见 §5
    output.md
    manifest.json
    sources.json
  samples/example-output.md        # kind: pattern-only 必需 · 脱敏样例
  feed.xml                         # 自动生成，勿手改
```

`<slug>`：小写 kebab-case，全 Hub 唯一。

---

## 2. `loop.yaml` 字段

```yaml
# ── 身份 ──────────────────────────────────
id: ad-platform-ai-tracker
title: 全球主流广告平台 AI 产品与合规变更追踪
summary: 每日扫主流广告平台官方一手信源，过滤营销噪音，只留影响投放决策的变更
author: granken
created: 2026-06-01

# ── 分类 ──────────────────────────────────
category: ads-platform          # 见 §3 品类枚举
kind: public-feed               # public-feed | pattern-only
tags: [广告投放, 合规, 每日]

# ── 可见性（🔴 默认私有）────────────────────
visibility:
  definition: public            # 定义是否公开
  outputs: private              # 🔴 默认 private，公开需逐项确认
  stats: public                 # 运行统计（天数/条数）可公开
  author_identity: public       # 署名是否公开

# ── 运行 ──────────────────────────────────
trigger:
  schedule: "0 8 * * *"         # 5 段 cron；⚠️ 见 §8，不承诺准点
  timezone: Asia/Shanghai
runtime:
  agnostic: true
  verified_on: [claude-code, codex]   # 作者实际验证过的运行时

# ── 依赖（🔴 防腐烂）────────────────────────
dependencies:
  - name: feishu-open-api
    version_pinned: "v1"
    fragility: medium           # low | medium | high
  - name: 各平台官方 changelog 页面结构
    version_pinned: null
    fragility: high             # 页面改版即失效

# ── 产出 ──────────────────────────────────
output:
  format: markdown
  language: zh
  delivery: [feishu-doc, feishu-group]

# ── 装载时需要用户提供 ─────────────────────
# 🔴 只写名字和用途，绝不写值
requires:
  - key: FEISHU_APP_ID
    secret: true
    purpose: 推送产出到飞书
  - key: TARGET_DOC_TOKEN
    secret: false
    purpose: 追加写入的目标文档

# ── 健康度（Actions 自动写，勿手改）────────
health:
  last_run: 2026-09-03
  streak_days: 94
  runs_total: 94
  status: healthy               # healthy | stale | broken
  replay_success_rate: 0.92     # 🔴 全新环境重放成功率，见 §6
```

**`kind` 的两种取值决定一切：**

| kind | 含义 | 有 `runs/` | 有 `samples/` | 主要价值 |
|---|---|---|---|---|
| `public-feed` | 公共情报型，产出可公开 | ✅ | — | **订阅**：你不用重复跑 |
| `pattern-only` | 私域工作流型，产出私有 | ❌ | ✅ | **装载**：一句话让你的 Agent 学会 |

---

## 3. 品类枚举（v1 只开三个）

| category | 中文名 | 角色 |
|---|---|---|
| `ads-platform` | 广告投放与平台政策 | 🎯 锚品类 |
| `ai-compliance` | AI 合规与监管追踪 | 💰 变现品类 |
| `ai-market` | AI 赛道产品情报 | 📣 引流品类 |

🔴 **v1 不接受其他品类的投稿。** 窄而深是刻意的：品类按「信息差能否直接换算成钱」× 「信源是否公开但分散枯燥」两轴筛出，二期候选（跨境电商平台政策、人才流动）等锚品类跑通再开。

---

## 4. `LOOP.md` 模板

六个小节，**标题必须一字不差**，Agent 靠它定位。

````markdown
# <Loop 标题>

## 目标

一到三句话：这个 loop 每次运行产出什么，为谁解决什么问题。
写清楚"产出"而不是"过程"。

## 需要你提供

<!-- 🔴 这一节让接收方 Agent 知道该问用户要什么。
     只写名字、是否敏感、用途。绝不写值。 -->

| 名称 | 敏感 | 用途 | 拿不到时 |
|---|---|---|---|
| `FEISHU_APP_ID` | 是 | 推送产出到飞书 | 降级为只写本地文件 |

## 信源

抓哪里、怎么去噪。每条给：名称 + URL + 抓取方式 + 为什么选它。
🔴 去噪规则要写清楚——这通常是一个 loop 最值钱的部分。

## 触发

周期、时点、时区。以及：错过一次要不要补跑。

## 产出格式与投递

产出长什么样（给结构，不给空话）、发到哪、失败了怎么办。

## 验收标准

<!-- 🔴 没这节，Agent 装完不知道对不对。 -->

- [ ] 可勾选的判断条件
- [ ] 明确的失败信号：什么情况算这次跑挂了
````

### 一句话装载

Hub 上每个 loop 页面展示这一行：

```
把 https://hub.plotloop.dev/l/<slug> 读完，
按里面的 LOOP.md 在我的环境里搭一遍，缺什么参数问我。
```

**接收方 Agent 的预期行为**（Hub 首页公开约定）：

1. 读 `LOOP.md`
2. 按「需要你提供」逐项**问用户要**——敏感项提示用户存进自己的密钥管理，**别贴在对话里**
3. 按「触发」在用户自己的运行时里建定时任务
4. 跑一次，对照「验收标准」自查
5. 报告装载结果和第一次产出

> 🟢 **信封依据**：OpenAI 的 ChatGPT Shared Scheduled Tasks（文档更新至 2026-08）分享 instructions + schedule + 时区，**明确不分享历史结果、记忆、文件、凭证**；Airia 分享 Agent 时凭证保留占位符。我们照抄这个信封。

---

## 5. 运行证据规范 *(v0.2 新增)*

每次成功运行在 `runs/YYYY/MM/YYYY-MM-DD-<run-id>/` 下产出三个文件。

**`manifest.json`** —— 运行元数据 + 回执：

```json
{
  "run_id": "2026-09-03-a3f21c",
  "started_at": "2026-09-03T00:00:12Z",
  "ended_at": "2026-09-03T00:03:41Z",
  "status": "success",
  "runtime": "github-actions",
  "workflow_run_url": "https://github.com/<org>/plotloop-hub/actions/runs/...",
  "commit_sha": "a3f21c9",
  "loop_version": "2026-08-20",
  "input_hash": "sha256:...",
  "output_hash": "sha256:...",
  "items_count": 4,
  "cost": { "model_tokens": 18400, "fetches": 12 }
}
```

**`sources.json`** —— 每条信源的 URL、抓取时间、内容 hash，用于溯源和"早于媒体 X 小时"的计算。

**`output.md`** —— 脱敏后的产出正文。

### ⚠️ 口径：可审计，不是不可伪造

`workflow_run_url` + `commit_sha` + 内容 hash **比用户自填强得多，但不是密码学证明**——作者仍可让 loop 产出编造的内容。对标的 AgentBoard 也自认本地日志可编辑、非 cryptographic proof。

**v1 因此规定：**

- 只认 **GitHub-hosted runs**，不认自报
- 🔴 **排行榜不上线**，前 100 个 loop 人工核验
- 用 10 个对抗投稿测试刷 run / 抄产出 / 伪造来源
- 高价值交易场景再接 OIDC / Sigstore

---

## 6. 防腐烂：重放要求 *(v0.2 新增)*

**依据**：myExperiment 92 个工作流复跑样本近 80% 失败，主因是第三方服务变更、不可用、文档不足。

| 规则 | 阈值 |
|---|---|
| 每个 seed loop **每周在全新账户/runner 重放一次** | 强制 |
| 🔴 **首次跑通率低于 80% 不上架** | 硬门槛 |
| `dependencies` 中 `fragility: high` 的项必须在 README 显式提示 | 强制 |
| 重放失败连续 2 次 → 自动置 `status: broken` 并通知作者 | 自动 |

`replay_success_rate` 写进 `loop.yaml` 的 `health`，在 Hub 卡片上公开显示。**这是区别于"又一个模板目录"的核心字段。**

---

## 7. 收录校验（`validate-loop.yml` 在 PR 时强制跑）

| 检查 | 失败即拒 |
|---|---|
| `loop.yaml` 字段完整、`category` 在枚举内 | ✅ |
| `LOOP.md` 六个小节齐全且标题一字不差 | ✅ |
| 🔴 **凭证扫描**：无疑似 key/token/cookie/内部 URL | ✅ |
| 🔴 **`LOOP.md` 不含可执行代码块**（无 `bash`/`sh`/`python` 等语言标记的 fenced block） | ✅ |
| `kind: public-feed` 必须有非空 `runs/` 且含合法 `manifest.json` | ✅ |
| `kind: pattern-only` 必须有非空 `samples/` | ✅ |
| `visibility.outputs` 缺省时按 `private` 处理 | ✅ |
| `health` 字段是否被手改（应只由 Actions 写） | ⚠️ 警告 |

### 🔴 安全红线：外部 PR 的执行边界

**绝不能在 `pull_request_target` 中 checkout 并执行投稿代码**——提交者可借此窃取高权限 token 和 secrets（GitHub 官方安全警告）。

| 阶段 | 允许 | 禁止 |
|---|---|---|
| 外部 PR | 无 secret 的 schema 校验、lint、静态渲染 | 🔴 执行投稿内容、访问 secrets、`pull_request_target` + checkout |
| 合并后 | 由**受信默认分支**执行 loop | — |

这条和 §0 原则 2（声明不是代码）是同一风险的两道防线。

---

## 8. GitHub Actions 硬约束 *(v0.2 新增)*

均据 GitHub 官方文档，2026-09-03 核实。**这四条必须设计进实现，不是注意事项。**

| 约束 | 后果 | 应对 |
|---|---|---|
| 🔴 **公共仓库 60 天无活动，scheduled workflow 自动停用** | Hub 冷清一阵**全线静默停跑**，且没人立刻发现 | `keepalive.yml` 定期产生活动 + 停用告警；`health.status` 兜底监测 |
| 高峰期 schedule 延迟甚至丢队列，最短间隔 5 分钟 | 准点承诺必然打脸 | 产品口径写"每日"**不写"每日 8:00 整"**；`manifest.json` 记真实 `started_at` |
| 🔴 **`GITHUB_TOKEN` 推的 commit 不触发 Pages build** | 产出 commit 了但**站点不更新** | 必须在**同一 workflow** 内用官方 Pages deploy Action 发布 |
| Pages 建议 ≤1GB 仓库 / 10 分钟单次部署 / 100GB 月带宽 | `runs/` 无限累积撞墙 | 早定归档策略：滚动保留 N 个月，更老的归档分支 |

**其他实现要点：**

- `schedule` 只在默认分支执行
- 每个 loop 用固定 `concurrency` 防重叠
- `runs/` **append-only**；**无新内容不 commit**（同时满足"无新意不发"）
- RSS item 用稳定 `guid` + `pubDate` + 结果 permalink；另生成 JSON Feed 供程序消费

**定位口径**：零服务器 v1 是「**可审计的公开样本与协议**」，不是可靠的多租户调度平台。SLA、私有 loop、付费执行留到订阅/Fork 需求被验证之后。

---

## 9. 健康度与降权

`runs/` 的 commit 历史自动算出 `health`：

| status | 判据 | Hub 展示 |
|---|---|---|
| `healthy` | 最近一次运行在预期周期内，且 `replay_success_rate` ≥ 0.8 | 正常展示 |
| `stale` | 超过 2 个周期没有新 run | 列表降权 + 标记 |
| `broken` | 超过 5 个周期，或连续 3 次产出为空，或连续 2 次重放失败 | 移出推荐位，通知作者 |

`pattern-only` 的 loop 没有 `runs/`，不参与健康度，改用「最后更新时间 + 重放成功率 + fork 数」排序。

---

## 10. 30 天验证闸门

**不过线就不开发市场功能。**

| 指标 | 过线 |
|---|---|
| 可公开的高价值 loop 数 | ≥ 10 |
| 全新环境首次跑通率 | ≥ 80% |
| 订阅/Fork 弱路径 ÷ 强路径 | ≥ 20% |
| 通知被打开或标为有用 | ≥ 50% |
| 非开发者 30 分钟内 Fork 成功率 | ≥ 80% |
