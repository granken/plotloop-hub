<p align="center">
  <strong>PlotLoop Hub</strong><br>
  <em>Live Agent Loops — 正在跑的 AI 循环</em>
</p>

<p align="center">
  <strong>订阅产出，Fork 定义。</strong>
</p>

---

别人已经在跑的 Loop，你不用再跑一遍——**订阅它的产出**，或者**让你自己的 Agent 学会它**。

## 为什么

当执行被 Agent 变得廉价，「**该做什么**」的价值权重就上升了。各家模型厂都在卷「自主规划 / 长时间执行」指标——稀缺的不再是**怎么跑**，而是**跑什么值得**。

已有的东西分别解决了一半：

| 已有 | 解决了 | 没解决 |
|---|---|---|
| n8n / Zapier 模板库、awesome-* 仓库、GPT Store | 分享**定义** | 定义会腐烂，下载 ≠ 跑起来 |
| Newsletter、RSS、AI 日报 | 分享**产出** | 你没法改造它，也不知道它怎么来的 |
| ChatGPT Scheduled Tasks、Claude Code routines | **执行** | 没有公共目录，产出不共享 |

PlotLoop Hub 把这三件事接在一起，并加上第四件：**运行证据**。

## 两种 Loop

| 类型 | 产出 | 你能拿走什么 |
|---|---|---|
| **公共情报型** `public-feed` | 公开 | **订阅**产出流（RSS / JSON Feed）。零配置，价值即时兑现 |
| **私域工作流型** `pattern-only` | 私有 | **一句话让你的 Agent 学会**，在你自己的数据上跑 |

第二类是这个 Hub 和"又一个模板目录"的分界线：**分享的是做法，不是数据。**

## 一句话装载

每个 loop 页面都给这一行，粘进你自己的 Agent：

```
把 https://hub.plotloop.dev/l/<slug> 读完，
按里面的 LOOP.md 在我的环境里搭一遍，缺什么参数问我。
```

你的 Agent 会读定义、**问你要参数**、建定时任务、跑一次、对照验收标准自查。

**凭证一步都不出你的门**——`LOOP.md` 里只有参数的**名字和用途**，从来没有值。

## 收录标准

🔴 **提交一个 prompt 不算数。上架必须带运行证据。**

| 要求 | 阈值 |
|---|---|
| 全新环境**首次跑通率** | ≥ 80% |
| `public-feed` 需有真实运行档案 | 含 `manifest.json`（workflow run URL + commit SHA + 内容 hash） |
| `pattern-only` 需有脱敏样例产出 | 非空 `samples/` |
| 凭证扫描 | 零命中 |
| `LOOP.md` 不含可执行代码 | 强制 |

**为什么这么严**——两个前车之鉴：

- **myExperiment**（科研工作流分享站）：92 个工作流复跑样本近 80% 跑不起来，仅约 5% 注册用户上传过 → **只收定义会被依赖衰减拖垮**
- **GPT Store**：上线即 300 万个 GPT，两个月后满是冒名与抄袭 → **无运行证据的无限供给会被垃圾拖垮**

只收 YAML/Prompt，会同时重演这两者。

## 隐私

🔴 **默认私有。公开是逐字段的显式选择。**

依据：StravaLeaks 中，被公开监测一年后**只有约 7% 的人改成了私密**——默认值就是绝大多数人的最终值。工作 loop 泄露的客户、项目、竞争意图，比跑步路线敏感得多。

秀出去的是**运行统计和能力证明**（跑了多少天、比公开媒体早多久），不是**产出内容本身**。这两层在数据模型里就是分开的。

## 目录结构

```
loops/<slug>/
  LOOP.md      # 给 Agent 读的安装契约（六个固定小节）
  loop.yaml    # 元数据：品类 / 触发 / 可见性 / 依赖 / 健康度
  README.md    # 给人读的
  runs/        # 运行档案（public-feed）
  samples/     # 脱敏样例（pattern-only）
```

完整规范见 [`docs/SPEC.md`](./docs/SPEC.md)。

## v1 品类（只开三个）

| 品类 | 角色 |
|---|---|
| `ads-platform` 广告投放与平台政策 | 🎯 锚品类 |
| `ai-compliance` AI 合规与监管追踪 | 💰 变现品类 |
| `ai-market` AI 赛道产品情报 | 📣 引流品类 |

窄而深是刻意的。v1 不接受其他品类投稿，也**不开放无审核批量投稿**。

## 现状

🚧 **v0 骨架期。** 目标：20 个 seed loop，每个真实跑满 30 天，再决定要不要做市场功能。

验证闸门（不过线就不往下做）见 [`docs/SPEC.md`](./docs/SPEC.md) §10。

## 相关

PlotLoop 工坊的一部分 —— [plotloop](https://github.com/granken/plotloop) · [plotloop-speaker-review](https://github.com/granken/plotloop-speaker-review)

## License

MIT
