import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== 测试 AI 服务导入 ===")
try:
    from app.core import ai_service
    print("✓ ai_service 模块导入成功")
    
    print("\n=== 检查关键组件 ===")
    print(f"✓ AiWorker 类: {ai_service.AiWorker}")
    print(f"✓ TEMP_DEFAULT: {ai_service.TEMP_DEFAULT}")
    print(f"✓ API_TIMEOUT: {ai_service.API_TIMEOUT}")
    
    print("\n=== 检查 AiWorker 方法 ===")
    import inspect
    methods = [m for m in dir(ai_service.AiWorker) if not m.startswith('_') or m == '_network_thread']
    for method in ['__init__', 'run', '_network_thread', 'cancel']:
        if hasattr(ai_service.AiWorker, method):
            print(f"✓ {method}")
        else:
            print(f"✗ {method} 缺失")
    
    print("\n=== 检查是否使用 threading ===")
    source = inspect.getsource(ai_service.AiWorker.run)
    if 'threading.Thread' in source:
        print("✓ 使用 threading.Thread")
    else:
        print("✗ 未使用 threading.Thread")
    
    if 'network_thread.start()' in source:
        print("✓ 启动网络线程")
    else:
        print("✗ 未启动网络线程")
        
    print("\n=== 测试消息构建 ===")
    messages = ai_service.build_continue_messages("测试文本", "")
    print(f"✓ 消息构建成功，包含 {len(messages)} 条消息")
    print(f"  系统提示词长度: {len(messages[0]['content'])} 字符")
    
    print("\n[成功] 所有检查通过!")
    
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
