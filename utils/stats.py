"""
统计功能模块 - 提供数据统计和可视化支持
"""
from typing import List, Dict
from datetime import datetime, timedelta
from utils.novel_length_config import get_length_category, format_length_description


class StatsHelper:
    """统计辅助类"""
    
    @staticmethod
    def calculate_word_count(text: str) -> int:
        """计算字数（中英文）"""
        # 移除空白字符
        text = text.strip()
        
        # 统计中文字符
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        
        # 统计英文单词（简单按空格分割）
        words = text.split()
        english_words = sum(1 for word in words if any(c.isalpha() for c in word))
        
        # 返回总计
        return chinese_chars + english_words
    
    @staticmethod
    def format_word_count(count: int) -> str:
        """格式化字数显示"""
        # 处理 None 值或非数字类型
        if count is None:
            return "0字"
        
        # 确保是数字类型
        try:
            count = int(count)
        except (ValueError, TypeError):
            return "0字"
        
        if count < 1000:
            return f"{count}字"
        elif count < 10000:
            return f"{count/1000:.1f}千字"
        else:
            return f"{count/10000:.1f}万字"
    
    @staticmethod
    def calculate_reading_time(word_count: int, words_per_minute: int = 300) -> str:
        """
        计算阅读时间
        
        Args:
            word_count: 字数
            words_per_minute: 每分钟阅读字数
        
        Returns:
            格式化的阅读时间
        """
        # 处理 None 值或非数字类型
        if word_count is None:
            word_count = 0
        
        try:
            word_count = int(word_count)
        except (ValueError, TypeError):
            word_count = 0
        
        if word_count <= 0:
            return "< 1分钟"
        
        minutes = word_count / words_per_minute
        
        if minutes < 1:
            return "< 1分钟"
        elif minutes < 60:
            return f"{int(minutes)}分钟"
        else:
            hours = minutes / 60
            return f"{hours:.1f}小时"
    
    @staticmethod
    def prepare_chart_data(timeline: List[Dict]) -> Dict:
        """
        准备图表数据
        
        Args:
            timeline: 时间线数据
        
        Returns:
            格式化的图表数据
        """
        if not timeline:
            return {
                'dates': [],
                'words': [],
                'chapters': []
            }
        
        dates = [item['date'] for item in timeline]
        words = [item.get('words_written', 0) for item in timeline]
        chapters = [item.get('chapters_created', 0) for item in timeline]
        
        return {
            'dates': dates,
            'words': words,
            'chapters': chapters
        }
    
    @staticmethod
    def calculate_progress(completed: int, total: int) -> float:
        """
        计算进度百分比
        
        Args:
            completed: 已完成数
            total: 总数
        
        Returns:
            进度百分比（0-100）
        """
        if total == 0:
            return 0.0
        
        return (completed / total) * 100
    
    @staticmethod
    def generate_summary(stats: Dict) -> str:
        """
        生成统计摘要文本
        
        Args:
            stats: 统计数据字典
        
        Returns:
            摘要文本
        """
        lines = []
        
        total_words = stats.get('total_words') or 0
        total_chapters = stats.get('total_chapters') or 0
        avg_words = stats.get('avg_words_per_chapter') or 0
        
        lines.append(f"📊 统计摘要")
        lines.append(f"总字数: {StatsHelper.format_word_count(total_words)}")
        lines.append(f"总章节数: {total_chapters} 章")
        
        if avg_words and avg_words > 0:
            try:
                avg_words_int = int(avg_words)
                lines.append(f"平均每章: {StatsHelper.format_word_count(avg_words_int)}")
            except (ValueError, TypeError):
                pass
        
        # 阅读时间
        reading_time = StatsHelper.calculate_reading_time(total_words)
        lines.append(f"预计阅读时间: {reading_time}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def get_daily_stats(timeline: List[Dict], days: int = 7) -> Dict:
        """
        获取最近N天的统计
        
        Args:
            timeline: 时间线数据
            days: 天数
        
        Returns:
            最近N天的统计数据
        """
        if not timeline:
            return {
                'total_words': 0,
                'total_chapters': 0,
                'avg_words_per_day': 0
            }
        
        # 按日期排序
        sorted_timeline = sorted(timeline, key=lambda x: x['date'], reverse=True)
        
        # 获取最近N天的数据
        recent_data = sorted_timeline[:days]
        
        total_words = sum(item.get('words_written', 0) for item in recent_data)
        total_chapters = sum(item.get('chapters_created', 0) for item in recent_data)
        
        return {
            'total_words': total_words,
            'total_chapters': total_chapters,
            'avg_words_per_day': total_words / len(recent_data) if recent_data else 0,
            'days': len(recent_data)
        }

    @staticmethod
    def get_novel_length_category(word_count: int) -> str:
        """
        获取小说篇幅分类名称

        Args:
            word_count: 字数

        Returns:
            分类名称（如 "微型小说"、"短篇小说" 等）
        """
        category = get_length_category(word_count)
        return category.name

    @staticmethod
    def format_novel_length(word_count: int) -> str:
        """
        格式化小说篇幅描述

        Args:
            word_count: 字数

        Returns:
            格式化的描述，如 "微型小说 (0.8万字)"
        """
        return format_length_description(word_count)

    @staticmethod
    def get_length_category_info(word_count: int) -> Dict:
        """
        获取小说篇幅分类的详细信息

        Args:
            word_count: 字数

        Returns:
            包含分类信息的字典
        """
        category = get_length_category(word_count)
        return {
            'key': category.key,
            'name': category.name,
            'description': category.description,
            'min_words': category.min_words,
            'max_words': category.max_words,
            'formatted': format_length_description(word_count)
        }

