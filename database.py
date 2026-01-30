import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import re


class DatabaseManager:
    """数据库管理器 - 管理故事记录的核心 CRUD 操作"""
    
    def __init__(self, db_path: str = "stories.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以像字典一样访问
        return conn
    
    def init_db(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # stories 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                title TEXT,
                topic TEXT,
                content TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                is_deleted INTEGER DEFAULT 0
            )
        """)
        
        # story_relations 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS story_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL,
                child_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES stories(id),
                FOREIGN KEY (child_id) REFERENCES stories(id)
            )
        """)
        
        # novels 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS novels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                topic TEXT,
                content TEXT,
                metadata TEXT,
                source_story_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (source_story_id) REFERENCES stories(id)
            )
        """)

        # chapters 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER NOT NULL,
                chapter_number INTEGER NOT NULL,
                chapter_title TEXT,
                content TEXT,
                word_count INTEGER DEFAULT 0,
                outline TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        
        # novel_versions 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS novel_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER NOT NULL,
                version_name TEXT NOT NULL,
                version_note TEXT,
                snapshot_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        
        # novel_metadata 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS novel_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER NOT NULL UNIQUE,
                total_chapters INTEGER DEFAULT 0,
                total_words INTEGER DEFAULT 0,
                tags TEXT,
                status TEXT DEFAULT 'writing',
                outline_id INTEGER,
                last_updated TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (novel_id) REFERENCES novels(id),
                FOREIGN KEY (outline_id) REFERENCES stories(id)
            )
        """)
        
        # novel_outlines 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS novel_outlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER NOT NULL,
                version INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 0,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        
        # outline_segments 表 (按段管理的大纲)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outline_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                novel_id INTEGER NOT NULL,
                segment_order INTEGER NOT NULL,
                start_chapter INTEGER NOT NULL,
                end_chapter INTEGER NOT NULL,
                title TEXT,
                summary TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (novel_id) REFERENCES novels(id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stories_type ON stories(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stories_created_at ON stories(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_novels_created_at ON novels(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_novels_source_id ON novels(source_story_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chapters_novel_id ON chapters(novel_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chapters_number ON chapters(chapter_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_versions_novel_id ON novel_versions(novel_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chapters_novel_number ON chapters(novel_id, chapter_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_outlines_novel_id ON novel_outlines(novel_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_outline_segments_novel_id ON outline_segments(novel_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_outline_segments_order ON outline_segments(novel_id, segment_order)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_outline_segments_chapters ON outline_segments(novel_id, start_chapter, end_chapter)")
        
        conn.commit()
        conn.close()
    
    def save_story(self, story_type: str, title: str, topic: str, content: str, 
                   metadata: Optional[Dict] = None) -> int:
        """保存新故事记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        
        cursor.execute("""
            INSERT INTO stories (type, title, topic, content, metadata, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (story_type, title, topic, content, metadata_json, datetime.now()))
        
        story_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return story_id
    
    def get_story(self, story_id: int) -> Optional[Dict]:
        """获取单条故事记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM stories WHERE id = ? AND is_deleted = 0
        """, (story_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            story = dict(row)
            if story['metadata']:
                story['metadata'] = json.loads(story['metadata'])
            return story
        return None
    
    def list_stories(self, story_type: Optional[str] = None, 
                    search_query: Optional[str] = None,
                    page: int = 1, page_size: int = 20,
                    order_by: str = 'created_at DESC') -> Tuple[List[Dict], int]:
        """列表查询故事记录（支持分页、筛选、搜索）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = ["is_deleted = 0"]
        params = []
        
        if story_type:
            conditions.append("type = ?")
            params.append(story_type)
        
        if search_query:
            conditions.append("(title LIKE ? OR topic LIKE ? OR content LIKE ?)")
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        where_clause = " AND ".join(conditions)
        
        # 查询总数
        cursor.execute(f"SELECT COUNT(*) FROM stories WHERE {where_clause}", params)
        total_count = cursor.fetchone()[0]
        
        # 查询数据
        offset = (page - 1) * page_size
        query = f"""
            SELECT id, type, title, topic, 
                   substr(content, 1, 200) as content_preview,
                   created_at, updated_at
            FROM stories 
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        stories = [dict(row) for row in rows]
        return stories, total_count
    
    def delete_story(self, story_id: int, soft: bool = True) -> bool:
        """删除故事记录（默认软删除）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if soft:
            cursor.execute("""
                UPDATE stories SET is_deleted = 1, updated_at = ?
                WHERE id = ?
            """, (datetime.now(), story_id))
        else:
            cursor.execute("DELETE FROM stories WHERE id = ?", (story_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def hard_delete_story(self, story_id: int) -> bool:
        """硬删除故事记录"""
        return self.delete_story(story_id, soft=False)
    
    def update_story(self, story_id: int, title: Optional[str] = None,
                    content: Optional[str] = None, metadata: Optional[Dict] = None) -> bool:
        """更新故事记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata, ensure_ascii=False))
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(story_id)
        
        query = f"UPDATE stories SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def create_relation(self, parent_id: int, child_id: int) -> int:
        """创建父子关联关系"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO story_relations (parent_id, child_id)
            VALUES (?, ?)
        """, (parent_id, child_id))
        
        relation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return relation_id
    
    def get_story_history(self, story_id: int) -> List[Dict]:
        """获取故事的重新生成历史链"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. 查找所有子记录 (stories表中的crew_ai等)
        cursor.execute("""
            SELECT s.*, sr.created_at as relation_created_at
            FROM story_relations sr
            JOIN stories s ON s.id = sr.child_id
            WHERE sr.parent_id = ? AND s.is_deleted = 0
        """, (story_id,))
        story_rows = cursor.fetchall()
        
        # 2. 查找关联的小说 (novels表)
        cursor.execute("""
            SELECT n.*, n.created_at as relation_created_at, 'full_novel' as type
            FROM novels n
            WHERE n.source_story_id = ? AND n.is_deleted = 0
        """, (story_id,))
        novel_rows = cursor.fetchall()
        
        conn.close()
        
        history = []
        for row in story_rows:
            item = dict(row)
            if item.get('metadata'):
                item['metadata'] = json.loads(item['metadata'])
            history.append(item)
            
        for row in novel_rows:
            item = dict(row)
            if item.get('metadata'):
                item['metadata'] = json.loads(item['metadata'])
            # 确保包含必要的字段以兼容前端显示
            history.append(item)
            
        # 按创建时间倒序排序
        history.sort(key=lambda x: x.get('relation_created_at', x.get('created_at')), reverse=True)
        
        return history


class NovelManager:
    """小说管理器 - 管理完整小说记录"""
    
    def __init__(self, db_path: str = "stories.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_novel(self, title: str, topic: str, content: str,
                   source_story_id: Optional[int] = None, metadata: Optional[Dict] = None) -> int:
        """保存新小说记录

        Args:
            title: 小说标题
            topic: 小说主题
            content: 小说内容
            source_story_id: 关联的企划书 ID（可选，如果为 None 则小说独立存在）
            metadata: 元数据字典

        Returns:
            新创建的小说 ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        
        cursor.execute("""
            INSERT INTO novels (title, topic, content, metadata, source_story_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, topic, content, metadata_json, source_story_id, datetime.now()))
        
        novel_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return novel_id

    def get_novel(self, novel_id: int) -> Optional[Dict]:
        """获取单条小说记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT *, 'full_novel' as type FROM novels WHERE id = ? AND is_deleted = 0
        """, (novel_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            novel = dict(row)
            if novel['metadata']:
                novel['metadata'] = json.loads(novel['metadata'])
            return novel
        return None
    
    def list_novels(self, search_query: Optional[str] = None,
                   page: int = 1, page_size: int = 20,
                   order_by: str = 'created_at DESC') -> Tuple[List[Dict], int]:
        """列表查询小说记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = ["is_deleted = 0"]
        params = []
        
        if search_query:
            conditions.append("(title LIKE ? OR topic LIKE ? OR content LIKE ?)")
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        where_clause = " AND ".join(conditions)
        
        # 查询总数
        cursor.execute(f"SELECT COUNT(*) FROM novels WHERE {where_clause}", params)
        total_count = cursor.fetchone()[0]
        
        # 查询数据
        offset = (page - 1) * page_size
        query = f"""
            SELECT id, title, topic, 
                   substr(content, 1, 200) as content_preview,
                   created_at, updated_at, 'full_novel' as type
            FROM novels 
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        novels = [dict(row) for row in rows]
        return novels, total_count
        
    def update_novel(self, novel_id: int, title: Optional[str] = None,
                    content: Optional[str] = None, metadata: Optional[Dict] = None) -> bool:
        """更新小说记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata, ensure_ascii=False))
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(novel_id)
        
        query = f"UPDATE novels SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success

    def delete_novel(self, novel_id: int, soft: bool = True) -> bool:
        """删除小说记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if soft:
            cursor.execute("""
                UPDATE novels SET is_deleted = 1, updated_at = ?
                WHERE id = ?
            """, (datetime.now(), novel_id))
        else:
            cursor.execute("DELETE FROM novels WHERE id = ?", (novel_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success


class ChapterManager:
    """章节管理器 - 管理长篇小说的章节"""
    
    def __init__(self, db_path: str = "stories.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_chapter(self, novel_id: int, chapter_number: int, 
                      chapter_title: str, content: str = "",
                      outline: str = "", status: str = "draft") -> int:
        """创建新章节"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        word_count = len(content)
        
        cursor.execute("""
            INSERT INTO chapters 
            (novel_id, chapter_number, chapter_title, content, word_count, outline, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (novel_id, chapter_number, chapter_title, content, word_count, outline, status, datetime.now()))
        
        chapter_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return chapter_id
    
    def update_chapter(self, chapter_id: int, chapter_title: Optional[str] = None,
                      content: Optional[str] = None, outline: Optional[str] = None,
                      status: Optional[str] = None) -> bool:
        """更新章节"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if chapter_title is not None:
            updates.append("chapter_title = ?")
            params.append(chapter_title)
        
        if content is not None:
            updates.append("content = ?")
            params.append(content)
            updates.append("word_count = ?")
            params.append(len(content))
        
        if outline is not None:
            updates.append("outline = ?")
            params.append(outline)
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(chapter_id)
        
        query = f"UPDATE chapters SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_chapter(self, chapter_id: int, soft: bool = True) -> bool:
        """删除章节"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if soft:
            cursor.execute("""
                UPDATE chapters SET is_deleted = 1, updated_at = ?
                WHERE id = ?
            """, (datetime.now(), chapter_id))
        else:
            cursor.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_chapter(self, chapter_id: int) -> Optional[Dict]:
        """获取单个章节"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM chapters WHERE id = ? AND is_deleted = 0
        """, (chapter_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def list_chapters(self, novel_id: int, include_deleted: bool = False) -> List[Dict]:
        """获取小说的所有章节（按序号排序）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        where_clause = "novel_id = ?"
        if not include_deleted:
            where_clause += " AND is_deleted = 0"
        
        cursor.execute(f"""
            SELECT * FROM chapters 
            WHERE {where_clause}
            ORDER BY chapter_number ASC
        """, (novel_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def reorder_chapters(self, chapter_ids_in_order: List[int]) -> bool:
        """调整章节顺序"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for new_number, chapter_id in enumerate(chapter_ids_in_order, start=1):
                cursor.execute("""
                    UPDATE chapters 
                    SET chapter_number = ?, updated_at = ?
                    WHERE id = ?
                """, (new_number, datetime.now(), chapter_id))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error reordering chapters: {e}")
            return False
        finally:
            conn.close()
    
    def parse_chapters_from_content(self, content: str) -> List[Dict[str, Any]]:
        """从完整内容中解析章节（用于迁移）"""
        chapters = []
        
        # 匹配多种 Markdown 格式的章节标题
        # 支持: ## 第一章、## Chapter 1、## 第1章、# 第一章 等
        # 优先匹配包含"第X章"的格式（支持汉字数字和阿拉伯数字）
        patterns = [
            r'^##\s+第([一二三四五六七八九十百\d]+)章[：:\s]+(.+?)$',  # ## 第一章：标题 或 ## 第1章 标题（有冒号或空格）
            r'^##\s+第([一二三四五六七八九十百\d]+)章([^\s：:].*)$',  # ## 第一章标题（无冒号无空格，直接跟标题）
            r'^##\s+第([一二三四五六七八九十百\d]+)章$',  # ## 第一章（无标题）
            r'^#\s+第([一二三四五六七八九十百\d]+)章[：:\s]+(.+?)$',  # # 第一章：标题
            r'^#\s+第([一二三四五六七八九十百\d]+)章([^\s：:].*)$',  # # 第一章标题（无冒号无空格）
            r'^#\s+第([一二三四五六七八九十百\d]+)章$',  # # 第一章（无标题）
            r'^第([一二三四五六七八九十百\d]+)章[：:\s]+(.+?)$',  # 第一章：标题（无Markdown标记）
            r'^第([一二三四五六七八九十百\d]+)章([^\s：:].*)$',  # 第一章标题（无Markdown标记，无冒号无空格）
            r'^第([一二三四五六七八九十百\d]+)章$',  # 第一章（无Markdown标记，无标题）
            r'^##\s+(.+?)$',  # ## 标题（通用格式）
            r'^#\s+(.+?)$',   # # 标题（一级标题，可能是章节）
            r'^Chapter\s+\d+[：:]\s*(.+?)$',  # Chapter 1: 标题
        ]
        
        lines = content.split('\n')
        current_chapter = None
        chapter_number = 0
        
        for line in lines:
            line_stripped = line.strip()
            matched = False
            
            # 尝试匹配各种章节标题格式
            for pattern_idx, pattern in enumerate(patterns):
                match = re.match(pattern, line_stripped)
                if match:
                    # 保存上一章
                    if current_chapter:
                        chapters.append(current_chapter)
                    
                    # 开始新章
                    chapter_number += 1
                    
                    # 根据不同的 pattern 提取标题
                    # 前9个 pattern 是"第X章"格式，group(1)是章节号，group(2)是标题（如果有）
                    if pattern_idx < 9:
                        # "第X章"格式
                        chapter_num_str = match.group(1) if match.lastindex >= 1 else ""
                        chapter_title = match.group(2).strip() if match.lastindex >= 2 and match.group(2) else ""

                        # 如果没有标题，尝试从下一行获取
                        if not chapter_title:
                            if len(lines) > lines.index(line) + 1:
                                next_line = lines[lines.index(line) + 1].strip()
                                if next_line and len(next_line) < 50 and not next_line.startswith('#'):
                                    chapter_title = next_line

                        # 如果还是没有标题，使用"第X章"作为完整标题
                        if not chapter_title:
                            chapter_title = f"第{chapter_num_str}章"
                    else:
                        # 其他格式，group(1)就是标题
                        chapter_title = match.group(1).strip() if match.lastindex >= 1 else match.group(0).strip()
                        # 清理标题（移除可能的标记符号）
                        chapter_title = re.sub(r'^[#\s]+', '', chapter_title)
                        
                        # 如果标题为空或太短，尝试从下一行获取
                        if not chapter_title or len(chapter_title) < 2:
                            if len(lines) > lines.index(line) + 1:
                                next_line = lines[lines.index(line) + 1].strip()
                                if next_line and len(next_line) < 50:
                                    chapter_title = next_line
                        
                        # 如果还是没有标题，使用默认格式（尝试使用汉字数字）
                        if not chapter_title or len(chapter_title) < 2:
                            # 尝试将章节号转换为汉字数字
                            def num_to_chinese(num):
                                chinese_nums = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
                                if num <= 10:
                                    return chinese_nums[num]
                                elif num < 20:
                                    return '十' + (chinese_nums[num % 10] if num % 10 > 0 else '')
                                elif num < 100:
                                    tens = num // 10
                                    ones = num % 10
                                    if ones == 0:
                                        return chinese_nums[tens] + '十'
                                    else:
                                        return chinese_nums[tens] + '十' + chinese_nums[ones]
                                else:
                                    return str(num)
                            chapter_title = f"第{num_to_chinese(chapter_number)}章"
                    
                    current_chapter = {
                        'chapter_number': chapter_number,
                        'chapter_title': chapter_title,
                        'content': ''
                    }
                    matched = True
                    break
            
            if not matched and current_chapter:
                current_chapter['content'] += line + '\n'
        
        # 保存最后一章
        if current_chapter:
            chapters.append(current_chapter)
        
        # 如果没有解析到章节，尝试从内容中提取标题
        if not chapters and content.strip():
            # 尝试从第一行提取标题
            first_line = content.split('\n')[0].strip()
            # 移除可能的 Markdown 标记
            first_line = re.sub(r'^[#\s]+', '', first_line)
            
            # 如果第一行看起来像标题（长度适中，不包含太多标点）
            if first_line and 5 <= len(first_line) <= 50 and first_line.count('。') < 2:
                chapter_title = first_line
            else:
                # 尝试从内容前100字中提取可能的标题
                preview = content[:100].strip()
                # 查找可能的标题模式
                title_match = re.search(r'第[一二三四五六七八九十\d]+章[：:]?\s*([^\n。]+)', preview)
                if title_match:
                    chapter_title = title_match.group(1).strip()
                else:
                    chapter_title = "第一章"
            
            chapters.append({
                'chapter_number': 1,
                'chapter_title': chapter_title,
                'content': content
            })
        
        return chapters


class NovelVersionManager:
    """小说版本管理器"""
    
    def __init__(self, db_path: str = "stories.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_version(self, novel_id: int, version_name: str,
                      version_note: str = "", snapshot_data: Dict = None) -> int:
        """创建新版本快照"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        snapshot_json = json.dumps(snapshot_data, ensure_ascii=False) if snapshot_data else "{}"
        
        cursor.execute("""
            INSERT INTO novel_versions 
            (novel_id, version_name, version_note, snapshot_data)
            VALUES (?, ?, ?, ?)
        """, (novel_id, version_name, version_note, snapshot_json))
        
        version_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return version_id
    
    def list_versions(self, novel_id: int) -> List[Dict]:
        """获取所有版本列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, novel_id, version_name, version_note, created_at, created_by
            FROM novel_versions
            WHERE novel_id = ?
            ORDER BY created_at DESC
        """, (novel_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_version(self, version_id: int) -> Optional[Dict]:
        """获取指定版本内容"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM novel_versions WHERE id = ?
        """, (version_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            version = dict(row)
            version['snapshot_data'] = json.loads(version['snapshot_data'])
            return version
        return None
    
    def compare_versions(self, version_id_1: int, version_id_2: int) -> Dict:
        """版本对比（返回差异）"""
        import difflib
        
        version1 = self.get_version(version_id_1)
        version2 = self.get_version(version_id_2)
        
        if not version1 or not version2:
            return {"error": "Version not found"}
        
        # 获取两个版本的内容
        content1 = version1['snapshot_data'].get('content', '')
        content2 = version2['snapshot_data'].get('content', '')
        
        # 生成差异
        diff = difflib.unified_diff(
            content1.splitlines(keepends=True),
            content2.splitlines(keepends=True),
            fromfile=f"{version1['version_name']}",
            tofile=f"{version2['version_name']}"
        )
        
        return {
            'version1': version1,
            'version2': version2,
            'diff': list(diff)
        }
    
    def restore_version(self, version_id: int) -> bool:
        """恢复到指定版本"""
        # 这个方法需要配合 DatabaseManager 和 ChapterManager 使用
        # 实现在具体使用时完成
        pass


class NovelStatsManager:
    """小说统计管理器"""
    
    def __init__(self, db_path: str = "stories.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def calculate_novel_stats(self, novel_id: int) -> Dict:
        """计算小说统计信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 统计章节数和总字数（使用 COALESCE 处理 NULL 值）
        cursor.execute("""
            SELECT 
                COUNT(*) as total_chapters,
                COALESCE(SUM(word_count), 0) as total_words,
                COALESCE(AVG(word_count), 0) as avg_words_per_chapter
            FROM chapters
            WHERE novel_id = ? AND is_deleted = 0
        """, (novel_id,))
        
        row = cursor.fetchone()
        if row:
            stats = dict(row)
            # 确保数值类型正确（SQLite 可能返回字符串）
            stats['total_chapters'] = int(stats.get('total_chapters', 0) or 0)
            stats['total_words'] = int(stats.get('total_words', 0) or 0)
            avg_words = stats.get('avg_words_per_chapter')
            if avg_words is not None:
                stats['avg_words_per_chapter'] = float(avg_words) if avg_words else 0.0
            else:
                stats['avg_words_per_chapter'] = 0.0
        else:
            stats = {
                'total_chapters': 0,
                'total_words': 0,
                'avg_words_per_chapter': 0.0
            }
        
        # 统计各状态章节数
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM chapters
            WHERE novel_id = ? AND is_deleted = 0
            GROUP BY status
        """, (novel_id,))
        
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        stats['status_counts'] = status_counts
        
        conn.close()
        return stats
    
    def update_novel_metadata(self, novel_id: int) -> bool:
        """更新小说元数据"""
        stats = self.calculate_novel_stats(novel_id)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查是否已存在元数据记录
        cursor.execute("SELECT id FROM novel_metadata WHERE novel_id = ?", (novel_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("""
                UPDATE novel_metadata
                SET total_chapters = ?, total_words = ?, last_updated = ?
                WHERE novel_id = ?
            """, (stats['total_chapters'], stats['total_words'] or 0, datetime.now(), novel_id))
        else:
            cursor.execute("""
                INSERT INTO novel_metadata (novel_id, total_chapters, total_words, last_updated)
                VALUES (?, ?, ?, ?)
            """, (novel_id, stats['total_chapters'], stats['total_words'] or 0, datetime.now()))
        
        conn.commit()
        conn.close()
        return True
    
    def get_writing_timeline(self, novel_id: int) -> List[Dict]:
        """获取写作时间线"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as chapters_created,
                SUM(word_count) as words_written
            FROM chapters
            WHERE novel_id = ? AND is_deleted = 0
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """, (novel_id,))
        
        timeline = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return timeline
    
    def get_word_count_chart(self, novel_id: int) -> Dict:
        """获取字数统计图表数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT chapter_number, chapter_title, word_count
            FROM chapters
            WHERE novel_id = ? AND is_deleted = 0
            ORDER BY chapter_number ASC
        """, (novel_id,))
        
        chapters = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            'chapters': [ch['chapter_number'] for ch in chapters],
            'titles': [ch['chapter_title'] for ch in chapters],
            'word_counts': [ch['word_count'] for ch in chapters]
        }


class OutlineManager:
    """大纲管理器 - 管理小说大纲及版本"""
    
    def __init__(self, db_path: str = "stories.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def save_outline(self, novel_id: int, content: str) -> int:
        """保存新版本大纲（自动停用旧版本）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. 获取当前最大版本号
        cursor.execute("SELECT MAX(version) FROM novel_outlines WHERE novel_id = ?", (novel_id,))
        result = cursor.fetchone()
        current_max_version = result[0] if result[0] is not None else 0
        new_version = current_max_version + 1
        
        # 2. 将所有旧版本设为非激活
        cursor.execute("UPDATE novel_outlines SET is_active = 0 WHERE novel_id = ?", (novel_id,))
        
        # 3. 插入新版本
        cursor.execute("""
            INSERT INTO novel_outlines (novel_id, version, content, is_active, created_at)
            VALUES (?, ?, ?, 1, ?)
        """, (novel_id, new_version, content, datetime.now()))
        
        outline_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return outline_id
    
    def get_latest_outline(self, novel_id: int) -> Optional[Dict]:
        """获取当前激活的大纲"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM novel_outlines 
            WHERE novel_id = ? AND is_active = 1
            ORDER BY version DESC
            LIMIT 1
        """, (novel_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_outline_history(self, novel_id: int) -> List[Dict]:
        """获取大纲历史版本列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM novel_outlines 
            WHERE novel_id = ?
            ORDER BY version DESC
        """, (novel_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def restore_outline_version(self, novel_id: int, version: int) -> bool:
        """恢复到指定版本的大纲"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查版本是否存在
        cursor.execute("SELECT id FROM novel_outlines WHERE novel_id = ? AND version = ?", (novel_id, version))
        if not cursor.fetchone():
            conn.close()
            return False
            
        # 更新激活状态
        cursor.execute("UPDATE novel_outlines SET is_active = 0 WHERE novel_id = ?", (novel_id,))
        cursor.execute("UPDATE novel_outlines SET is_active = 1 WHERE novel_id = ? AND version = ?", (novel_id, version))
        
        conn.commit()
        conn.close()
        return True
    
    # ==================== 按段管理的新方法 ====================
    
    def create_outline_segment(self, novel_id: int, start_chapter: int, end_chapter: int,
                               title: str = "", summary: str = "",
                               status: str = "active", priority: int = 0) -> int:
        """创建大纲段"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 自动计算 segment_order（取最大值+1）
        cursor.execute("SELECT MAX(segment_order) FROM outline_segments WHERE novel_id = ?", (novel_id,))
        result = cursor.fetchone()
        max_order = result[0] if result[0] is not None else 0
        segment_order = max_order + 1
        
        cursor.execute("""
            INSERT INTO outline_segments 
            (novel_id, segment_order, start_chapter, end_chapter, title, summary, status, priority, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (novel_id, segment_order, start_chapter, end_chapter, title, summary, status, priority, datetime.now()))
        
        segment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return segment_id
    
    def get_outline_segment(self, segment_id: int) -> Optional[Dict]:
        """获取单个大纲段"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM outline_segments WHERE id = ? AND is_deleted = 0
        """, (segment_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def list_outline_segments(self, novel_id: int, include_deleted: bool = False) -> List[Dict]:
        """列出所有大纲段（按 segment_order 排序）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        where_clause = "novel_id = ?"
        if not include_deleted:
            where_clause += " AND is_deleted = 0"
        
        cursor.execute(f"""
            SELECT * FROM outline_segments 
            WHERE {where_clause}
            ORDER BY segment_order ASC, start_chapter ASC
        """, (novel_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_outline_segment(self, segment_id: int, **kwargs) -> bool:
        """更新大纲段"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        allowed_fields = ['segment_order', 'start_chapter', 'end_chapter', 'title', 'summary', 'status', 'priority']
        updates = []
        params = []
        
        for field in allowed_fields:
            if field in kwargs:
                updates.append(f"{field} = ?")
                params.append(kwargs[field])
        
        if not updates:
            conn.close()
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(segment_id)
        
        query = f"UPDATE outline_segments SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_outline_segment(self, segment_id: int, soft: bool = True) -> bool:
        """删除大纲段（默认软删除）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if soft:
            cursor.execute("""
                UPDATE outline_segments SET is_deleted = 1, updated_at = ?
                WHERE id = ?
            """, (datetime.now(), segment_id))
        else:
            cursor.execute("DELETE FROM outline_segments WHERE id = ?", (segment_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_segments_by_chapter_range(self, novel_id: int, 
                                      start_chapter: int, end_chapter: int) -> List[Dict]:
        """根据章节范围查询大纲段（查询与指定范围有重叠的所有段）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM outline_segments 
            WHERE novel_id = ? 
              AND is_deleted = 0
              AND (
                  (start_chapter <= ? AND end_chapter >= ?)
                  OR (start_chapter >= ? AND start_chapter <= ?)
              )
            ORDER BY segment_order ASC, start_chapter ASC
        """, (novel_id, end_chapter, start_chapter, start_chapter, end_chapter))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_latest_outline_as_segments(self, novel_id: int) -> List[Dict]:
        """获取最新大纲作为段列表（兼容方法，优先从 outline_segments 读取）"""
        # 先尝试从 outline_segments 读取
        segments = self.list_outline_segments(novel_id)
        
        if segments:
            return segments
        
        # 如果没有，尝试从旧的 novel_outlines 转换
        old_outline = self.get_latest_outline(novel_id)
        if old_outline:
            try:
                outline_data = json.loads(old_outline['content'])
                return outline_data if isinstance(outline_data, list) else []
            except:
                return []
        
        return []
