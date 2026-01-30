import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "stories.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Check if 'novels' table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='novels'")
    if cursor.fetchone():
        print("Table 'novels' already exists. Migration might have been run.")
        conn.close()
        return
    
    print("Starting migration...")

    try:
        # 2. Create 'novels' table
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_novels_created_at ON novels(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_novels_source_id ON novels(source_story_id)")

        # 3. Migrate 'full_novel' from 'stories' to 'novels'
        cursor.execute("SELECT * FROM stories WHERE type = 'full_novel'")
        full_novels = cursor.fetchall()
        
        # Mapping: old_story_id -> new_novel_id
        id_map = {}

        for novel in full_novels:
            old_id = novel['id']
            
            # Find source_story_id from story_relations
            cursor.execute("SELECT parent_id FROM story_relations WHERE child_id = ?", (old_id,))
            relation = cursor.fetchone()
            source_id = relation['parent_id'] if relation else None

            # Insert into novels
            cursor.execute("""
                INSERT INTO novels (title, topic, content, metadata, source_story_id, created_at, updated_at, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                novel['title'], 
                novel['topic'], 
                novel['content'], 
                novel['metadata'], 
                source_id,
                novel['created_at'],
                novel['updated_at'],
                novel['is_deleted']
            ))
            new_id = cursor.lastrowid
            id_map[old_id] = new_id
            print(f"Migrated story {old_id} to novel {new_id}")

        # 4. Handle dependent tables: chapters, novel_versions, novel_metadata
        tables_to_migrate = ['chapters', 'novel_versions', 'novel_metadata']
        
        for table in tables_to_migrate:
            print(f"Migrating table {table}...")
            # Rename old table
            cursor.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
            
            if table == 'chapters':
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
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_chapters_novel_id ON chapters(novel_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_chapters_number ON chapters(chapter_number)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_chapters_novel_number ON chapters(novel_id, chapter_number)")

            elif table == 'novel_versions':
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
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_versions_novel_id ON novel_versions(novel_id)")

            elif table == 'novel_metadata':
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

            # Copy data
            cursor.execute(f"SELECT * FROM {table}_old")
            rows = cursor.fetchall()
            for row in rows:
                old_novel_id = row['novel_id']
                if old_novel_id in id_map:
                    new_novel_id = id_map[old_novel_id]
                    data = dict(row)
                    data['novel_id'] = new_novel_id
                    
                    columns = ', '.join(data.keys())
                    placeholders = ', '.join(['?'] * len(data))
                    values = list(data.values())
                    
                    cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
                else:
                    print(f"Skipping {table} record {row['id']} for unknown novel {old_novel_id}")

        # 5. Clean up
        for old_id in id_map.keys():
            cursor.execute("DELETE FROM stories WHERE id = ?", (old_id,))
            cursor.execute("DELETE FROM story_relations WHERE child_id = ?", (old_id,))
        
        for table in tables_to_migrate:
            cursor.execute(f"DROP TABLE {table}_old")

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        # Consider restoring tables if needed, but for now we rely on rollback
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
