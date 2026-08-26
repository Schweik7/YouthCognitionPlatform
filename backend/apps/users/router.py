from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError, OperationalError

from database import get_session
from logger_config import logger
from .models import User
from .schemas import UserCreate, UserResponse, SchoolsResponse


router = APIRouter(tags=["用户管理"])


@router.get("/schools/recent", response_model=SchoolsResponse)
async def get_recent_schools(session: Session = Depends(get_session)):
    """获取最近一天参与测试的学校列表"""
    try:
        schools = session.exec(select(User.school).distinct()).all()
        return {"schools": [s for s in schools if s]}
    except Exception as e:
        logger.exception("获取学校列表失败")
        # 学校列表只用于输入联想，失败时返回空列表，避免阻塞用户填写信息
        return {"schools": []}


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, session: Session = Depends(get_session)):
    """创建新用户（同名同班级则复用已有用户）"""

    def find_existing():
        query = select(User).where(
            User.name == user_data.name,
            User.school == user_data.school,
            User.grade == user_data.grade,
            User.class_number == user_data.class_number,
        )
        return session.exec(query).first()

    # 数据库瞬时抖动（连接被回收/网络闪断）时重试一次，避免让学生看到“创建用户失败”
    for attempt in range(2):
        try:
            # 查找已存在的用户（不包含birth_date，因为可能后续更新）
            existing_user = find_existing()

            # 如果已存在，更新birth_date（如果提供）
            if existing_user:
                if user_data.birth_date and not existing_user.birth_date:
                    existing_user.birth_date = user_data.birth_date
                    session.add(existing_user)
                    session.commit()
                    session.refresh(existing_user)
                return existing_user

            # 创建新用户
            new_user = User(
                name=user_data.name,
                school=user_data.school,
                grade=user_data.grade,
                class_number=user_data.class_number,
                birth_date=user_data.birth_date,
            )

            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            return new_user
        except IntegrityError:
            # 并发提交造成的重复写入：回滚后取已存在的那条记录
            session.rollback()
            existing_user = find_existing()
            if existing_user:
                return existing_user
            logger.exception("创建用户时发生唯一性冲突且未找到已有记录")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建用户失败，请重试"
            )
        except OperationalError:
            session.rollback()
            logger.warning("创建用户时数据库连接异常，第 %s 次尝试", attempt + 1, exc_info=True)
            if attempt == 1:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="数据库暂时不可用，请稍后重试"
                )
        except Exception as e:
            session.rollback()
            logger.exception("创建用户失败")
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
