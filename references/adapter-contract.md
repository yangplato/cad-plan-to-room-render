# 宿主适配契约 v1.0

适用于 Skill v1.1.x。它约定 Agent 应交换和保留的信息，**不是可直接调用的 API**。宿主把逻辑动作映射到真实工具；工具名称、模型参数、上传方式与等待机制由宿主确认。示例见 [platform-adapter.example.json](../examples/platform-adapter.example.json)。

## 1. 底座与本地适配分开

- `contract_version`：本契约版本；`base_skill_version`：实际加载的 Skill 版本。更新底座后重新检查差异，不能自动把旧适配标为兼容。
- `adapter`：宿主名称、适配版本、真实能力证据及工具绑定。仅写自己能验证的模型名/版本，未知填 `null`。
- 本地 overlay 只处理工具、参数、附件/输出格式、限额和交互方式。它不能移除阶段确认、质量检查，不能降低空间约束，不能把占位体块变成指定家具款式。
- 用户对本案的明确指示写进案例记录；不要为了一个案例更改上游通用规则。若宿主不能满足不变量，采用降级交付或说明不兼容，不静默删规则。

## 2. 执行前探测与资源预检

能力值仅用 `available / unavailable / unverified`；附简短证据。没有工具定义或实际可读内容支持时用 `unverified`，不能因平台品牌推定可用。

| 能力键 | 要确认的事实 |
|---|---|
| `read_files` | 支持的格式、是否真能打开包内文件；DWG、DXF、PDF 分别记录，不能从“支持附件”推导全部可读。 |
| `inspect_images` | 能否观察上传图纸的真实像素，必要时查看细节。 |
| `parse_cad` / `execute_code` | 是否真有原生解析/转换或代码工具；图片识别不等于原生 CAD 几何提取。 |
| `generate_with_images` / `edit_images` | 能否把图像内容传给模型、支持的格式/尺寸/张数、是否具备编辑动作；未知限额标未知。 |
| `inspect_outputs` | 能否重新查看本次生成结果；生成工具返回“成功”不代表看过图。 |
| `persist_artifacts` / `resume_jobs` | 能否保存实际文件和状态、查询未结束任务；不能保存时以消息交接。 |
| `confirm_with_user` | 原生按钮或文本回复如何关联成果版本；不需要平台专有审批 API。 |

本阶段预检只包含必需文档、选定的离线风格模块和真实图片。逐项记录存在、可读及传图状态。图片条目包括 `artifact_id`、`revision`、角色、格式和实际 `handle`；handle 可以是当前工具可读取的路径、上传 ID、附件 ID 或已解码内容引用，但必须验证本次工具真能取到。`file_name` 仅为显示标签，不能用它代替图片。可用时保留内容哈希；不能计算则用 `null` 并保留版本/来源，绝不编造哈希。

角色限于实际用途：`source_plan / clean_plan / spatial_guide / approved_design / quality_reference / style_reference / photography_reference`。按最终发送顺序记录。无关样张不加载，质感参考不能提供本案布局。若底图和样张混合，Prompt 必须明确各自权责。

## 3. 最小逻辑请求与返回

每次动作至少携带：

```text
request_id, case_id, stage, action
inputs[] = artifact_id + revision + role + 实际图像handle
prompt = 本次完整实际文本（如动作需要生图）
constraints = 本案空间事实/选型记录的版本引用
output = 目标格式、画幅、需要的风格/房间
confirmation_policy = 当前人工节点要求及明确委托范围
```

`action` 是逻辑标签：`inspect_source / prepare_plan / generate_color_plan / generate_room_render / inspect_result / request_confirmation`。不是任何平台保证存在的函数。宿主先检查本步依据与确认有效，再按工具文档组装真实调用；不把整个 JSON 当作已发送的生图 Prompt。

最小返回：

```text
request_id, status, job_id（工具确实提供时）
outputs[] = artifact_id + revision + 实际可访问handle
actual_inputs, actual_prompt, provider/model（仅已知值）
self_check = not_run / passed / failed / partial，附实际观察
error = code + 简短原因 + 可重试性 + 下一步（出错时）
```

动作状态：`not_started / queued / running / succeeded / failed / needs_input / unavailable`。`succeeded` 只说明该动作产物已可取；它不等于自检通过，更不等于用户接受。失败、超时和能力缺失不得返回空图片却标成功。错误类别可用 `INPUT_UNREADABLE / RESOURCE_MISSING / CAPABILITY_MISSING / GENERATION_FAILED / JOB_STATUS_UNKNOWN / CONFIRMATION_REQUIRED / STALE_INPUT`，宿主可补充真实服务错误码。

异步动作有任务 ID 时保存并查询；重复提交前先确认原任务状态。结果不明时用 `JOB_STATUS_UNKNOWN`，说明可能仍在执行，不自动重发有费用的任务。宿主不能查询、取消或后台常驻时如实告知；不要通过固定睡眠假定完成。恢复时核对输入版本、任务 ID 与输出归属，不把其他案例的图当成本任务结果。

## 4. 四个确认节点与失效规则

| 阶段 ID | 交给用户确认什么 | 下游使用前提 |
|---|---|---|
| `01-source` | 目标平面、识别事实、影响制作的疑点 | 有明确确认，或用户对该节点的明确委托；关键冲突仍需解决。 |
| `02-clean-plan` | 整理图和与原件的变化摘要 | 当前整理图版本自检通过，且用户确认或该节点在明确委托内。 |
| `03-color-plan` | 本风格彩平、选型和未解决问题 | 自检通过且用户确认，或在明确委托范围内代检通过；关键错误未解不能进入04。固定被选中的设计版本后再生成该风格房间图。 |
| `04-room-render` | 各房间效果图及自检结论 | 接受具体成果后标记用户验收完成；未选择的候选保留为过程。 |

成果状态用 `draft / self_checked / awaiting_user / accepted / delegated / stale`。多风格/多房间使用 `scope_id` 区分分支；每个分支绑定自己的成果，不能用一个全局“通过”覆盖尚未审阅的图。每条确认保留 `artifact_id + revision`、用户回复或授权记录的引用。`delegated` 表示用户明确把该节点的推进判断交给 Agent，**不能改写成用户接受该图**。用户说“做全流程”默认依然有四个确认节点；沉默、超时、工具返回成功、文件名“最终版”均不是确认。确认有歧义时只澄清当前节点，不重问已经有效确认的旧阶段。

更换原图或纠正布局会使依赖它的整理图、彩平、房间图及确认过期；更换某风格彩平只使该风格依赖的房间图过期。保留旧图和历史状态，重新从受影响的最早阶段核验。适配工具或质量 Prompt 改版不会自动撤销用户对旧图的接受；后续新图记录新版本即可。依赖以实际 `artifact_id + revision` 为准，不按文件修改时间猜测。

## 5. 适配完成的最小验证

目标 Agent 应用其真实工具完成一次可读附件检查、一张按角色传图的生成与回看、一次绑定版本的文本/界面确认，以及一次保存后恢复。不能生图时只验证它实际支持的识别/交接范围，剩余标未验证。再检查换图后下游确认是否失效、无法读取参考时是否明确降级、工具失败时是否没有虚报完成。

验证记录保留调用和结果证据；完成接口映射不代表图像质量达到基线。公开分享适配记录时去掉用户文件、私有附件 handle、鉴权内容与客户信息。本接口不授权向新的第三方服务传输原始 CAD 或项目图片。
