#!/usr/bin/env python3
"""测试从 osz 提取封面的功能"""

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

from astrbot_service.cover_theme import _extract_cover_from_osz

def main():
    print("=" * 60)
    print("测试从 osz 文件提取封面功能")
    print("=" * 60)

    # 使用临时目录作为缓存
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "cover-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # 测试谱面 ID
        set_id = "2513401"

        print(f"\n缓存目录: {cache_dir}")
        print(f"测试 BeatmapSetID: {set_id}")
        print(f"测试谱面: https://osu.ppy.sh/beatmapsets/{set_id}")
        print("\n开始从 osz 提取封面...\n")

        cover_data = _extract_cover_from_osz(set_id, cache_dir)

        print("\n" + "=" * 60)
        if cover_data:
            print("✓ 成功从 osz 提取封面！")
            print(f"  封面大小: {len(cover_data)} bytes")
            print(f"  封面格式: ", end="")
            # 检测图片格式
            if cover_data[:2] == b'\xff\xd8':
                print("JPEG")
            elif cover_data[:8] == b'\x89PNG\r\n\x1a\n':
                print("PNG")
            else:
                print("未知")
        else:
            print("✗ 从 osz 提取封面失败")
            print("  请查看上方日志了解失败原因")
        print("=" * 60)

if __name__ == "__main__":
    main()
