"""
综述生成服务
"""

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.messages import HumanMessage

from ..config import llm, survey_section_prompt
from ..models import SurveySection


class SurveyService:
    """综述生成服务"""
    
    def __init__(self):
        """初始化综述服务"""
        self.llm = llm

    def parallel_generate_sections(self, sections: list, topic: str, paper_summaries: list, max_workers: int = 2) -> list[str]:
        """
        并行生成综述章节内容，保证章节顺序
        
        Args:
            sections: 章节列表
            topic: 综述主题
            paper_summaries: 论文摘要列表
            max_workers: 最大并发工作线程数，默认为2（避免API限制）
        
        Returns:
            按原始顺序排列的完整章节内容列表
        """
        def generate_single_section(section_data: tuple) -> tuple[int, str]:
            """生成单个章节内容的包装函数"""
            index, section = section_data
            try:
                print(f"  📝 开始生成第 {index+1} 章：{section.title}")
                
                section_prompt_text = survey_section_prompt.format(
                    section_title=section.title,
                    section_description=section.description,
                    topic=topic,
                    paper_info=chr(10).join([f"论文{j+1}: {summary.title}\n关键贡献: {', '.join(summary.key_contributions)}\n方法: {summary.methodology}\n" for j, summary in enumerate(paper_summaries)])
                )
                
                section_content = self.llm.invoke([HumanMessage(content=section_prompt_text)])
                completed_section = f"## {section.title}\n\n{section_content.content}"
                
                print(f"  ✅ 完成第 {index+1} 章：{section.title}")
                return index, completed_section
                
            except Exception as e:
                print(f"  ❌ 生成第 {index+1} 章失败：{e}")
                return index, f"## {section.title}\n\n生成失败：{str(e)}"
        
        # 创建带索引的章节列表
        indexed_sections = [(i, section) for i, section in enumerate(sections)]
        completed_sections = [None] * len(sections)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {executor.submit(generate_single_section, section_data): section_data[0] 
                              for section_data in indexed_sections}
            
            completed_count = 0

            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    section_index, section_content = future.result()
                    completed_sections[section_index] = section_content
                    completed_count += 1
                    print(f"    🎯 章节生成进度: {completed_count}/{len(sections)}")
                except Exception as e:
                    print(f"    ❌ 处理第 {index+1} 章结果时出错：{e}")
                    completed_sections[index] = f"## 第{index+1}章\n\n生成异常：{str(e)}"
        
        print(f"📊 章节生成统计: 完成 {len([s for s in completed_sections if s])} / {len(sections)} 章")

        return [section for section in completed_sections if section]
