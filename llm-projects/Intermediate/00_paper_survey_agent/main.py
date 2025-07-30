#!/usr/bin/env python3
"""
科学论文调研智能助手 - 主入口文件

基于LangGraph构建的科学论文调研和分析工具，支持通过CORE API搜索论文、
下载PDF文件、提取内容并生成智能分析报告。

使用方法：
    python main.py "你的查询"
    
示例：
    python main.py "深度学习中的注意力机制综述"

环境要求：
    - OPENAI_API_KEY: OpenAI API密钥
    - OPENAI_BASE_URL: OpenAI API基础URL
    - DEFAULT_MODEL: 默认模型
    - CORE_API_KEY: CORE API密钥 (可在 https://core.ac.uk/services/api#form 申请)
    - TEMPERATURE: 温度参数
    - MAX_SURVEY_REFERENCE: 最大参考文献数量
    - SAVE_DIR: 保存目录
"""

from src.main import main

if __name__ == "__main__":
    main()
