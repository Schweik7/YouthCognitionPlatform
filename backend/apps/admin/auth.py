"""后台管理员登录与鉴权

管理员账号来自配置（ADMIN_USERNAME / ADMIN_PASSWORD，可用环境变量覆盖）。
登录成功后签发一个 HMAC 签名的令牌，后续所有后台接口都要带上它。
令牌可以放在 Authorization: Bearer <token> 头里，也可以用 ?token= 传，
因为导出下载是浏览器直接打开链接，带不了自定义请求头。
"""
import base64
import hashlib
import hmac
import json
import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel

from config import settings

auth_router = APIRouter(tags=["后台管理"])


class AdminLogin(BaseModel):
    username: str
    password: str


def _sign(payload: bytes) -> str:
    return base64.urlsafe_b64encode(
        hmac.new(settings.SECRET_KEY.encode(), payload, hashlib.sha256).digest()
    ).decode().rstrip("=")


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def create_token(username: str) -> str:
    exp = int(time.time()) + settings.ADMIN_TOKEN_EXPIRE_MINUTES * 60
    payload = json.dumps({"sub": username, "exp": exp}, separators=(",", ":")).encode()
    return f"{_b64(payload)}.{_sign(payload)}"


def _verify(token: str) -> Optional[str]:
    """校验令牌，通过则返回用户名，否则返回 None"""
    try:
        body, sig = token.split(".", 1)
        payload = _unb64(body)
    except Exception:
        return None
    if not hmac.compare_digest(sig, _sign(payload)):
        return None
    try:
        data = json.loads(payload)
    except Exception:
        return None
    if int(data.get("exp", 0)) < time.time():
        return None
    return data.get("sub")


async def require_admin(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None, description="令牌（供下载链接使用）"),
) -> str:
    raw = token
    if not raw and authorization and authorization.lower().startswith("bearer "):
        raw = authorization[7:]
    username = _verify(raw) if raw else None
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录后台，或登录已过期",
        )
    return username


@auth_router.post("/login")
async def admin_login(data: AdminLogin):
    """管理员登录，返回访问令牌"""
    ok = hmac.compare_digest(data.username.strip(), settings.ADMIN_USERNAME) and hmac.compare_digest(
        data.password, settings.ADMIN_PASSWORD
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    return {
        "success": True,
        "username": settings.ADMIN_USERNAME,
        "token": create_token(settings.ADMIN_USERNAME),
        "expires_in": settings.ADMIN_TOKEN_EXPIRE_MINUTES * 60,
    }


@auth_router.get("/me")
async def admin_me(username: str = Depends(require_admin)):
    """校验当前令牌是否仍然有效"""
    return {"success": True, "username": username}
