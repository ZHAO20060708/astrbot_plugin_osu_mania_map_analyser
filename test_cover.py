#!/usr/bin/env python3
"""测试封面下载功能"""

import logging
import sys
import tempfile
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

# 添加项目路径
PLUGIN_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PLUGIN_ROOT))

from astrbot_service.cover_theme import build_cover_theme

# 测试用的 osu 文件内容片段（包含 BeatmapSetID）
TEST_OSU_TEXT = """
osu file format v14

[General]
AudioFilename: audio.mp3
AudioLeadIn: 0
PreviewTime: 12345
Countdown: 0
SampleSet: Normal
StackLeniency: 0.7
Mode: 3
LetterboxInBreaks: 0
SpecialStyle: 0
WidescreenStoryboard: 1

[Metadata]
Title:Test Map
TitleUnicode:测试铺面
Artist:Test Artist
ArtistUnicode:测试作者
Creator:Mapper
Version:Hard
Source:
Tags:test mania
BeatmapID:5540799
BeatmapSetID:2513401
"""

def main():
    print("=" * 60)
    print("测试封面主题构建功能")
    print("=" * 60)

    # 使用临时目录作为缓存
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "cover-cache"

        print(f"\n缓存目录: {cache_dir}")
        print(f"测试 BeatmapSetID: 2513401")
        print(f"测试谱面: https://osu.ppy.sh/beatmapsets/2513401#mania/5540799")
        print("\n开始构建封面主题...\n")

        theme = build_cover_theme(
            osu_text=TEST_OSU_TEXT,
            cache_dir=cache_dir
        )

        print("\n" + "=" * 60)
        if theme:
            print("✓ 成功构建封面主题！")
            print(f"  主题色: {theme.get('accent')}")
            print(f"  有封面: {theme.get('hasCover')}")
            data_uri = theme.get('coverDataUri', '')
            print(f"  DataURI 长度: {len(data_uri)} 字符")
            if data_uri:
                print(f"  DataURI 前缀: {data_uri[:50]}...")
        else:
            print("✗ 构建封面主题失败，返回 None")
            print("  请查看上方日志了解失败原因")
        print("=" * 60)

if __name__ == "__main__":
    main()
