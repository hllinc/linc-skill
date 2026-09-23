# 多环境发布流程与任务流转

> 提炼自 Gitflow 发版规范、发布/任务流转技能与个人记忆；已去除公司/产品/人员信息，保留通用做法。

## 1 分支与环境模型

- 四级台阶：本地 → develop（dev 环境，push 即部署）→ test-staging（tag `X.Y.Z-alpha.N`/`-beta.N` = 测试态，`-rc.N` = 预发态，共用一套集群）→ main + 正式 tag `X.Y.Z`（生产，人工审批闸门）。
- tag 的 semver 后缀是唯一真相，CI 按后缀路由环境，不看 commit；同一 commit 误打多个环境 tag 时以后缀为准。
- main 永远等于生产正在跑的代码，只接受 release/hotfix MR；develop 是持续集成分支，接受 feature MR 与 back-merge；两者均禁直接 push。
- release/* 从 develop 切，整个 alpha→beta→rc 阶段不合 main/develop，只有正式 tag 部署生产成功后才一次性合回。
- hotfix/* 从 main 切，走与 release 完全相同的 alpha→beta→rc→正式路径，只是 PATCH 升级、抢环境、加急审批、压缩轮次，一个环境都不少。
- 同一时间只允许一条 release 活跃；预发验证期间不并行打新 alpha，第二个版本等前一个上线或撤回。
- 版本号两维分离：代码文件里的版本号在切 release/hotfix 分支当下改一次并锁死；制品/git tag 由 CI 按基础版本 + 后缀动态生成，绝不写回代码。

| 场景 | 改代码文件? | 示例 |
|---|---|---|
| 刚切出 release / hotfix 分支 | 是，仅此一次 | bump 到 `1.4.0` / `1.4.1` |
| 测试期修 bug | 否 | 制品 tag `1.4.0-alpha.1` |
| 环境流转 测试→预发→生产 | 否 | 沿用同一制品 |
| 发布完合回 develop | 视仓约定 | `1.5.0-SNAPSHOT` |

- 预发序号每阶段从 .0 起、三阶段各自独立计数（alpha.0→alpha.1→beta.0→rc.0→rc.1→正式），不是 rc 一路连续递增。
- 合并方式：feature→develop 与 bugfix/hotfix→release 用 squash；release→main 与 release→develop 禁 squash、用 fast-forward，否则回合时 git 认不出已合改动。

## 2 提测与发版步骤

- 范围确认：切 release 前 review develop 领先上一正式 tag 的 diff，确认这批要发什么；不想发的用 feature flag 或时间切片控制，禁止 cherry-pick 拼版本。
- 版本号核对：常规 release 升 MINOR，PATCH 只给 hotfix；不符先回去和发起人确认。
- 发布文档：用 compare 接口取上一正式 tag 到 release 分支的 commit，正则抓 `#N`/`!N` 补 issue 与 MR 关联（过滤 #1–#5 之类噪音），按 Bug Fixes / Features 分模块列、带作者；多仓联发时显式写部署顺序。
- 提测：`git checkout -b release/vX.Y.Z develop` → bump 代码版本 → 打 `X.Y.Z-alpha.0` → 查 `pipelines?ref=<tag>` 处于 running/success 才算"部署被触发"，不要只看 tag 创建成功。
- 优先点 CI 内置按钮（cut-release / prerelease:tag / promote:beta / promote:rc / release:prod / mergeback），手工 tag 是无按钮时的 fallback；同阶段递增用 prerelease:tag，promote:* 只产 .0，rc.0 已存在时再点 promote:rc 会失败。
- MR 门：预发期修复走"从 release 切短分支 → MR → 至少 1 名非作者 review + CI 绿 → squash 进 release"，没过 review 不准更新 release 内容、不准打下一个 tag。
- 正式 tag 前必须 `git pull --ff-only` 到最新分支头，并核对 release 是否落后 main；点 release:prod 时该 job 的 commit sha 必须等于 release 分支当前头，旧流水线的按钮点了就发旧代码。
- 建 release 分支前先读该仓 CI 配置的 deploy rules，确认分支名不会命中"自动发生产"规则；用 API 建分支没有 `-o ci.skip` 保护。
- 预发绿灯不等于生产可发：当 deploy:test-staging 与 deploy:prod 走不同代码路径时，生产独有分支在打正式 tag 时才第一次执行，go-live 前人工确认两者部署逻辑对称。
- 生产 tag 是红线：脚本只做预检并打印命令，由发布负责人手动执行；提测与阶段递进可代跑但要输入 tag 名二次确认。
- 平台抖动（构建基础设施 internal error）重试即可，不必回滚；验证以重试后的流水线为准。
- 发布后 reset：部署成功 → 合 release→main（记录线上版本）→ back-merge develop → develop 版本号回 bump 到下一迭代 → 关闭相关任务并写结论。
- 正式 tag 打错不删不改，直接打下一个修订号并在发布文档标作废。

## 3 hotfix 与 back-merge

- 生产出事：建 incident issue → 从 main 切 `hotfix/vX.Y.(Z+1)_<描述>` → 第一刻 bump PATCH → 修复 → `alpha.0` 上测试态 → 可压缩 beta → `rc.N` 预发验收 → 正式 tag → 加急审批 → 生产。
- hotfix 部署成功后必须合回 main 和 develop，否则下次 release 覆盖掉 hotfix（经典事故）。
- 预发期插入 hotfix：hotfix 抢占 test-staging，进行中的 rc 顺延；hotfix 上线后 release 分支需先合入 main 的 hotfix 提交再继续。
- back-merge 源分支永远是打了正式 tag 的那条 release/hotfix 分支，同时建 →main 与 →develop 两条 MR；绝不用 main→develop 当源，tag 触发时 main 还没更新会得到空回合。
- 建 develop 方向回合前先比 `compare?from=develop&to=release/x.y.z` 的 diffs 数：为 0 说明 develop 已含全部内容，不必建或直接关掉。
- 回合冲突由改动 owner 手工解 + review，禁止 `-X ours/theirs` 一把梭。
- 回合积压不逐条补合：合掉最新一条 main 方向回合，历史积压自动变空 MR，直接关闭。
- mergeback 自动 job 的触发条件各仓可能不同（有的依赖 deploy 成功，有的依赖前序 stage 全部成功），部署失败后要去确认回合 MR 是否真的建出来了。
- CI 可加定时检查"main 领先 develop 的 commit 数"，大于 0 就告警。

## 4 多仓联合发版顺序

- 先列耦合契约：运行时事件 schema、命令生命周期、鉴权/沙盒生命周期假设、共享 contracts 目录、前端与网关的 API/SSE 契约。
- 默认顺序：runtime 服务 → 网关 → 前端；后端协议向后兼容时先上 runtime，前端依赖新网关端点时网关先于前端；网关拒绝旧前端流量才反过来（尽量避免）。
- 每仓独立 MR、独立 tag、独立发布文档段；不建 monorepo 指针 MR 除非明确要求。
- 联发时每个仓都要分别判断回合方向，常见情况是所有仓 develop 方向都是 0 文件，只有 main 方向真正需要合。
- 没有发版自动化的仓（无 cut-release/release:prod）走手工：Releases API 建正式 tag → tag 流水线上各 deploy:*:prod manual job 分别点 → 回合 MR 手工建。
- 发布后验证：查生产日志有无新错误与预期成功信号、查缓存/状态键流转、查沙盒负载；前端确认 tag 到达生产并抽查关键流程与错误遥测；采集 session/request/trace id 后再深挖。

## 5 配置变更与重启规则

- 先问"这次配置是要改变正在跑的行为，还是给将来的代码备好？"：后者只 patch 不重启，新镜像发布时的滚动重启会一并加载；只有激活已部署代码的配置才重启。
- 同一标准在预发与生产保持一致，别预发重启了生产不重启。
- 改前先查各环境镜像是否已含目标代码（`kubectl get deploy -o jsonpath` 看 image tag）；改后核对用 exec 进 pod 读 settings，这是核对手段不是决策前提。
- 仓库里的 configmap 模板若 CI 只做只读校验、从不 apply，kubectl patch 就是正规通道且不会被覆盖；先读文件头确认。
- 写操作只对 dev 集群；生产 context 只读，切 context 前核对名字（常只差几个字母）。

## 6 任务系统状态机

- 开工那一刻就流转：动第一行代码/派出 agent 前，把工作项从"需求提出"推到"方案设计/开发中"，并评论要做什么；不要等做完或等人问。
- MR 建出后：评论 MR 链接、目标分支、验证范围；状态推到"开发/开发评审"，不要仅因有 MR 就推"测试"。
- 合入 develop（= 部署 dev/测试环境）后：立刻推到"测试中"，评论 MR、commit/tag、环境、部署时间与验证项（bug 附原复现路径）。
- 推"已上线/全量"前必须核实代码真在 main：`git branch -r --contains <sha> | grep -c origin/main` 返回 0 就禁止推；"合入 develop"与"随 release 上生产"不是一回事。
- 发布后在工作项下写结论：改了什么、为什么、生产现在是什么状态、用户能否看到变化；"代码已发布但数据未回填、看板未变"要写明，否则对方以为已修好。
- 缺陷与需求同样要流转；容器型需求（多个子项各自上线）看子项状态，不逐个推需求节点。
- 关闭条件：验证证据已记录（生产修复附 tag/版本）、或业务确认重复/不再单独跟踪、或被命名的 Epic/canonical issue 取代；关闭评论写发了什么、关联 MR/tag、后续 issue。
- MR 关闭未合：评论原因，工作项保持打开，方向作废则退回分析状态。
- 提任务、列任务时对象必须带名称，只给数字 ID 读者看不懂也判断不了是否已处理。
- 一次只推一个节点，推完重读状态再决定下一步；把所有 doing 节点一次性 confirm 会冲过目标状态，冲过头用 rollback 从后往前逐节点回滚。
- 批量流转脚本不可无差别复用，每批的上线前提可能不同；脚本内置前置校验或每次运行前重新核实。

## 7 CLI 使用原则

- 先 `--help` 与列元数据（字段类型、可选值、当前状态可用流转），再动手；`--help` 的示例格式也可能是错的，遇到"照文档写却报错"优先找一条已有成功样本读原文照抄。
- 字段值全传字符串：bool 传 `"true"`/`"false"`，多选传 `"[{\"option_id\":\"x\"}]"` JSON 字符串，关联单选传纯 id 字符串，关联多选传 `"[id]"` JSON 数组字符串；传原生对象/数组几乎必然被网关拒。
- 整个数组走一个参数（`--params '{"fields":[...]}'`），不要逐元素多次传，逐元素会触发按元素的字符串校验并得出"写不了"的错误结论。
- 写操作假成功要回读：返回 `success`/空结果不代表落库，写完立刻 `get` 复查；角色、交付物、关联多选等类型的静默失败尤其常见；读写键名可能不对称（回读显示的字段名不一定是写入接受的键名）。
- 报错的 inner_err 常直接暴露后端解析器期望的类型，照它改一次即可，不要盲试形状；试过三种形状仍不行就让人在 UI 操作并给出该填什么值。
- 列清单必须核对总数：显式传最大 page_size，每页打印 total 与本页条数比对；返回条数正好等于页大小时一律当分页信号；按容器枚举会漏掉游离项，再按负责人查一次取并集。
- 建工作项时把角色/负责人当固定字段一并传入，事后 API 补不上；建完立刻回读角色成员，否则没人有权限流转。
- 状态流转 id 随当前状态变，每次先列当前状态下的可用流转再用；节点流与状态流是两套命令，用错报"流程不存在"。
- 建 MR 前先 push：`git push -u origin <branch>` → `glab mr create`；建完用 API 看 `changes_count` 与 `head_sha` 是否与本地 `git log -1` 一致，源分支未推时会建出 0 改动的空 MR 且不报错。
- 合并命令裸发：先用单独命令等状态到 mergeable，再发一条只含 `glab mr merge <iid> --sha <完整 SHA> --auto-merge=false --yes` 的命令；不包 if/for、不并行多条，批量串行且每合一条先确认下一条状态。
- zsh 不对 `$VAR` 分词：`set -- $S`、`for x in $S` 都拿到整串；用数组 `"${arr[@]}"`、`read -A`、`${=var}` 或 `setopt sh_word_split`。
- 有 CLI 就用 CLI（如 `glab`），不用网页抓取；写操作 token 走脚本内裸变量或临时文件中转，不在命令行里 export 含 token 的命令替换（会被脱敏层截断成 `***` 导致 401）。
- 长文本先落文件再由脚本拼 JSON，避免 shell 转义问题。

## 8 常见错误清单

- rc 阶段就把 release 合进 main → main 提前含未上线代码 → 只在正式 tag 部署成功后合。
- 用 main→develop 当 back-merge 源 → 空回合、漏掉预发修复 → 源永远是打 tag 的 release/hotfix 分支。
- hotfix 没合回 develop → 下次 release 覆盖修复 → 回合列入发布收尾必做项。
- API 建 release 分支命中自动发生产规则 → 立刻触发生产部署 → 建前读 CI rules，优先用仓内按钮。
- 同一版本号并存带 v/不带 v 两条 release 分支 → 自动化选错分支 → 命名统一，删掉废弃的那条。
- 点了过期流水线的 release:prod → 发布旧代码 → 核对 job commit sha = 分支头。
- 预发全绿就 go-live，生产部署走了预发没有的分支 → 副本被缩到 0 → 人工确认两条 deploy 逻辑对称。
- promote:rc 用来打 rc.1 → tag 已存在失败 → 同阶段递增用 prerelease:tag。
- 给未发布代码提前加配置还重启预发/生产 → 无收益的真实操作，且各环境不一致 → 只 patch 不重启。
- 工作项推到"已上线"但代码只在 develop → 看板显示已灰度而生产没代码 → 先 `--contains` 核实 main。
- 只流转需求不流转缺陷、只写评论不改状态 → 项目进度长期失真 → 发布后状态与结论一起更新。
- 提任务只给数字 ID → 读者无法判断 → 对象带名称。
- 相信 CLI 返回的 success → 字段根本没写进去 → 写后回读。
- 逐元素传字段 → 误判"该类型写不了" → 整数组一个参数传。
- 列表只取第一页 → 基于残缺清单下结论 → 核对 total。
- 建缺陷不带负责人角色 → 谁都无权流转且 API 补不了 → create 时固定带角色。
- 分支没推就建 MR → 空 MR 不报错 → 先 push 再建并核对 changes_count。
- 合并命令包条件/并行 → 合并闸按命令文本放行但实际没合 → 裸发、串行。
- 命令行 export 含 token 的命令替换 → 被脱敏成 `***`、401 → 脚本内裸变量或临时文件中转。
- 文档里的命令没跑过就写 → 缺必填参数 → 写进文档/MR 的每条命令先本地执行至少 `--help` 或 dry-run。
