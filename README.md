# osu!mania 谱面分析插件

`astrbot_plugin_osu_mania_map_analyser` 是面向 AstrBot 的 osu!mania 谱面分析插件。插件根据 Beatmap ID 下载谱面，通过 Playwright 驱动 Chromium 渲染分析卡片，并将结果图片发送到当前会话。

本仓库由 [ZHAO20060708](https://github.com/ZHAO20060708) 基于 [2710165659/astrbot_plugin_osu_mania_map_analyser](https://github.com/2710165659/astrbot_plugin_osu_mania_map_analyser) 维护，并集成 [LeoBlackMT/osumania_map_analyser](https://github.com/LeoBlackMT/osumania_map_analyser) 的分析与可视化代码。

![渲染示例](image.png)

## 功能

- 根据 osu! Beatmap ID 生成谱面分析卡片。
- 提供 Pattern、Etterna、Graph、Auto 与精简卡片等显示模式。
- 支持 `DT`、`HT`、`IN`、`HO` 参数。
- 支持 4K、6K、7K osu!mania 谱面；非 mania 谱面会返回明确提示。
- 复用常驻 Chromium，避免每次渲染重复启动浏览器。
- 在 AstrBot WebUI 中配置并发数、渲染内容、估算算法与卡片样式。

## 环境要求

- AstrBot `>=4.16,<5`
- Python 依赖见 [`requirements.txt`](requirements.txt)
- Linux 主机需具备 Chromium 所需的系统运行库
- 首次运行需要访问 PyPI 和 Playwright 浏览器下载源

AstrBot 会先安装 `requirements.txt` 中声明的 Python 依赖。插件会将 Playwright Chromium 和必要的后备运行环境保存在：

```text
data/plugin_data/astrbot_plugin_osu_mania_map_analyser/runtime/
```

该目录不会在插件更新时被覆盖。首次启动可能需要较长时间，后续启动会复用已经安装的浏览器。

## 安装

可以在 AstrBot WebUI 中通过 GitHub 仓库地址安装：

```text
https://github.com/ZHAO20060708/astrbot_plugin_osu_mania_map_analyser
```

也可以将仓库克隆到 AstrBot 的插件目录：

```bash
cd AstrBot/data/plugins
git clone https://github.com/ZHAO20060708/astrbot_plugin_osu_mania_map_analyser.git
```

安装后在 WebUI 中重载插件，或重启 AstrBot。

## 使用

| 命令 | 说明 |
| --- | --- |
| `/ma <bid>` | 使用配置中的默认主体内容进行分析 |
| `/ma -n <bid>` | 生成精简卡片 |
| `/ma -a <bid>` | 根据 LN 占比自动选择 Pattern 或 Etterna |
| `/ma -p <bid>` | 显示 Pattern 键型分析 |
| `/ma -e <bid>` | 显示 Etterna MSD 分析 |
| `/ma -g <bid>` | 显示难度变化图 |
| `/mag <bid>` | `/ma -g` 的简写 |
| `/ma help` | 显示命令帮助 |

参数示例：

```text
/ma 5170433
/ma 5170433+dt
/ma 5170433+dt1.10
/ma 5170433+ht0.75
/ma 5170433+in
/mag 5170433
```

`DT` 自定义倍速范围为 `1.01` 至 `2.00`，`HT` 自定义倍速范围为 `0.50` 至 `0.99`。`IN` 和 `HO` 不接受额外倍速参数。

## 配置与数据

插件配置由 `_conf_schema.json` 定义，可在 AstrBot WebUI 中修改。下载缓存、封面缓存、渲染结果与浏览器运行时均位于：

```text
data/plugin_data/astrbot_plugin_osu_mania_map_analyser/
```

渲染结果仅供谱面分析参考，不代表官方难度评级。

## 维护说明

- 插件入口与 AstrBot 适配代码位于 `main.py` 和 `astrbot_service/`。
- 浏览器桥接页面位于 `bridge/`。
- 内嵌分析器位于 `osumania_map_analyser/`。
- 版本变更记录见 [`CHANGELOG.md`](CHANGELOG.md)。

## 许可证与致谢

请分别遵守本仓库及所集成上游项目的许可证。感谢 AstrBot、Playwright、osu! 社区及相关算法作者的工作。
