#!/bin/bash
# 快速状态检查脚本

echo "================================"
echo "🔍 快速状态检查"
echo "================================"
echo ""

# 检查服务器是否运行
if lsof -ti:7070 > /dev/null 2>&1; then
    echo "✅ 服务器运行中 (端口7070)"
else
    echo "❌ 服务器未运行"
    exit 1
fi

echo ""
echo "📊 自动农场状态:"
curl -s http://localhost:7070/api/auto_farm/status | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"  状态: {data.get('status', 'unknown')}\")
    print(f\"  启用: {data.get('enabled', False)}\")
    stats = data.get('stats', {})
    print(f\"  已收获: {stats.get('plants_harvested', 0)}\")
    print(f\"  已播种: {stats.get('seeds_planted', 0)}\")
    print(f\"  已浇水: {stats.get('waterings_done', 0)}\")
    print(f\"  已除草: {stats.get('weeds_removed', 0)}\")
except:
    print('  ❌ 无法获取状态')
" 2>/dev/null

echo ""
echo "🌱 农场概况:"
curl -s http://localhost:7070/api/game/state | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    state = data.get('state', {})
    plants = state.get('plants', [])
    
    empty = sum(1 for p in plants if p.get('is_empty'))
    weeds = sum(1 for p in plants if p.get('is_weed') or p.get('type') == 'weed')
    growing = sum(1 for p in plants if p.get('is_vegetable') and p.get('growth_stage', 0) < 3)
    mature = sum(1 for p in plants if p.get('is_vegetable') and p.get('growth_stage', 0) >= 3 and p.get('health', 0) >= 30)
    
    print(f\"  总格子: {len(plants)}\")
    print(f\"  空地: {empty}\")
    print(f\"  杂草: {weeds}\")
    print(f\"  生长中: {growing}\")
    print(f\"  成熟可收获: {mature}\")
    
    cart = state.get('cart', {})
    print(f\"  小车位置: ({cart.get('x', 0):.2f}, {cart.get('z', 0):.2f})\")
    print(f\"  金币: {state.get('coins', 0)}\")
except:
    print('  ❌ 无法获取农场状态')
" 2>/dev/null

echo ""
echo "================================"


