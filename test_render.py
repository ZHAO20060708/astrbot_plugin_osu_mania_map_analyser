#!/usr/bin/env python3
"""测试渲染脚本"""

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from astrbot_service.service_mania_map_analyser import ManiaMapAnalyserService

def main():
    # 铺面 ID
    bid = "5575205"
    
    # 初始化服务
    service = ManiaMapAnalyserService(
        plugin_root=PLUGIN_ROOT,
        render_config={
            "capture_target": "full_card",
            "content_bar": "Auto",
            "sr_text": "Auto",
            "diff_text": "Difficulty",
            "estimator_algorithm": "Mixed",
            "etterna_version": "0.72.3",
            "companella_etterna_version": "0.74.0",
            "enable_numeric_difficulty": True,
            "enable_etterna_rainbow_bars": True,
            "show_mode_tag_capsule": True,
            "vibro_detection": True,
            "debug_use_amount": False,
            "debug_use_sv_detection": True,
            "azusa_sunny_reference_ho": True,
            "card_opacity": "95%",
            "card_blur": "Soft",
            "card_radius": "Medium",
        },
    )
    
    print(f"正在渲染铺面 {bid}...")
    
    try:
        result = service.generate_from_bid(
            bid=bid,
            render_overrides={},
            runtime_overrides={},
        )
        
        print(f"✓ 渲染成功！")
        print(f"图片路径: {result['image_path']}")
        
    except Exception as e:
        print(f"✗ 渲染失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
