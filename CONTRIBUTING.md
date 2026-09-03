# 投一个 Loop

> **v0 阶段不开放公开投稿。** 现在是 20 个 seed loop 的定向邀请期，每周只上 5 个。
> 本文档描述的是最终流程，也是受邀者当前遵循的流程。

---

## 先决条件：这个 loop 真的在跑

🔴 **提交一个 prompt 不算数。**

这是 Hub 和"又一个模板目录"唯一的区别，也是收录标准里唯一不能商量的一条。原因写在 [`README.md`](./README.md#收录标准)——myExperiment 和 GPT Store 分别演示了不这么做会怎么死。

你需要能回答：**它跑了多久？最近一次产出是什么？换个环境还能跑起来吗？**

## 选一个 kind

| 你的情况 | kind | 你要提供 |
|---|---|---|
| 产出可以公开，别人能直接订阅 | `public-feed` | 真实运行档案 `runs/` |
| 产出含私有数据，但做法值得分享 | `pattern-only` | 脱敏样例 `samples/` |

**拿不准就选 `pattern-only`。** 默认私有是本 Hub 的原则，不是妥协——见 [`docs/SPEC.md`](./docs/SPEC.md) §0.4。

## 目录

```
loops/<your-slug>/
  LOOP.md      # 六个固定小节，标题一字不差
  loop.yaml    # 元数据
  README.md    # 给人读的
  runs/  或  samples/
```

照着现有两个抄最快：
- `public-feed` 样板 → [`loops/ad-platform-ai-tracker/`](./loops/ad-platform-ai-tracker/)
- `pattern-only` 样板 → [`loops/feishu-daily-digest/`](./loops/feishu-daily-digest/)

## 本地自检

```bash
pip install pyyaml
python3 scripts/validate_loop.py
```

CI 跑的是同一个脚本，本地过了 CI 就会过。

## 三条会被直接拒的

**1. 🔴 任何凭证**

`LOOP.md` 和 `loop.yaml` 里只能有参数的**名字和用途**，永远不能有值：

```yaml
requires:
  - key: FEISHU_APP_ID
    secret: true
    purpose: 推送产出到飞书    # ✅ 声明它需要什么
```

自动扫描 + gitleaks 双重检查。**一次命中直接拒。**

**2. 🔴 `LOOP.md` 里的可执行代码块**

带 `bash` / `python` / `sh` 等语言标记的代码块会被拒。

**理由不是洁癖**：别人的 Agent 会读你这份文件**并照着做**。代码块就是注入面。契约只描述**要做什么**，怎么执行由接收方的运行时决定——这也是"一句话装载"能跨 Claude Code / Codex / 其他运行时的前提。

需要展示格式，用不带语言标记的围栏，或 `text` / `json` / `yaml` / `markdown`。

**3. 🔴 `samples/` 里的真实数据**

样例必须脱敏。人名、群名、公司、项目、金额——全部换成虚构的，并在文件顶部标明是虚构的。

参考 [`loops/feishu-daily-digest/samples/example-output.md`](./loops/feishu-daily-digest/samples/example-output.md)。

## 声明依赖的脆弱度

```yaml
dependencies:
  - name: 某平台官方 changelog 页面结构
    version_pinned: null
    fragility: high      # 页面改版即失效
```

**这不是走过场。** myExperiment 92 个工作流复跑近 80% 失败，主因就是第三方服务变更——而失效往往是**静默的**：产出变空，不报错。

标了 `high` 的项要在 `README.md` 里显式提示，并在 `LOOP.md` 的验收标准里给出**可观测的失败信号**（例："连续 3 天产出为空 → 大概率信源改版"）。

## 上架门槛

| 指标 | 阈值 |
|---|---|
| 全新环境首次跑通率 | **≥ 80%** |
| 凭证扫描 | 零命中 |
| `LOOP.md` 六小节齐全 | 强制 |
| 运行证据（`public-feed`）或脱敏样例（`pattern-only`） | 非空 |

不到 80% 的不上架——**先修可移植性，而不是先上架再说**。

## staging 状态

`public-feed` 的 loop 有个先有鸡还是先有蛋的问题：**没合并就没法在 Hub 里跑，没跑过就没有运行证据。**

解法：把 `health.status` 设成 `unproven` 提交。契约照常校验、PR 照常合并，但在产生第一次 GitHub-hosted run 之前**不会公开展示**（`index.json` 里 `listed: false`）。

第一次真实运行落地后，`update_health.py` 会自动把它转正。

## 审核

外部 PR 只跑**无 secret** 的校验：schema、lint、静态渲染。**不执行任何投稿内容**——合并后才由受信默认分支执行（[`docs/SPEC.md`](./docs/SPEC.md) §7）。

合并前还有一道人工审核，看的是：**这个 loop 解决的问题是真的吗？去噪规则写清楚了吗？验收标准可自查吗？**

## 品类

v1 只收三个：`ads-platform` · `ai-compliance` · `ai-market`。

窄而深是刻意的。品类是按**「信息差能否直接换算成钱」× 「信源是否公开但分散枯燥」**两轴筛出来的——第二轴容易被忽略但关键：**信息如果已经被媒体整理好了，loop 就没价值**。

其他品类等锚品类跑通再开。
