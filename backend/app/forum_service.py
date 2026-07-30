from sqlalchemy.orm import Session

from app.models import ForumComment, ForumLike, ForumPost, ForumSave
from app.schemas import ForumCommentRead, ForumPostRead


def serialize_forum_post(db: Session, post: ForumPost, current_user_id: int | None = None) -> ForumPostRead:
    return ForumPostRead(
        id=post.id,
        user_id=post.user_id,
        author_name=post.user.name if post.user else None,
        category_id=post.category_id,
        category_name=post.category.name if post.category else None,
        title=post.title,
        content=post.content,
        post_type=post.post_type,
        status=post.status,
        created_at=post.created_at,
        like_count=db.query(ForumLike).filter(ForumLike.post_id == post.id).count(),
        comment_count=db.query(ForumComment).filter(ForumComment.post_id == post.id).count(),
        save_count=db.query(ForumSave).filter(ForumSave.post_id == post.id).count(),
        is_liked=bool(
            current_user_id
            and db.query(ForumLike).filter(ForumLike.post_id == post.id, ForumLike.user_id == current_user_id).first()
        ),
        is_saved=bool(
            current_user_id
            and db.query(ForumSave).filter(ForumSave.post_id == post.id, ForumSave.user_id == current_user_id).first()
        ),
    )


def serialize_forum_comment(comment: ForumComment) -> ForumCommentRead:
    return ForumCommentRead(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        author_name=comment.user.name if comment.user else None,
        content=comment.content,
        created_at=comment.created_at,
    )
