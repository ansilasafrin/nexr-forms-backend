from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.api.deps import get_db
from app.db.models import Post
from app.api.endpoints.common import PostCreate, PostResponse

router = APIRouter()

@router.post("/", response_model=PostResponse, tags=["posts"], summary="Create a post")
async def create_post(post: PostCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_post = Post(title=post.title, content=post.content)
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)
        return new_post
    except Exception as e:
        print(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail="Failed to create post")

@router.get("/", response_model=List[PostResponse], tags=["posts"], summary="List all posts")
async def get_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post))
    return result.scalars().all()
