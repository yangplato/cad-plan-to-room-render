# 可选空间数据与 CAD 辅助工具

主流程可以直接使用清晰的平面图片/PDF、空间事实卡及提示词。本模块适合已有可靠尺寸、能够执行 Python、需要保存和回绘结构化空间事实的使用者。它不自动辨认墙体、房间或家具，不从图片推导毫米精度，也不要求图片平台运行代码。

## 数据约定

示例见 [synthetic-scene.json](../examples/synthetic-scene.json)。该示例完全人工构造，没有客户原图、项目坐标或真实住宅信息。

- `schema` 固定为 `cad-plan-scene/1.0`；`units` 固定为 `mm`。必须先确认来源单位并明确转换；像素图、未知比例或只有视觉推测的资料继续用事实卡，不伪造毫米数据。
- `coordinates` 为 `{"x":"right","y":"up","z":"up"}`，表示图上右、图上上及高度上，不声称地理方位。所有平面坐标必须已经转换到同一原点、单位和朝向；旋转/镜像/块变换不能留给渲染器猜测。
- `title` 是显示名称。`source` 记录 `kind`、`filename` 和原文件 `sha256`；哈希为 64 位十六进制。仅 `kind: synthetic` 的合成例子可以省略文件与哈希，此时不能证明来源身份。
- `assumptions` 与 `unresolved` 为字符串列表，分别记录设计补全和待确认项。未知内容不默默补成已测量事实。
- `walls`、`openings`、`objects` 必须都是列表；每个元素包含全场景唯一的字符串 `id` 以及说明几何/分类来源的 `basis`，可有 `name`。
- 墙体用 `outer_mm` 外环及可选 `holes_mm` 内环表示。每环至少三个不同的有限二维点，可省略重复闭合点；不得用大矩形代替真实凹口。SVG 用 even-odd 填充表达内环。
- 门窗用 `category`、`a_mm`、`b_mm` 表示原墙面内的跨度。常用类别为 `door`、`window`、`opening`、`sliding_door`；可有正数 `thickness_mm`。开口仅绘制跨度符号，不自动切掉墙体：墙体轮廓与门洞缺口必须由来源核对后正确提供。
- 物件用 `category` 和多边形 `footprint_mm` 表示占地；`front_vector: [dx,dy]` 是使用正面方向，不是 CAD 块原始旋转角，可以为任意非零有限向量。未知方向为 `null` 或省略；工具提示缺失，不猜测。未知类别保留原足迹并标注问号/虚线，不能改配为最相近的库家具。
- 可选 `height_mm` 必须为正数，并同时提供 `height_basis` 区分实测和设计补全。SVG 是二维示意，不表达净高或遮挡；没有给高度时不默认补 2700mm。

工具拒绝 NaN/Infinity、重复 JSON 键、跨列表重复 ID、错误单位、退化环、零方向向量和提供源文件后的哈希不符。结构检查不会验证每条分类的真实性。

## 运行

在 Skill 根目录使用 Python 3.10+。`scene_tools.py` 只用标准库，无安装步骤。

```sh
python3 scripts/scene_tools.py validate examples/synthetic-scene.json
python3 scripts/scene_tools.py render examples/synthetic-scene.json --out /tmp/synthetic-plan.svg --report /tmp/synthetic-checks.json
python3 -m unittest discover -s tests -v
```

真实资料的结构化数据准备好后，可以校验来源并导出：

```sh
python3 scripts/scene_tools.py check-source /path/to/scene.json /path/to/original.dxf
python3 scripts/scene_tools.py render /path/to/scene.json --source /path/to/original.dxf --out /path/to/review/plan.svg --report /path/to/review/checks.json
```

三个命令均输出 JSON 检查报告；`--report` 可另存。退出码 `0` 表示所执行的检查通过，`2` 表示失败；未知类别是需要审阅的警告。`render` 遇到验证或源哈希失败不生成 SVG。输入文件与另一输出文件不能作为输出路径，包含已有的软/硬链接；已有普通输出文件会被新结果替换，因此使用独立审阅目录或版本文件名。

每份有效报告记录本次读取的 `scene_sha256`；渲染报告另记录 `rendered_svg_sha256`。修改 scene 后重新运行，不能拿旧报告证明新数据。未传入 `--source` 时来源核对显示 `not_checked`，不能称源文件已核验。

SVG 按全部几何动态计算视野；标识和标题通过 XML 转义写入，不执行输入字符串。坐标、类别、占地和方向才是空间输入，示意色及简化轮廓不决定家具款式。输出用浏览器或 SVG 查看器实际打开，检查比例、开口、邻接、功能朝向及遗漏；工具没有自动输出 PNG，可由查看器导出后传给只支持图片的平台。

## 可选 DXF 清单

`inspect_dxf.py` 在实际读取 DXF 时才加载 `ezdxf`；`--help`、其他 scene 命令及图片流程不依赖它。先检查现有 Python 环境，仅在需要 DXF 清单且依赖缺失时安装到自己的虚拟环境；该包不含 `ezdxf`、DWG 转换器或三维库。

```sh
# 可选；仅DXF清单需要。建议在自己的虚拟环境安装已测版本。
python3 -m pip install "ezdxf==1.4.4"
python3 scripts/inspect_dxf.py --help
python3 scripts/inspect_dxf.py /path/to/original.dxf --out /path/to/review/dxf-inventory.json
```

清单记录原文件哈希、DXF 单位代码、图层、块和模型空间实体类型/句柄/可用外包框，读取前后检查源哈希。外包框可能只是近似，部分类型可能无法计算；这些情况保留实体并写警告。块名只是一条来源线索，一个块也可能包含多个家具、人物或标注。清单不自动分类，不自动应用单位转换，不输出可直接信任的 scene。DWG 需另用合法可用的 CAD 工具转换为 DXF，并保留原件；本包不验证该转换器。

## 核对边界

输出报告将多边形完整拓扑、墙体与物件碰撞、空间连通、语义分类及施工准确性全部标为 `not_checked`。环的点数与非零面积检查，不代表已验证自相交、内环包含关系或全部几何合法性。SVG 中门窗是跨度标记；尺寸、门扇开启范围、人体可达区、三维遮挡和相机可站立性要另行回到原图核对。

从 JSON 回绘与从原 CAD 独立导出的线稿，应在同一比例、原点及方向下对照；同一个 JSON 生成的两张图不能互相证明没有提取错误。任何工具检查通过都不等同于彩平、摄影图、跨平台或用户验收通过。

测试覆盖合成输入、远坐标、墙洞、未知类别、非法数据、源哈希变化、报告绑定、XML 转义和输入防覆盖。可选 DXF 清单是否已在当前环境实测，应查看本次验证记录；不能从标准库测试通过推断其外部依赖或真实 CAD 兼容性。
