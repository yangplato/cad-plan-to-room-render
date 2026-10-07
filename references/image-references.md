# 参考图选择与用途

参考库共30张：10张彩平表现图与20张低分辨率摄影构图图。固定彩平母版和完整风格模块不因参考图改变。

## 两类参考的职责

| 类型 | 参考什么 | 本案仍由什么决定 |
|---|---|---|
| 彩平表现图（quality_reference） | 纹理尺度、软包体积、材质反射、光影层次、留白与画幅的整体感受 | 原资料与整理平面决定空间和物品；固定母版决定正交俯视与画布规则；完整风格模块决定家具选型、材料、配色、植物和陈设。 |
| 摄影构图图（photography_reference） | 空间广角或正向广角、前中后景、主体与视线、光影组织 | 本案平面与对应机位约束图决定空间；已确认彩平决定本套设计；用户选择决定景别。 |

表中的风格名称用于查找原图，不把该图的设计变成当前任务的事实。彩平样张不是新户型的布局模板；摄影样张不是本案机位或空间正确性的证据。图片中的缺墙、漏物、门状态和其他问题不沿用。

## 每次怎样使用

- 03彩平：本案整理平面＋一张彩平表现图＋固定母版、房间信息和完整风格模块。优先选同风格表现图以减少画面干扰；它仍只管表现，不替代风格文字。
- 04效果图：本案整理平面＋本套已确认彩平＋本机位已核对的空间约束图。按已确认景别，需要时再选一张摄影构图图；不上传整库。
- 运行时根据任务选择参考，不随机切换已确认请求。
- 留白和画幅仍执行固定母版。参考画面只帮助理解整体感受，不复制某个样张的户型缩放或边距。
- 完整提示词与实际附件先在对话中展示并确认。参考无法实际传入时如实说明，保留完整文字，不声称等价质量。

## 图库

| 原图风格 | 彩平表现 | 空间广角构图 | 正向广角构图 |
|---|---|---|---|
| 当代新中式 | [彩平](color-plan-01.png) | [空间广角](photo-01-space.jpg) | [正向广角](photo-01-front.jpg) |
| 宋式美学 | [彩平](color-plan-02.png) | [空间广角](photo-02-space.jpg) | [正向广角](photo-02-front.jpg) |
| 奶油风 | [彩平](color-plan-03.png) | [空间广角](photo-03-space.jpg) | [正向广角](photo-03-front.jpg) |
| 中古风 | [彩平](color-plan-04.png) | [空间广角](photo-04-space.jpg) | [正向广角](photo-04-front.jpg) |
| 法式复古 | [彩平](color-plan-05.png) | [空间广角](photo-05-space.jpg) | [正向广角](photo-05-front.jpg) |
| 现代简约 | [彩平](color-plan-06.png) | [空间广角](photo-06-space.jpg) | [正向广角](photo-06-front.jpg) |
| 意式极简 | [彩平](color-plan-07.png) | [空间广角](photo-07-space.jpg) | [正向广角](photo-07-front.jpg) |
| 意式轻奢 | [彩平](color-plan-08.png) | [空间广角](photo-08-space.jpg) | [正向广角](photo-08-front.jpg) |
| 东南亚风格 | [彩平](color-plan-09.png) | [空间广角](photo-09-space.jpg) | [正向广角](photo-09-front.jpg) |
| 北欧风格 | [彩平](color-plan-10.png) | [空间广角](photo-10-space.jpg) | [正向广角](photo-10-front.jpg) |

## 固定附件角色文字

按真实附件顺序填图号。保留以下职责，不根据所选样张重新抽取一套设计要求。

```text
图1是本案已确认的整理平面，提供房间、物品类别、占位和空间关系。
图2是彩平表现参考，只参考纹理尺度、软包体积、材质反射、光影、留白和画幅的整体感受。家具款式、材料类别、配色、植物、陈设与本案布局仍按固定母版、完整风格模块和房间信息执行。
```

效果图中，摄影参考使用以下职责；本案整理平面、已确认彩平与本机位空间约束图仍按房间方法实际传入。

```text
摄影参考只提供景别、前中后景、主体视线和光影组织，不提供本案布局、墙门窗、家具数量、朝向或选型。固定风格模块与本套已确认设计照常执行。
```

