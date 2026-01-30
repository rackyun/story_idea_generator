"""
导出功能模块 - 支持多种格式导出小说
"""
from typing import List, Dict, Optional
import re


def _outline_segments_to_lines(title: str, segments: List[Dict], as_markdown: bool) -> List[str]:
    """将大纲段列表格式化为文本行。segments 每项含 start_chapter, end_chapter, title, summary。"""
    lines = []
    if as_markdown:
        lines.append(f"# {title} - 大纲")
    else:
        lines.append(title + " - 大纲")
        lines.append("=" * (len(title) + 4))
    lines.append("")
    for seg in segments:
        ch_range = f"第{seg['start_chapter']}-{seg['end_chapter']}章"
        seg_title = seg.get('title') or ch_range
        summary = (seg.get('summary') or "").strip()
        if as_markdown:
            lines.append(f"## {ch_range} {seg_title}")
        else:
            lines.append(f"{ch_range} {seg_title}")
            lines.append("-" * max(20, len(ch_range) + len(seg_title)))
        lines.append("")
        lines.append(summary)
        lines.append("")
    return lines


class ExportManager:
    """导出管理器"""
    
    @staticmethod
    def export_to_markdown(title: str, chapters: List[Dict], 
                          include_outline: bool = False,
                          metadata: Optional[Dict] = None) -> str:
        """
        导出为 Markdown 格式
        
        Args:
            title: 小说标题
            chapters: 章节列表
            include_outline: 是否包含大纲
            metadata: 元数据信息
        
        Returns:
            Markdown 格式的文本
        """
        lines = []
        
        # 添加 YAML Front Matter
        if metadata:
            lines.append("---")
            lines.append(f"title: {title}")
            if 'author' in metadata:
                lines.append(f"author: {metadata['author']}")
            if 'created_at' in metadata:
                lines.append(f"created: {metadata['created_at']}")
            if 'tags' in metadata:
                tags = metadata['tags'] if isinstance(metadata['tags'], list) else []
                if tags:
                    lines.append(f"tags: [{', '.join(tags)}]")
            lines.append("---")
            lines.append("")
        
        # 标题
        lines.append(f"# {title}")
        lines.append("")
        
        # 章节内容
        for chapter in chapters:
            chapter_title = chapter.get('chapter_title', f"第{chapter.get('chapter_number', '?')}章")
            content = chapter.get('content', '')
            outline = chapter.get('outline', '')
            
            # 章节标题
            lines.append(f"## {chapter_title}")
            lines.append("")
            
            # 大纲（如果需要）
            if include_outline and outline:
                lines.append("**章节大纲**:")
                lines.append(outline)
                lines.append("")
                lines.append("---")
                lines.append("")
            
            # 章节内容
            lines.append(content.strip())
            lines.append("")
            lines.append("")
        
        return '\n'.join(lines)
    
    @staticmethod
    def export_to_txt(title: str, chapters: List[Dict],
                     include_outline: bool = False) -> str:
        """
        导出为纯文本格式
        
        Args:
            title: 小说标题
            chapters: 章节列表
            include_outline: 是否包含大纲
        
        Returns:
            纯文本格式
        """
        lines = []
        
        # 标题
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")
        
        # 章节内容
        for chapter in chapters:
            chapter_title = chapter.get('chapter_title', f"第{chapter.get('chapter_number', '?')}章")
            content = chapter.get('content', '')
            outline = chapter.get('outline', '')
            
            # 章节标题
            lines.append(chapter_title)
            lines.append("-" * len(chapter_title))
            lines.append("")
            
            # 大纲（如果需要）
            if include_outline and outline:
                lines.append("[章节大纲]")
                # 移除 Markdown 标记
                outline_plain = ExportManager._remove_markdown(outline)
                lines.append(outline_plain)
                lines.append("")
            
            # 章节内容（移除 Markdown 标记）
            content_plain = ExportManager._remove_markdown(content)
            lines.append(content_plain.strip())
            lines.append("")
            lines.append("")
        
        return '\n'.join(lines)
    
    @staticmethod
    def _remove_markdown(text: str) -> str:
        """移除 Markdown 标记"""
        # 移除标题标记
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # 移除粗体和斜体
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        
        # 移除链接，保留文本
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        
        # 移除代码块标记
        text = re.sub(r'```.*?\n', '', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        
        # 移除分隔线
        text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
        
        return text
    
    @staticmethod
    def export_to_epub(title: str, chapters: List[Dict],
                      metadata: Optional[Dict] = None,
                      output_path: str = "novel.epub") -> bool:
        """
        导出为 EPUB 格式
        
        Args:
            title: 小说标题
            chapters: 章节列表
            metadata: 元数据
            output_path: 输出文件路径
        
        Returns:
            是否成功
        """
        try:
            from ebooklib import epub
        except ImportError:
            print("需要安装 ebooklib 库: pip install ebooklib")
            return False
        
        # 创建 EPUB 书籍
        book = epub.EpubBook()
        
        # 设置元数据
        book.set_identifier(f'novel_{metadata.get("id", "unknown")}')
        book.set_title(title)
        book.set_language('zh')
        
        if metadata and 'author' in metadata:
            book.add_author(metadata['author'])
        else:
            book.add_author('Unknown')
        
        # 创建章节
        epub_chapters = []
        toc = []
        
        for idx, chapter in enumerate(chapters, start=1):
            chapter_title = chapter.get('chapter_title', f"第{chapter.get('chapter_number', idx)}章")
            content = chapter.get('content', '')
            
            # 创建 EPUB 章节
            epub_chapter = epub.EpubHtml(
                title=chapter_title,
                file_name=f'chapter_{idx}.xhtml',
                lang='zh'
            )
            
            # 设置章节内容（转换 Markdown 到 HTML）
            html_content = ExportManager._markdown_to_html(content)
            epub_chapter.content = f'<h1>{chapter_title}</h1>{html_content}'
            
            book.add_item(epub_chapter)
            epub_chapters.append(epub_chapter)
            toc.append(epub_chapter)
        
        # 设置目录
        book.toc = tuple(toc)
        
        # 添加默认的 NCX 和 Nav 文件
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 定义 CSS 样式
        style = '''
        body { font-family: serif; margin: 2em; }
        h1 { text-align: center; margin-bottom: 2em; }
        p { text-indent: 2em; line-height: 1.8; }
        '''
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)
        
        # 定义书籍的 spine（阅读顺序）
        book.spine = ['nav'] + epub_chapters
        
        # 写入文件
        epub.write_epub(output_path, book, {})
        
        return True
    
    @staticmethod
    def _markdown_to_html(markdown_text: str) -> str:
        """简单的 Markdown 到 HTML 转换"""
        try:
            import markdown
            return markdown.markdown(markdown_text)
        except ImportError:
            # 如果没有 markdown 库，进行简单转换
            lines = markdown_text.split('\n')
            html_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 标题
                if line.startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    text = line.lstrip('#').strip()
                    html_lines.append(f'<h{level}>{text}</h{level}>')
                # 普通段落
                else:
                    html_lines.append(f'<p>{line}</p>')
            
            return '\n'.join(html_lines)
    
    @staticmethod
    def export_to_pdf(title: str, chapters: List[Dict],
                     metadata: Optional[Dict] = None,
                     output_path: str = "novel.pdf") -> bool:
        """
        导出为 PDF 格式
        
        Args:
            title: 小说标题
            chapters: 章节列表
            metadata: 元数据
            output_path: 输出文件路径
        
        Returns:
            是否成功
        """
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
        except ImportError:
            print("需要安装 weasyprint 库: pip install weasyprint")
            return False
        
        # 生成 HTML 内容
        html_content = ExportManager._generate_pdf_html(title, chapters, metadata)
        
        # CSS 样式
        css_content = '''
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: "SimSun", serif;
            font-size: 12pt;
            line-height: 1.8;
        }
        h1 {
            text-align: center;
            font-size: 24pt;
            margin-bottom: 2cm;
            page-break-after: avoid;
        }
        h2 {
            font-size: 18pt;
            margin-top: 1cm;
            margin-bottom: 0.5cm;
            page-break-after: avoid;
        }
        p {
            text-indent: 2em;
            margin-bottom: 0.5em;
        }
        .chapter {
            page-break-before: always;
        }
        .metadata {
            text-align: center;
            color: #666;
            margin-bottom: 2cm;
        }
        '''
        
        # 生成 PDF
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        css = CSS(string=css_content, font_config=font_config)
        html.write_pdf(output_path, stylesheets=[css], font_config=font_config)
        
        return True
    
    @staticmethod
    def _generate_pdf_html(title: str, chapters: List[Dict], 
                          metadata: Optional[Dict] = None) -> str:
        """生成用于 PDF 的 HTML 内容"""
        lines = ['<!DOCTYPE html>', '<html lang="zh">', '<head>',
                '<meta charset="UTF-8">', '</head>', '<body>']
        
        # 标题和元数据
        lines.append(f'<h1>{title}</h1>')
        
        if metadata:
            lines.append('<div class="metadata">')
            if 'author' in metadata:
                lines.append(f'<p>作者: {metadata["author"]}</p>')
            if 'created_at' in metadata:
                lines.append(f'<p>创建时间: {metadata["created_at"]}</p>')
            lines.append('</div>')
        
        # 章节内容
        for idx, chapter in enumerate(chapters):
            chapter_class = 'chapter' if idx > 0 else ''
            lines.append(f'<div class="{chapter_class}">')
            
            chapter_title = chapter.get('chapter_title', f"第{chapter.get('chapter_number', '?')}章")
            lines.append(f'<h2>{chapter_title}</h2>')
            
            content = chapter.get('content', '')
            # 转换段落
            paragraphs = content.split('\n')
            for para in paragraphs:
                para = para.strip()
                if para:
                    lines.append(f'<p>{para}</p>')
            
            lines.append('</div>')
        
        lines.extend(['</body>', '</html>'])
        
        return '\n'.join(lines)
