import sqlite3
import sys

def update_article(db_path, url, has_comments=True, comment_count=10):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update the article
    cursor.execute(
        "UPDATE articles SET has_comments = ?, comment_count = ? WHERE url LIKE ?",
        (1 if has_comments else 0, comment_count, f"%{url}%")
    )
    
    # Check if the update was successful
    if cursor.rowcount > 0:
        print(f"Updated {cursor.rowcount} article(s)")
    else:
        print(f"No articles found with URL containing: {url}")
    
    # Commit the changes
    conn.commit()
    
    # Verify the update
    cursor.execute("SELECT id, identifier, url, title, has_comments, comment_count FROM articles WHERE url LIKE ?", (f"%{url}%",))
    article = cursor.fetchone()
    
    if article:
        print(f"Article after update:")
        print(f"ID: {article[0]}, Identifier: {article[1]}, URL: {article[2]}, Title: {article[3]}, Has Comments: {article[4]}, Comment Count: {article[5]}")
    
    conn.close()

if __name__ == "__main__":
    db_path = "osint_comments.db"
    url = "stoltenberg-frykter-trippelskvis-for-norge"
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    update_article(db_path, url)
