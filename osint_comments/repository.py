# repository.py
from .models import Article, User, Comment
from datetime import datetime

class Repository:
    def __init__(self, session):
        self.session = session

    def get_or_create_article(self, identifier: str) -> Article:
        article = self.session.query(Article).filter_by(identifier=identifier).first()
        if not article:
            article = Article(identifier=identifier)
            self.session.add(article)
            self.session.commit()
        return article

    def get_or_create_user(self, external_id: int, name: str, display_name: str) -> User:
        user = self.session.query(User).filter_by(external_id=external_id).first()
        if not user:
            user = User(external_id=external_id, name=name, display_name=display_name)
            self.session.add(user)
            self.session.commit()
        return user

    def add_comment(self, comment_data: dict, article: Article, user: User) -> tuple[Comment, bool]:
        # Check if the comment already exists.
        existing = self.session.query(Comment).filter_by(id=comment_data['id']).first()
        if existing:
            return existing, False

        # Convert ISO timestamps to Python datetime objects.
        created_at = datetime.fromisoformat(comment_data['createdAt'].replace("Z", "+00:00"))
        updated_at = None
        if comment_data.get('updatedAt'):
            updated_at = datetime.fromisoformat(comment_data['updatedAt'].replace("Z", "+00:00"))

        comment = Comment(
            id=comment_data['id'],
            message=comment_data['message'],
            created_at=created_at,
            updated_at=updated_at,
            score=comment_data.get('score'),
            article=article,
            user=user
        )
        self.session.add(comment)
        self.session.commit()
        return comment, True
