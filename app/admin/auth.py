"""
管理后台认证中间件
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import Optional
import hashlib
import secrets
from datetime import datetime, timedelta

from app.core.config import settings

# 简单的内存 Session 存储（生产环境建议使用 Redis）
_sessions = {}

# Session 有效期（小时）
SESSION_EXPIRE_HOURS = 24


def generate_session_token() -> str:
    """生成随机 session token"""
    return secrets.token_urlsafe(32)


def create_session(password: str) -> Optional[str]:
    """
    创建 session

    Args:
        password: 用户输入的密码

    Returns:
        session_token 或 None（密码错误）
    """
    # 验证密码
    if password != settings.ADMIN_PASSWORD:
        return None

    # 生成 session token
    session_token = generate_session_token()

    # 存储 session（包含过期时间）
    _sessions[session_token] = {
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=SESSION_EXPIRE_HOURS),
        "authenticated": True
    }

    return session_token


def verify_session(session_token: Optional[str]) -> bool:
    """
    验证 session 是否有效

    Args:
        session_token: Session token

    Returns:
        是否已认证
    """
    if not session_token:
        return False

    session = _sessions.get(session_token)
    if not session:
        return False

    # 检查是否过期
    if datetime.now() > session["expires_at"]:
        # 删除过期 session
        del _sessions[session_token]
        return False

    return session.get("authenticated", False)


def delete_session(session_token: Optional[str]):
    """删除 session（登出）"""
    if session_token and session_token in _sessions:
        del _sessions[session_token]


def get_session_token_from_request(request: Request) -> Optional[str]:
    """从请求中获取 session token"""
    return request.cookies.get("admin_session")


async def require_auth(request: Request):
    """
    认证依赖项：要求用户已登录

    在路由中使用：
    @router.get("/admin", dependencies=[Depends(require_auth)])
    """
    session_token = get_session_token_from_request(request)

    if not verify_session(session_token):
        # 未认证，重定向到登录页
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="未登录",
            headers={"Location": "/admin/login"}
        )


def get_authenticated_user(request: Request) -> bool:
    """
    获取当前认证状态（用于模板）

    Returns:
        是否已认证
    """
    session_token = get_session_token_from_request(request)
    return verify_session(session_token)


def cleanup_expired_sessions():
    """清理过期的 session（定时任务调用）"""
    now = datetime.now()
    expired_tokens = [
        token for token, session in _sessions.items()
        if now > session["expires_at"]
    ]

    for token in expired_tokens:
        del _sessions[token]

    return len(expired_tokens)
