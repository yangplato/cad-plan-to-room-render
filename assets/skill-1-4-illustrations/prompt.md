# README 1.4.1 流程配图

采用小黑 Skill 生成手绘解释图；Kami 用于 README 图文层级和留白。PNG 是生成资产，不是 HTML 导出。原始生成文件保留。

## 必须保留

约束图保留布局，参考库选型转成本房设计，先形成主视角，再延续其他角度。整体成立即停。图示不代表精确建模或施工验收。

## 可选补充

当前不增加节点。原始资料识别、确认和具体修正规则由 README 正文说明。

## 视觉方向

纯白、黑色手绘、小黑执行核心动作；蓝色短标注、橙色路径、红色停止提醒。宽幅，避免PPT框图。中文标签8处，手机端通过README正文补充阅读。

## 相邻内容边界

历史案例拼图 assets/workflow-overview.jpg 保留原样，放在历史案例部分，不当作1.4.1新增生图验证。参考照片不进入此配图。

## 实际生成提示词

```text
Generate one standalone 16:9 horizontal Chinese README illustration, crisp high resolution. Pure white background, minimalist black hand-drawn thin slightly wobbly pen lines, generous whitespace at least 35%, sparse orange arrows, blue annotations and one red note. No gradients, shadows, paper texture, commercial vector style, PPT boxes or grid, top-left title, cute mascot, or real UI.

Core meaning: this residential design skill uses a spatial guide to retain layout, a form-reference library to complete ceiling lighting and cabinetry design, creates one main render then continues the same scheme from another angle; stop when the complete scheme can be judged.

Invent a fresh physical metaphor: a tiny serious solid-black creature 小黑 with white dot eyes and thin legs is fitting a removable ceiling-and-lighting sheet onto an open fold-out paper room. His hands actively hold the sheet above the room, making design completion the core action. Left: two small overlapping sheets, first a simple clean floor plan labelled “整理平面”, second a floor plan with a few restrained colour patches labelled “彩平”. An orange arrow leads to the central open paper room: visible walls, door opening, plain flat ceiling and block furniture placeholders, labelled “空间约束图”. Above it, a small open catalogue with ceiling outlines, cabinet elevations and lamps, labelled in blue “参考库选型”; the ceiling sheet held by 小黑 plus a nearby small design note is labelled “本房设计”. An orange arrow leads right to a finished room drawing on a sheet labelled “主视角”, showing coordinated ceiling, lamps and sofa, cabinet, door. Behind it a second room sheet, visibly the SAME design from another angle, labelled “延续其他视角”. Near the bottom right one small red handwritten note: “整体成立即停”.
8 labels exactly, short clearly readable simplified Chinese. No other text. Distinctive imaginative product sketch, calm deadpan character, no formal flowchart rectangles. Layout loosely flows left-to-right with plenty of air and a clear central action. Keep illustrations legible at README display width ~800px. Diagram is explanation, not evidence that all renders match perfectly.
```

## 记录

2026-10-13：首次生成1张。Agent已查看，8处中文标注可读，小黑承担设计补全动作，无顶角标题。未做二次修图；未记录为用户已接受。模型版本及随机种子未公开。
