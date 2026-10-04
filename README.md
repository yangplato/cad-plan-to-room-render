# CAD Plan to Room Render

**从住宅平面到多风格彩平，再到保持空间关系的室内摄影效果图。**

一个可携带的 Agent Skill：核实平面事实、按风格选择家具、用摄影表达空间。支持原始CAD或导出平面，不把家具占位模型的盒子造型当成最终设计。

**v1.0.0 · MIT · 2026-10-04**。95㎡单案例十风格、40张审阅图获用户接受；不是自动施工建模工具，也不承诺每个模型一次出图成功。

![意式极简彩平质量样张](references/quality-italian.png)

## 开始使用

### 支持 Skill 文件夹的 Agent

下载完整包，解压得到 `cad-plan-to-room-render/`，保留其内部结构。把这一整个文件夹放到目标Agent支持的Skill目录；不要只复制SKILL.md。以支持用户级 `.agents/skills` 的客户端为例，在解压目录执行：

```bash
mkdir -p ~/.agents/skills
# 目标已存在时先比较版本并备份，不覆盖正在使用的版本。
test ! -e ~/.agents/skills/cad-plan-to-room-render && cp -R cad-plan-to-room-render ~/.agents/skills/
```

其他客户端按其实际支持的Skill路径安装。格式遵循 [Agent Skills 规范](https://agentskills.io/specification)，安装位置与调用方式由各宿主决定。Codex可用其Skills设置或支持的本地Skill目录；没有看到新Skill时刷新/重开会话后检查，不以“文件已复制”代替已加载。

调用示例：

```text
使用 $cad-plan-to-room-render 处理附件平面。先整理并核对底图，然后制作中古风彩平，以及客厅、餐厅和一间卧室的效果图。按风格把图片放在同一个审阅入口，并附每一步实际Prompt。
```

### 豆包、Kimi、Work Buddy及其他平台

打开 [跨平台入口](references/portability.md)，复制入口指令并上传当前阶段所需的真实图片和文字。原生Skill支持、文件读取、代码与生图能力按当前环境核实；没有某项能力就使用对应替代路径。**本包已整理迁移材料，尚未在这些平台完成同等整链验收。**

## 三步工作流

| 阶段 | 依据与产物 | 固定什么／允许什么 |
|---|---|---|
| A 平面整理 | 原CAD或清晰平面 → 干净平面＋个案确认信息 | 核实墙门窗、连通、家具与洁具；移除制图辅助信息，不重设计 |
| B 彩平 | 通用母版＋个案特点＋单一风格＋适用参考 | 锁布局、类别、数量和占位；家具构造、材质、软装按风格选择 |
| C 空间摄影 | 核实平面＋本套彩平＋空间提示＋镜头说明 | 继承本套已选设计；在真实机位改善构图与光线 |

默认通高墙、统一浅灰水泥剖面、线性抽象挂衣图示、正确洗衣机顶视面。缺少立面可以合理补全设计。三张内置样张提供材质/摄影基线，**不能把它们的布局套到新户型**。

十种风格：当代新中式、宋式美学、奶油风、中古风、法式复古、现代简约、意式极简、意式轻奢、东南亚风格、北欧风格。形态与材料依据、可复制段落见 [风格模块](references/style-modules.md)。

## 文件入口

- [SKILL.md](SKILL.md)：Agent入口和不可漂移的工作规则。
- [A 平面整理](references/prepare-plan.md) / [B 母版](references/color-plan.md) / [C 摄影方法](references/room-render.md)：阶段执行和Prompt。
- [参考样张及作用](references/image-references.md) / [运行记录](references/run-record.md)：真实传图、选型承接与结果核验。
- [可选结构化工具](references/scene-contract.md)：只读DXF清单，JSON校验与动态SVG回绘；不自动猜语义，不含95㎡硬编码。
- [验证范围与下个案例](examples/validation.md)：本次通过和仍需实测的边界。

## 工具验证

基础工具只需Python标准库；最低版本及完整命令以 [数据约定](references/scene-contract.md) 为准。DXF清单功能另需 `ezdxf`，仅在使用时安装；不需要为了普通PNG生图安装CAD依赖。

```bash
python3 -m unittest discover -s tests -v
python3 scripts/scene_tools.py --help
python3 scripts/inspect_dxf.py --help
```

`examples/synthetic-scene.json` 是匿名合成数据，只验证代码行为。检查报告不等于家具无碰撞、房间连通正确或生成图精准；这些必须结合原始资料实际看图核实。

## 发布与贡献

仓库根就是Skill目录。提交新规则前，用一个真正遇到的问题说明它改善了哪个决策；通用规则、个案信息和风格选型分开。新增脚本运行相关测试，新增参考说明来源和作用，避免附私有CAD、客户身份信息或未获授权图库。模型生成结果记录实际Prompt，不用后来改写的模板代替。

本地目录可直接作为GitHub仓库内容，或将完整Skill文件夹作为Release附件。公开上传前由发布者确认包含的材料适合公开；本包未绑定远程仓库、没有密钥、转换器或客户DWG。

[MIT许可](LICENSE) · [图片及第三方来源说明](NOTICE.md)。
