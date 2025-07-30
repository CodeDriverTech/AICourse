"""
配置管理
"""

import os
from dotenv import load_dotenv
load_dotenv()

LANGUAGE = os.getenv("LANGUAGE", "cn")

# 加载提示词
def load_prompts(language='cn'):
    """根据语言动态加载提示词"""
    if language == 'cn':
        from .prompt.prompt_cn import (
            decision_making_prompt,
            planning_prompt, 
            agent_prompt,
            judge_prompt,
            paper_analysis_prompt,
            survey_outline_prompt,
            survey_section_prompt,
            survey_title_abstract_prompt
        )
    else:  # language == 'en'
        from .prompt.prompt_en import (
            decision_making_prompt,
            planning_prompt,
            agent_prompt, 
            judge_prompt,
            paper_analysis_prompt,
            survey_outline_prompt,
            survey_section_prompt,
            survey_title_abstract_prompt
        )
    
    return (
        decision_making_prompt,
        planning_prompt,
        agent_prompt,
        judge_prompt,
        paper_analysis_prompt,
        survey_outline_prompt,
        survey_section_prompt,
        survey_title_abstract_prompt
    )

(decision_making_prompt, planning_prompt, agent_prompt, judge_prompt,
 paper_analysis_prompt, survey_outline_prompt,
 survey_section_prompt, survey_title_abstract_prompt) = load_prompts(LANGUAGE)

# 环境变量配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")
CORE_API_KEY = os.getenv("CORE_API_KEY")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.3))
MAX_SURVEY_REFERENCE = int(os.getenv("MAX_SURVEY_REFERENCE", 10))
SAVE_DIR = os.getenv("SAVE_DIR", "papers")

# LLM初始化
from langchain.chat_models import init_chat_model

llm = init_chat_model(
    model=DEFAULT_MODEL,
    model_provider="openai",
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    temperature=TEMPERATURE,
)
