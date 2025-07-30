"""
论文处理服务
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import pdfplumber
from langchain_core.messages import HumanMessage

from ..config import SAVE_DIR, llm, paper_analysis_prompt
from ..models import PaperSummary


class PaperService:
    """论文处理服务"""
    
    def __init__(self):
        """初始化论文服务"""
        self.llm = llm

    def extract_paper_content_from_save_dir(self) -> list[dict]:
        """从保存目录中提取已下载的论文信息"""
        papers_info = []

        if not SAVE_DIR or not os.path.exists(SAVE_DIR):
            print(f"⚠️ 保存目录 {SAVE_DIR} 不存在")
            return papers_info

        try:
            for filename in os.listdir(SAVE_DIR):
                if filename.lower().endswith('.pdf'):
                    filepath = os.path.join(SAVE_DIR, filename)
                    print(f"📄 读取PDF文件: {filename}")
                    
                    try:
                        with pdfplumber.open(filepath) as pdf:
                            text_content = ""
                            for page in pdf.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    text_content += page_text + "\n"
                            
                            if text_content.strip():
                                papers_info.append({
                                    'filepath': filepath,
                                    'filename': filename,
                                    'content': text_content.strip()
                                })
                                print(f"  ✅ 成功读取，内容长度: {len(text_content)} 字符")
                            else:
                                print(f"  ⚠️ PDF文件 {filename} 内容为空")
                                
                    except Exception as e:
                        print(f"  ❌ 读取PDF文件 {filename} 失败: {e}")
                        
        except Exception as e:
            print(f"❌ 遍历保存目录失败: {e}")
        
        return papers_info

    def summarize_paper_content(self, paper_content: str, topic: str) -> PaperSummary:
        """使用LLM总结论文内容"""
        summarize_llm = self.llm.with_structured_output(PaperSummary)

        prompt = paper_analysis_prompt.format(
            topic=topic,
            paper_content=paper_content[:65536]  # 限定长度为 64K 字符，约等于 32K Tokens，以确保模型响应质量的有效性。
        )
        
        try:
            summary = summarize_llm.invoke([HumanMessage(content=prompt)])
            return summary
        except Exception as e:
            # 如果结构化输出失败，返回基本信息
            return PaperSummary(
                title="未能提取标题",
                abstract="论文内容解析失败",
                key_contributions=["解析失败"],
                methodology="未知",
                limitations="未知",
                relevance_score=1
            )
