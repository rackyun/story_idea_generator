import sqlite3
import os

def migrate():
    db_path = "stories.db"
    
    if not os.path.exists(db_path):
        print("Database not found, skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='novel_outlines'")
        if cursor.fetchone():
            print("Table 'novel_outlines' already exists.")
        else:
            print("Creating 'novel_outlines' table...")
            cursor.execute("""
                CREATE TABLE novel_outlines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    novel_id INTEGER NOT NULL,
                    version INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 0,
                    FOREIGN KEY (novel_id) REFERENCES novels(id)
                )
            """)
            cursor.execute("CREATE INDEX idx_outlines_novel_id ON novel_outlines(novel_id)")
            print("Table created successfully.")

    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.commit()
        conn.close()

if __name__ == "__main__":
    migrate()
