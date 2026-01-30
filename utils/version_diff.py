"""
版本对比工具 - 提供文本差异对比功能
"""
import difflib
from typing import List, Tuple, Dict


class VersionDiff:
    """版本差异对比类"""
    
    @staticmethod
    def generate_unified_diff(text1: str, text2: str, 
                             name1: str = "版本1", 
                             name2: str = "版本2") -> List[str]:
        """
        生成统一差异格式
        
        Args:
            text1: 第一个版本的文本
            text2: 第二个版本的文本
            name1: 第一个版本的名称
            name2: 第二个版本的名称
        
        Returns:
            差异行列表
        """
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            lines1, lines2,
            fromfile=name1,
            tofile=name2,
            lineterm=''
        )
        
        return list(diff)
    
    @staticmethod
    def generate_html_diff(text1: str, text2: str,
                          name1: str = "版本1",
                          name2: str = "版本2") -> str:
        """
        生成 HTML 格式的差异对比
        
        Args:
            text1: 第一个版本的文本
            text2: 第二个版本的文本
            name1: 第一个版本的名称
            name2: 第二个版本的名称
        
        Returns:
            HTML 格式的差异对比
        """
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        differ = difflib.HtmlDiff()
        html = differ.make_file(
            lines1, lines2,
            fromdesc=name1,
            todesc=name2,
            context=True,
            numlines=3
        )
        
        return html
    
    @staticmethod
    def get_change_summary(text1: str, text2: str) -> Dict[str, int]:
        """
        获取变更摘要统计
        
        Args:
            text1: 第一个版本的文本
            text2: 第二个版本的文本
        
        Returns:
            包含新增、删除、修改行数的字典
        """
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        
        added = 0
        deleted = 0
        modified = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'insert':
                added += (j2 - j1)
            elif tag == 'delete':
                deleted += (i2 - i1)
            elif tag == 'replace':
                modified += max(i2 - i1, j2 - j1)
        
        return {
            'added': added,
            'deleted': deleted,
            'modified': modified,
            'total_changes': added + deleted + modified
        }
    
    @staticmethod
    def generate_side_by_side_diff(text1: str, text2: str) -> List[Tuple[str, str, str]]:
        """
        生成并排对比数据
        
        Args:
            text1: 第一个版本的文本
            text2: 第二个版本的文本
        
        Returns:
            包含 (状态, 左侧文本, 右侧文本) 的元组列表
            状态可以是: 'equal', 'delete', 'insert', 'replace'
        """
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        result = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for i in range(i1, i2):
                    result.append(('equal', lines1[i], lines2[j1 + (i - i1)]))
            
            elif tag == 'delete':
                for i in range(i1, i2):
                    result.append(('delete', lines1[i], ''))
            
            elif tag == 'insert':
                for j in range(j1, j2):
                    result.append(('insert', '', lines2[j]))
            
            elif tag == 'replace':
                # 处理替换：可能行数不同
                for i in range(i1, i2):
                    j = j1 + (i - i1)
                    if j < j2:
                        result.append(('replace', lines1[i], lines2[j]))
                    else:
                        result.append(('delete', lines1[i], ''))
                
                # 如果右侧还有剩余行
                for j in range(j1 + (i2 - i1), j2):
                    result.append(('insert', '', lines2[j]))
        
        return result
    
    @staticmethod
    def format_diff_for_display(diff_lines: List[str]) -> str:
        """
        格式化差异输出用于显示
        
        Args:
            diff_lines: 差异行列表
        
        Returns:
            格式化的文本
        """
        formatted_lines = []
        
        for line in diff_lines:
            line = line.rstrip('\n')
            
            # 添加颜色标记（使用 Streamlit 的 markdown）
            if line.startswith('+') and not line.startswith('+++'):
                formatted_lines.append(f"🟢 {line}")
            elif line.startswith('-') and not line.startswith('---'):
                formatted_lines.append(f"🔴 {line}")
            elif line.startswith('@@'):
                formatted_lines.append(f"**{line}**")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
        
        Returns:
            相似度（0-1之间）
        """
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    @staticmethod
    def find_common_substring(text1: str, text2: str) -> str:
        """
        查找两个文本的最长公共子串
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
        
        Returns:
            最长公共子串
        """
        matcher = difflib.SequenceMatcher(None, text1, text2)
        match = matcher.find_longest_match(0, len(text1), 0, len(text2))
        
        if match.size > 0:
            return text1[match.a:match.a + match.size]
        
        return ""
