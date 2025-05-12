from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Dict, Any
from datetime import datetime, timedelta

from database import get_session
from .models import User
from .schemas import UserCreate, UserResponse, SchoolsResponse


router = APIRouter(tags=["用户管理"])


@router.get("/schools/recent", response_model=SchoolsResponse)
async def get_recent_schools(session: Session = Depends(get_session)):
    """获取最近一天参与测试的学校列表"""
    try:
        schools = session.exec(select(User.school)).all()
        return {"schools": schools}
    except Exception as e:
        raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取最近学校失败: {str(e)}"
        )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, session: Session = Depends(get_session)):
    """创建新用户"""
    try:
        # 查找已存在的用户
        query = select(User).where(
            User.name == user_data.name,
            User.school == user_data.school,
            User.grade == user_data.grade,
            User.class_number == user_data.class_number,
        )
        existing_user = session.exec(query).first()

        # 如果已存在，则直接返回
        if existing_user:
            return existing_user

        # 创建新用户
        new_user = User(
            name=user_data.name,
            school=user_data.school,
            grade=user_data.grade,
            class_number=user_data.class_number,
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建用户失败: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: Session = Depends(get_session)):
    """获取用户信息"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user
