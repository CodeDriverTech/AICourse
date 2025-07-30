"""
CORE API封装
"""

import os
import time
from typing import ClassVar, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from pydantic import BaseModel

from ..config import CORE_API_KEY


class CoreAPIWrapper(BaseModel):
    """CORE API的简单封装"""
    base_url: ClassVar[str] = "https://api.core.ac.uk/v3"
    api_key: ClassVar[str] = CORE_API_KEY
    top_k_results: int = 1

    def _get_search_response(self, query: str) -> Dict[str, Any]:
        """获取搜索响应"""
        url = f"{self.base_url}/search/works"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "q": query,
            "limit": self.top_k_results,
            "offset": 0,
            "scroll": False
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=data, headers=headers, timeout=30)
                response.raise_for_status()
                original_output = response.json()
                
                # 并行下载论文
                download_urls = [result.get("downloadUrl") for result in original_output.get("results", []) if result.get("downloadUrl")]
                if download_urls:
                    print(f"🚀 开始并行下载 {len(download_urls)} 篇论文...")
                    self._parallel_download_papers(download_urls)
                
                return original_output
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(f"CORE API请求失败: {e}")
    
    def _parallel_download_papers(self, download_urls: list[str], max_workers: int = 3) -> None:
        """
        并行下载多篇论文
        
        Args:
            download_urls: 下载链接列表
            max_workers: 最大并发工作线程数，默认为3
        """
        def download_single_paper(url: str) -> tuple[str, bool, str]:
            """下载单篇论文的包装函数"""
            try:
                from ..tools.download_tools import download_paper
                result = download_paper(url)
                return url, True, result
            except Exception as e:
                return url, False, str(e)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(download_single_paper, url): url for url in download_urls}
            
            completed_count = 0
            failed_count = 0
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    original_url, success, result = future.result()
                    if success:
                        completed_count += 1
                        print(f"  ✅ 下载完成 ({completed_count}/{len(download_urls)}): {os.path.basename(original_url)}")
                    else:
                        failed_count += 1
                        print(f"  ❌ 下载失败 ({failed_count}/{len(download_urls)}): {result}")
                except Exception as e:
                    failed_count += 1
                    print(f"  ❌ 下载异常 ({failed_count}/{len(download_urls)}): {e}")
            
            print(f"📊 下载统计: 成功 {completed_count} 篇, 失败 {failed_count} 篇")

    def search(self, query: str) -> str:
        """搜索论文"""
        response = self._get_search_response(query)
        results = response.get("results", [])
        if not results:
            return "未找到相关结果"

        # 格式化结果
        docs = []
        for result in results:
            published_date_str = result.get('publishedDate') or result.get('yearPublished', '')
            authors_str = ' and '.join([item['name'] for item in result.get('authors', [])])
            docs.append((
                f"* ID: {result.get('id', '')}\n"
                f"* 标题: {result.get('title', '')}\n"
                f"* 发表日期: {published_date_str}\n"
                f"* 作者: {authors_str}\n"
                f"* 摘要: {result.get('abstract', '')}\n"
                f"* 论文下载链接: {result.get('downloadUrl') or result.get('sourceFulltextUrls', '')}"
            ))
        return "\n-----\n".join(docs)
