# 封面下载功能更新

## 更新内容

实现了从 osz 文件下载并解压背景图片的逻辑，解决了之前所有铺面查询时都 fallback 的问题。

## 工作流程

### 1. 快速路径：CDN 直接下载（优先）
首先尝试从 osu! 官方 CDN 下载封面图片：
- `https://assets.ppy.sh/beatmaps/{set_id}/covers/fullsize.jpg`
- `https://assets.ppy.sh/beatmaps/{set_id}/covers/cover@2x.jpg`
- `https://assets.ppy.sh/beatmaps/{set_id}/covers/cover.jpg`

### 2. Fallback 路径：osz 文件提取
如果 CDN 下载失败，自动降级到 osz 文件提取：

1. **多镜像源下载** - 按优先级尝试以下镜像：
   - `https://osu.direct/api/d/{set_id}`
   - `https://catboy.best/d/{set_id}`
   - `https://api.chimu.moe/v1/download/{set_id}?n=1`

2. **解析 .osu 文件** - 从 osz (zip 文件) 中找到第一个 .osu 文件，解析 [Events] 区块获取背景文件名：
   ```
   [Events]
   0,0,"bg.jpg",0,0
   ```

3. **提取背景图片** - 从 osz 中读取对应的背景文件

4. **智能 Fallback** - 如果解析失败，使用以下策略：
   - 优先选择文件名包含 `bg`、`background`、`cover` 的图片
   - 否则使用第一个 `.jpg`/`.jpeg`/`.png` 文件

### 3. 缓存机制
- 封面图片缓存：`{cache_dir}/{set_id}.cover`
- osz 文件缓存：`{cache_dir}/{set_id}.osz`
- 下次查询同一谱面时直接从缓存读取，无需重新下载

## 主要改动文件

- `astrbot_service/cover_theme.py` - 核心功能实现

## 新增功能

1. **多镜像源支持** - 增加了镜像下载的容错能力
2. **osz 解压提取** - 从完整谱面包中提取背景图片
3. **智能背景识别** - 自动解析 .osu 文件或使用启发式规则查找背景
4. **双层缓存** - 既缓存封面也缓存 osz 文件

## 测试结果

### 测试 1: CDN 下载（快速路径）
```
测试 BeatmapSetID: 2513401
✓ 成功下载封面 fullsize.jpg (size=1341760 bytes)
✓ 成功构建封面主题 (accent=#e10c34)
```

### 测试 2: osz 提取（Fallback 路径）
```
测试 BeatmapSetID: 2513401
✓ 成功从镜像下载 osz (size=11658218 bytes)
✓ 解析到背景文件: sev26_bg_2560x1440.png
✓ 成功提取封面 (size=1900329 bytes, format=PNG)
```

## 兼容性

- 保持了原有的 API 接口不变
- 对于无法获取封面的情况，仍然返回 `None`，渲染流程会使用默认主题
- 所有失败都是静默处理，不会影响主要的谱面分析功能

## 性能考虑

- CDN 下载超时：30 秒
- osz 下载超时：45 秒
- osz 文件较大（通常 5-50 MB），但会缓存以供后续使用
- 首次查询会比 CDN 慢，但缓存命中后速度相同
