"""
下载工具模块
"""

import os
import io
import time
import urllib3
import re
import uuid
from datetime import datetime
from urllib.parse import urlparse
import pdfplumber
from langchain_core.tools import tool

from ..config import SAVE_DIR


@tool("download-paper")
def download_paper(url: str) -> str:
    """从给定URL下载特定科学论文（若只给定论文标题，请先使用 `search_papers` 工具进行查询论文，获取下载URL）
    
    示例：
    {"url": "https://sample.pdf"}
    
    返回：
        论文内容
    """
    try:
        http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        
        # 模拟浏览器请求头避免403错误
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        if "arxiv.org/abs" in url:
            url = url.replace("arxiv.org/abs", "arxiv.org/pdf")
        
        max_retries = 5
        for attempt in range(max_retries):
            response = http.request('GET', url, headers=headers)
            if 200 <= response.status < 300:
                pdf_file = io.BytesIO(response.data)

                save_dir = SAVE_DIR
                os.makedirs(save_dir, exist_ok=True)

                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                # print(f"[DEBUG] PDF文件预期保存文件名: {filename}")
                if not str(filename).endswith('.pdf'):
                    # 如果无法从URL获取文件名，使用时间戳+uuid
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_id = str(uuid.uuid4())
                    filename = f"{timestamp}_{unique_id}.pdf"
                
                # 移除不安全字符
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                filepath = os.path.join(save_dir, filename)

                # 保存至本地
                with open(filepath, 'wb') as f:
                    f.write(response.data)
                print(f"📄 PDF文件已保存到: {filepath}")
                
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                return f"📄 PDF文件已保存到: {filepath}\n论文内容: {text}"
            elif attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 2))
            else:
                raise Exception(f"下载论文时收到非2xx状态码: {response.status}")
    except Exception as e:
        return f"下载论文时出错: {e}"
