import sqlite3
import sys

def check_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check articles with comments
    cursor.execute("SELECT COUNT(*) FROM articles WHERE has_comments = 1")
    articles_with_comments = cursor.fetchone()[0]
    print(f"Articles with comments: {articles_with_comments}")
    
    # Check articles with comments not gathered
    cursor.execute("SELECT COUNT(*) FROM articles WHERE has_comments = 1 AND comments_gathered = 0")
    articles_with_comments_not_gathered = cursor.fetchone()[0]
    print(f"Articles with comments not gathered: {articles_with_comments_not_gathered}")
    
    # List articles with comments
    cursor.execute("SELECT id, identifier, url, title, has_comments, comment_count FROM articles WHERE has_comments = 1")
    articles = cursor.fetchall()
    print("\nArticles with comments:")
    for article in articles:
        print(f"ID: {article[0]}, Identifier: {article[1]}, URL: {article[2]}, Title: {article[3]}, Has Comments: {article[4]}, Comment Count: {article[5]}")
    
    conn.close()

if __name__ == "__main__":
    db_path = "osint_comments.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    check_database(db_path)
