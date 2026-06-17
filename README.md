# astrbot_plugin_osu_mania_map_analyser

AstrBot 插件版 `osumania_map_analyser`。机器人可通过 `/ma <bid>` 下载 `.osu`、用 Playwright 驱动常驻 Chromium 渲染图表，并返回 PNG 图片。

![效果图](image.png)

原始项目地址：<https://github.com/LeoBlackMT/osumania_map_analyser>

> 项目内 `osumania_map_analyser/ManiaMapAnalyser by Leo_Black` 已同步到上游 `fddbad2`（v1.5.0）运行时代码；受 AstrBot 插件安装行为限制，仍未采用 submodule。

## 安装

插件启动时会自动把 Python 依赖安装到 `data/runtime/site-packages`，并把
Playwright Chromium 安装到 `data/runtime/ms-playwright`。正常情况下不需要再手动执行
`pip install -r requirements.txt` 或 `playwright install chromium`。

首次启动或 `requirements.txt` 变更后，插件会触发一次自动安装，因此需要确保：

- AstrBot 运行账号对本插件目录有写权限
- 服务器可以访问 PyPI 和 Playwright 浏览器下载源
- Linux 主机已经具备 Chromium 所需系统库；若缺少系统依赖，仍需在系统层补齐

## 使用

基于 `osumania_map_analyser` 实现本项目，可以分析键型、SV，并预估对应 RF/LN 段位。当前默认开启 SV 检测；若误判较多，可在插件配置中将 `debug_use_sv_detection` 关闭。

```text
/ma <bid>       默认等同于 /ma -a <bid>
/ma -n <bid>    主体不显示任何内容，即短卡片模式
/ma -a <bid>    主体内容按谱面 LN 占比自动选择 Pattern 或 Etterna
/ma -p <bid>    主体显示 Pattern 键型分析，非 4/6/7K 主体自动回退 Pattern
/ma -e <bid>    主体显示 Etterna 7 大键型分
/ma -g <bid>    主体显示难度变化图，命令简写 /mag
/ma help        显示本帮助文本

示例:
/ma 5170433+dt1.1
```
