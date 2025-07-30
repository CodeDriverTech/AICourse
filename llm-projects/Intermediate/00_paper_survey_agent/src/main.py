"""
主程序入口
"""

import sys
from langchain_core.messages import HumanMessage

from .core.workflow import app


def main():
    """主程序入口函数"""
    if len(sys.argv) != 2:
        print("用法: python main.py \"你的查询\"")
        print("示例: python main.py \"深度学习中的注意力机制综述\"")
        sys.exit(1)
    
    user_query = sys.argv[1]
    print(f"🚀 开始处理查询: {user_query}")
    print("=" * 80)
    
    try:
        # 初始状态
        initial_state = {
            "messages": [HumanMessage(content=user_query)],
            "requires_research": False,
            "type": None,
            "is_good_answer": False,
            "num_feedback_requests": 0
        }
        
        # 流式执行工作流
        for chunk in app.stream(initial_state):
            if "__end__" not in chunk:
                for node_name, node_output in chunk.items():
                    print(f"\n🔄 节点: {node_name}")
                    if "messages" in node_output and node_output["messages"]:
                        for message in node_output["messages"]:
                            if hasattr(message, 'content'):
                                print(f"💬 输出: {message.content}")
                    print("-" * 60)
    
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎯 程序执行完成")


if __name__ == "__main__":
    main()
