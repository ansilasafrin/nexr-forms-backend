from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.db.models import Post
from app.api.endpoints.common import PostCreate

router = APIRouter()

@router.post("/")
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    try:
        new_post = Post(title=post.title, content=post.content)
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except Exception as e:
        print(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail="Failed to create post")

@router.get("/")
def get_posts(db: Session = Depends(get_db)):
    return db.query(Post).all()
