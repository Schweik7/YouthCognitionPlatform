from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session
from datetime import datetime
import uuid

from config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,  # type: ignore
    # echo=settings.DEBUG,
    echo=False,
    pool_pre_ping=True,
)


# 基础模型类
class BaseModel(SQLModel):
    """所有模型的基类"""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now, index=True)

    class Config:
        arbitrary_types_allowed = True


# 会话上下文管理器
def get_session():
    with Session(engine) as session:
        yield session


# 创建所有数据库表
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# 开发模式：重建数据库表
def recreate_db_and_tables():
    """开发模式下重建数据库表（清空所有数据）"""
    from logger_config import logger
    
    logger.warning("开发模式：正在重建数据库表，所有数据将被清空！")
    
    # 禁用外键检查，删除所有表，然后重新启用
    with engine.connect() as conn:
        from sqlalchemy import text
        
        # 禁用外键检查
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        logger.info("已禁用外键检查")
        
        # 删除所有表
        SQLModel.metadata.drop_all(conn)
        logger.info("已删除所有表")
        
        # 重新启用外键检查
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        logger.info("已重新启用外键检查")
        
        # 提交事务
        conn.commit()
    
    # 重新创建所有表
    SQLModel.metadata.create_all(engine)
    logger.info("已重新创建所有表")


# 开发模式：重建特定表
def recreate_specific_tables(table_names: list):
    """开发模式下重建特定表"""
    from logger_config import logger
    
    logger.warning(f"开发模式：正在重建表 {table_names}，相关数据将被清空！")
    
    # 获取要重建的表对象
    tables_to_drop = []
    for table_name in table_names:
        for table in SQLModel.metadata.tables.values():
            if table.name == table_name:
                tables_to_drop.append(table)
                break
    
    if tables_to_drop:
        # 删除指定表
        SQLModel.metadata.drop_all(engine, tables=tables_to_drop)
        logger.info(f"已删除表: {[t.name for t in tables_to_drop]}")
        
        # 重新创建指定表
        SQLModel.metadata.create_all(engine, tables=tables_to_drop)
        logger.info(f"已重新创建表: {[t.name for t in tables_to_drop]}")
    else:
        logger.warning(f"未找到要重建的表: {table_names}")


# 初始化开发数据
def init_dev_data():
    """初始化开发环境的测试数据"""
    from apps.users.models import User
    from logger_config import logger
    
    with Session(engine) as session:
        # 检查是否已有用户数据
        existing_user = session.query(User).first()
        if not existing_user:
            # 创建测试用户
            test_user = User(
                name="测试用户",
                school="测试小学",
                grade=2,
                class_number=1
            )
            session.add(test_user)
            session.commit()
            logger.info(f"创建测试用户: {test_user.name}, ID: {test_user.id}")


if __name__ == "__main__":
    # 手动运行此文件时创建数据库和表
    create_db_and_tables()
    print("数据库表已创建")
