from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError, OperationalError

from database import get_session
from logger_config import logger
from .models import User
from .schemas import UserCreate, UserResponse, SchoolsResponse, UserRegister, UserLogin


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


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(data: UserRegister, session: Session = Depends(get_session)):
    """首次登记：填写一次基本信息并绑定学号，之后凭学号即可登录"""
    student_id = data.student_id.strip()
    if not student_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请填写学号")

    try:
        if session.exec(select(User).where(User.student_id == student_id)).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该学号已登记，请直接用学号登录")

        # 同名同校同班的历史用户直接绑定学号，避免重复建档、丢失既有成绩
        existing = session.exec(
            select(User).where(
                User.name == data.name,
                User.school == data.school,
                User.grade == data.grade,
                User.class_number == data.class_number,
            )
        ).first()

        if existing and not existing.student_id:
            existing.student_id = student_id
            if data.birth_date and not existing.birth_date:
                existing.birth_date = data.birth_date
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

        user = User(
            name=data.name,
            school=data.school,
            grade=data.grade,
            class_number=data.class_number,
            birth_date=data.birth_date,
            student_id=student_id,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except HTTPException:
        raise
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该学号已登记，请直接用学号登录")
    except Exception:
        session.rollback()
        logger.exception("学号登记失败")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="登记失败，请稍后重试"
        )


@router.post("/login", response_model=UserResponse)
async def login_user(data: UserLogin, session: Session = Depends(get_session)):
    """凭学号 + 姓名登录"""
    try:
        user = session.exec(
            select(User).where(
                User.student_id == data.student_id.strip(),
                User.name == data.name.strip(),
            )
        ).first()
    except OperationalError:
        session.rollback()
        logger.exception("登录时数据库连接异常")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="数据库暂时不可用，请稍后重试"
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="学号与姓名不匹配，或该学号尚未登记"
        )

    # 记录本次测验序号与开始时间，供后台导出统计
    try:
        if data.test_round:
            user.test_round = data.test_round
        user.last_login_at = datetime.now()
        session.add(user)
        session.commit()
        session.refresh(user)
    except Exception:
        session.rollback()
        # 记录失败不应挡住学生开始测验
        logger.exception("记录登录信息失败")

    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: Session = Depends(get_session)):
    """获取用户信息"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user