## 来源与保存方式

- 彩平：新中式与奶油风来自V1.2实测，其余8张来自V1.3实测。具体源文件见下表。10张均逐字节保存源文件，不重绘或缩小。
- 摄影：全部来自“青云书院187-V1.3实测-20261007/十风格成果”。每风格从两个空间广角中随机抽取一张，并采用同风格正向广角一张。仅等比缩小为1024×576并保存JPEG（质量85），不裁切或重绘。原始高分辨率文件保留在案例档案。
- 本次建库采用随机抽样，选中源文件在下表列明。这不是生图种子，也不要求运行时再次抽样。
- 来源与许可见 [NOTICE](../NOTICE.md)。
- 以下源文件位置是案例内部名称。SHA-256用于识别实际文件，不表示全图空间已经验证正确。

| 当前文件 | 来源 | 当前文件SHA-256 |
|---|---|---|
| [color-plan-01.png](color-plan-01.png) | V1.2实测/01-当代新中式/01-彩平.png（用户附件1） | `c94f68c225ca612701b8f2d4f0df41a036bd7d1b00a130d3c094d055df7a3899` |
| [photo-01-space.jpg](photo-01-space.jpg) | V1.3实测/01-当代新中式/02-客厅与休闲区-空间广角2.png | `b1bcae2abb223dfe92f4c33efdbb93ff8635bd318cbbd5f82f7539bf9fe32ae7` |
| [photo-01-front.jpg](photo-01-front.jpg) | V1.3实测/01-当代新中式/07-客餐厅-正向广角.png | `bebef8889123d1c541ebacd466ef51f19b41bb194d72223507351c93ea069de2` |
| [color-plan-02.png](color-plan-02.png) | V1.3实测/02-宋式美学/00-彩平.png（用户授权补齐） | `9877240b34fe3a1b13ad8fc6d4c7ddd4cec4f62113ddb58b2d517cb564bd15b5` |
| [photo-02-space.jpg](photo-02-space.jpg) | V1.3实测/02-宋式美学/01-客餐厅-空间广角1.png | `dd2127f34e89147627a8f509339d194d6692e12164da7583a5cac6a0f13191f4` |
| [photo-02-front.jpg](photo-02-front.jpg) | V1.3实测/02-宋式美学/07-客餐厅-正向广角.png | `6387b2ca15dcdee7331f41988eaa57236862fac436af09121c152ed031cfdf94` |
| [color-plan-03.png](color-plan-03.png) | V1.2实测/03-奶油风/01-彩平.png（用户附件2） | `da99202981c74940102cc676aa9ec2bc0fd60c2f421a2cff01b9964c86ae88b8` |
| [photo-03-space.jpg](photo-03-space.jpg) | V1.3实测/03-奶油风/01-客餐厅-空间广角1.png | `5becc4c8465486ad30d0450514386a801b6c24098d4ae05f7b8904963421d7f0` |
| [photo-03-front.jpg](photo-03-front.jpg) | V1.3实测/03-奶油风/07-客餐厅-正向广角.png | `71abd655de8f0d4b351eeaecc02d4f3cbd9b4e1c73e97e33ccfa6ba2c4a28189` |
| [color-plan-04.png](color-plan-04.png) | V1.3实测/04-中古风/00-彩平.png（用户附件3） | `0c3fdcc96bc47726314a31a79278a5b48c0cfaf4111427ccf8f5e0dfd3c9c67a` |
| [photo-04-space.jpg](photo-04-space.jpg) | V1.3实测/04-中古风/02-客厅与休闲区-空间广角2.png | `5bb9925bd25a8af03357e29af9373b8249e4fa14885048caa654fbcfae385f50` |
| [photo-04-front.jpg](photo-04-front.jpg) | V1.3实测/04-中古风/07-客餐厅-正向广角.png | `a0ecbe433cc7876d24ccae5ff6236de2e4570ccc86d8d9d708a5e7ec296f1c57` |
| [color-plan-05.png](color-plan-05.png) | V1.3实测/05-法式复古/00-彩平.png（用户附件4） | `10883b5c901e3284e47b434ce8ad7501083caa78704afefd99ddfa917635d1da` |
| [photo-05-space.jpg](photo-05-space.jpg) | V1.3实测/05-法式复古/01-客餐厅-空间广角1.png | `9375368f80e7a437e8bfb301171acfdaf4a8d6ba812a2901095fbe4a06c4457a` |
| [photo-05-front.jpg](photo-05-front.jpg) | V1.3实测/05-法式复古/07-客餐厅-正向广角.png | `e6b429c2ab13bfd2de1e633d8ce24dcce75364ffad2be0b2d81e2ea8a584337b` |
| [color-plan-06.png](color-plan-06.png) | V1.3实测/06-现代简约/00-彩平.png（用户附件5） | `6683cdd53381e70040f3ac6642d4c86cb1c16ecca2f2074c8c9ee71f036cea36` |
| [photo-06-space.jpg](photo-06-space.jpg) | V1.3实测/06-现代简约/01-客餐厅-空间广角1.png | `cee6a84817b2ec6b7a25b91ad352ccfc58f0f9e0054cd1ba15fc7ec9e2de6f31` |
| [photo-06-front.jpg](photo-06-front.jpg) | V1.3实测/06-现代简约/07-客餐厅-正向广角.png | `1f6256fc396be4b6ca866118e6cc21f48bea4e6fea9db1ab77f864ee556a6e7f` |
| [color-plan-07.png](color-plan-07.png) | V1.3实测/07-意式极简/00-彩平.png（用户附件6） | `29a7d29b8e2cb225af9eb78452eb948c1ea0ce903309f9f1324d3bf3245c4fab` |
| [photo-07-space.jpg](photo-07-space.jpg) | V1.3实测/07-意式极简/02-客厅与休闲区-空间广角2.png | `79c6a6261c91f8ec039c020cb731f28bcf3edab3e73521307227656baa322687` |
| [photo-07-front.jpg](photo-07-front.jpg) | V1.3实测/07-意式极简/07-客餐厅-正向广角.png | `e03a8f928c073f3c5e9c8bcf015b1c257a4507749b024d3d4b2eaec0f7247131` |
| [color-plan-08.png](color-plan-08.png) | V1.3实测/08-意式轻奢/00-彩平.png（用户附件7） | `01c0f7d5e143b9989b3a36296c09b7946821a7dcc369e90afc34d7ef71d34cb0` |
| [photo-08-space.jpg](photo-08-space.jpg) | V1.3实测/08-意式轻奢/02-客厅与休闲区-空间广角2.png | `6f83381f51ef4193b55ebb9eec2d5d039d3edcb38217c562db622285f032f3d9` |
| [photo-08-front.jpg](photo-08-front.jpg) | V1.3实测/08-意式轻奢/07-客餐厅-正向广角.png | `65da51f704352ecc69024da9cc6fb4e59683dce8137137bcbcc217192f922f80` |
| [color-plan-09.png](color-plan-09.png) | V1.3实测/09-东南亚风格/00-彩平.png（用户附件8） | `3e3c65c4e2e25ead8657e9b55901b2a79e478f2f2c3541652d06868287dcd456` |
| [photo-09-space.jpg](photo-09-space.jpg) | V1.3实测/09-东南亚风格/01-客餐厅-空间广角1.png | `318d67212355d0dfdbc0463779f69381c338bdecc3bb8cdf63d4af3ca0e98900` |
| [photo-09-front.jpg](photo-09-front.jpg) | V1.3实测/09-东南亚风格/07-客餐厅-正向广角.png | `0597d0f8da37170bf2994e5db9ea762a72debaba254ef663f2fc60f445bfd220` |
| [color-plan-10.png](color-plan-10.png) | V1.3实测/10-北欧风格/00-彩平.png（用户附件9） | `72a6d58af7977730285aa5e176a4ffbdb67e2b5748d354d4f6f8a9d04a3118bc` |
| [photo-10-space.jpg](photo-10-space.jpg) | V1.3实测/10-北欧风格/02-客厅与休闲区-空间广角2.png | `b477c67857dc183632de7d116729f7ab8395318996d3b6e462fbbc7f0d37dfc9` |
| [photo-10-front.jpg](photo-10-front.jpg) | V1.3实测/10-北欧风格/07-客餐厅-正向广角.png | `f0e97bffaea3f6935aa2813f460f017e1505b0394341ccd659c3f58bbbba7e67` |
