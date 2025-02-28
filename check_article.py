import sqlite3
import sys

def check_article(db_path, url):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the article exists
    cursor.execute("SELECT id, identifier, url, title, has_comments, comment_count FROM articles WHERE url LIKE ?", (f"%{url}%",))
    article = cursor.fetchone()
    
    if article:
        print(f"Article found:")
        print(f"ID: {article[0]}, Identifier: {article[1]}, URL: {article[2]}, Title: {article[3]}, Has Comments: {article[4]}, Comment Count: {article[5]}")
    else:
        print(f"Article not found with URL containing: {url}")
    
    conn.close()

if __name__ == "__main__":
    db_path = "osint_comments.db"
    url = "stoltenberg-frykter-trippelskvis-for-norge"
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    check_article(db_path, url)
