# linc-skill

一份给 AI 编码 agent 用的研发操作手册。加载后，agent 会按任务类型走对应 playbook（排查、方案、实现交付、数据口径、发布运维、评审拷问、推进委派、复盘沉淀），按风险分档决定做多少步骤、读多少手册，并在合并、部署、生产写操作这类动作前停下等真人授权。与具体公司、产品、技术栈无关。

## 目录

```
.claude-plugin/              插件清单与自带 marketplace 清单（Claude Code 插件安装用）
skills/linc-skill/
  SKILL.md                   入口：任务分类、风险三档最小路径、8 个 playbook、判断准则、完成自检、授权边界
  references/
  gates.md                   各阶段硬性门禁总表（自检前逐条核对）
  requirements.md            需求澄清 / 现状盘点 / 范围界定
  delivery.md                交付生命周期：阶段门、测试先行、设计门、收尾标签、状态同步、下线级联
  testing.md                 测试选层、写法、数据与确定性、CI 与 flake、变异走查、非功能场景
  review-release.md          评审触发、发布回读、诊断补救阶梯、多 agent 委派、合并协议
  writing.md                 方案、结论、汇报等文档的定稿规则
  python-service.md          Python 服务实现做法
  node-service.md            Node/TypeScript 服务实现做法
  observability.md           日志 schema、trace 关联、指标、SLO、告警
  tooling.md                 独立评审系统的接线细节（只在有该系统时读）
  profile.md                 工作画像、决策风格、反模式
  generic-techniques.md      57 条可迁移技法
  agent-runtime.md           LLM Agent 运行时设计：工具双通道、prompt cache、流式会话、沙箱令牌、灰度、协议兼容
  billing-system.md          计费与商业化：账本、幂等、订阅权益、促销、支付迁移、防刷、对账、上线 runbook
  data-metrics.md            数据看板与口径治理：真相源、校验、时区、重算、假数据、看板评审清单
  ci-review-bot.md           CI 里的 AI 代码评审机器人：架构、结果判定、运维、多仓推广、故障清单
  release-multi-env.md       多环境发版：分支/环境模型、hotfix 与 back-merge、多仓顺序、配置重启、任务状态机、CLI 原则
hooks/
  hooks.json                 插件方式安装时自动注册的钩子清单
  linc-remind.sh             每条提示注入"先分类定档"提醒
  linc-git-guard.sh          拦无 lease 强推、删 release 分支；默认分支上 commit/merge 改为询问
  linc-secret-guard.sh       命令或写入内容含明文凭据时拒绝
  settings-snippet.json      注册上面三个钩子的 settings 片段
```

## 安装

依赖：git；钩子另需 bash 与 jq。

**Claude Code（推荐，插件方式，自动更新，钩子自动注册）**

会话里依次执行：

```
/plugin marketplace add hllinc/linc-skill
/plugin install linc-skill@linc-skill
```

之后每次启动 Claude Code 会自动拉取新版本。私有仓库需要本机已有可访问该仓库的 git 凭据（`gh auth login` 或 SSH）。

**Cursor / Codex（clone 方式）**

两者自动发现各自 `skills/*/SKILL.md`，把本仓库里的 `skills/linc-skill` 目录放到该位置即可：

```bash
git clone https://github.com/hllinc/linc-skill ~/linc-skill
ln -s ~/linc-skill/skills/linc-skill ~/.cursor/skills/linc-skill
ln -s ~/linc-skill/skills/linc-skill ~/.codex/skills/linc-skill
```

更新时在 `~/linc-skill` 里 `git pull`，软链接指向的内容随之更新。Claude Code 也可以用同样的 clone 方式（软链到 `~/.claude/skills/linc-skill`），但那样不自动更新，钩子要手动注册。

## 使用

- 显式调用：会话里输入 `/linc-skill`，或说"用 linc-skill 处理这个问题"。
- 自动触发：技能描述覆盖排查、方案、实现、数据、发布、评审、委派、复盘八类研发任务，agent 命中后会自行加载。
- 加载后的行为：先按 `SKILL.md` §0 分类并定风险档（低/中/高）。低档只走五步、不读手册；中档加用例登记表、测试层决策表、独立评审；高档命中钱/权限/数据/契约/生产开关等高风险形状时，再加安全四问、技术设计门、对抗挑战、权威后置条件回读。
- 会停下等你的动作：合并到默认或集成分支、打 tag、部署、生产库写操作、线上配置变更、批量账号/额度操作、对外发消息。其余问题它会打包成编号列表附默认值，按默认值先干。
- 收尾标签只有三种：`complete`、`pre-runtime-test-ready`、`blocked`，各自对应的证据要求见 `SKILL.md` §3.10。

## 钩子（可选，仅 Claude Code）

三个钩子把手册里最容易被忘记的三条规则变成机械拦截。插件方式安装时它们随插件自动注册，无需配置。clone 方式安装时把 `hooks/settings-snippet.json` 里的 `hooks` 对象合进 `~/.claude/settings.json`（已有 `hooks` 键时合并数组，不要覆盖），或在会话里打开 `/hooks` 逐个添加；片段里的脚本路径按你的 clone 位置改。

验证是否生效：注册后在会话里让 agent 执行 `git push -f origin main`，应被拒绝并给出理由；执行含 `${VAR}` 引用的命令应正常放行。

单独关闭某个钩子：从 settings.json 里删掉对应条目，或在 `/hooks` 菜单里禁用。

## 更新

插件方式：自动，每次启动 Claude Code 时拉取；也可在会话里 `/plugin update linc-skill@linc-skill`。clone 方式：在 clone 目录 `git pull`，新会话即生效。

## 维护约定

- 稳定做法写在 `SKILL.md`；项目专有的人名、系统名、状态机、事故教训放各项目自己的 memory 或仓库规则文件，不进本仓。
- 同一纠正第二次出现即更新 `SKILL.md`；新规则至少要有三条不同日期的原始观察支撑，单次观察只能作为例子。
- 修改后先在一个小任务上冷启动跑一遍再合并：看 agent 是否按 playbook 走、读了多少手册、在哪一步卡住。
