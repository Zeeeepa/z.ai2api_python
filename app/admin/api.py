"""
管理后台 API 接口
用于 htmx 调用的 HTML 片段返回
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, Response
from datetime import datetime
from app.utils.logger import logger
import os

router = APIRouter(prefix="/admin/api", tags=["admin-api"])
templates = Jinja2Templates(directory="app/templates")


# ==================== 认证 API ====================

@router.post("/login")
async def login(request: Request):
    """管理后台登录"""
    from app.admin.auth import create_session

    try:
        data = await request.json()
        password = data.get("password", "")

        # 创建 session
        session_token = create_session(password)

        if session_token:
            # 登录成功，设置 cookie
            response = JSONResponse({
                "success": True,
                "message": "登录成功"
            })
            response.set_cookie(
                key="admin_session",
                value=session_token,
                httponly=True,
                max_age=86400,  # 24小时
                samesite="lax"
            )
            logger.info("✅ 管理后台登录成功")
            return response
        else:
            # 密码错误
            logger.warning("❌ 管理后台登录失败：密码错误")
            return JSONResponse({
                "success": False,
                "message": "密码错误"
            }, status_code=401)

    except Exception as e:
        logger.error(f"❌ 登录异常: {e}")
        return JSONResponse({
            "success": False,
            "message": "登录失败"
        }, status_code=500)


@router.post("/logout")
async def logout(request: Request):
    """管理后台登出"""
    from app.admin.auth import delete_session, get_session_token_from_request

    session_token = get_session_token_from_request(request)
    delete_session(session_token)

    # 清除 cookie
    response = JSONResponse({
        "success": True,
        "message": "已登出"
    })
    response.delete_cookie("admin_session")
    logger.info("✅ 管理后台已登出")
    return response


async def reload_settings():
    """热重载配置（重新加载环境变量并更新 settings 对象）"""
    from app.core.config import settings
    from app.utils.logger import setup_logger
    from dotenv import load_dotenv

    # 重新加载 .env 文件
    load_dotenv(override=True)

    # 重新创建 Settings 对象并更新全局配置
    new_settings = type(settings)()

    # 更新全局 settings 的所有属性
    for field_name in new_settings.model_fields.keys():
        setattr(settings, field_name, getattr(new_settings, field_name))

    # 重新初始化 logger（使用新的 DEBUG_LOGGING 配置）
    setup_logger(log_dir="logs", debug_mode=settings.DEBUG_LOGGING)

    logger.info(f"🔄 配置已热重载 (DEBUG_LOGGING={settings.DEBUG_LOGGING})")


@router.get("/token-pool", response_class=HTMLResponse)
async def get_token_pool_status(request: Request):
    """获取 Token 池状态（HTML 片段）"""
    from app.utils.token_pool import get_token_pool

    token_pool = get_token_pool()

    if not token_pool:
        # Token 池未初始化
        context = {
            "request": request,
            "tokens": [],
        }
        return templates.TemplateResponse("components/token_pool.html", context)

    # 获取 token 状态统计
    pool_status = token_pool.get_pool_status()
    tokens_info = []

    for idx, token_info in enumerate(pool_status.get("tokens", []), 1):
        is_available = token_info.get("is_available", False)
        is_healthy = token_info.get("is_healthy", False)

        # 确定状态和颜色
        if is_healthy:
            status = "健康"
            status_color = "bg-green-100 text-green-800"
        elif is_available:
            status = "可用"
            status_color = "bg-yellow-100 text-yellow-800"
        else:
            status = "失败"
            status_color = "bg-red-100 text-red-800"

        # 格式化最后使用时间
        last_success = token_info.get("last_success_time", 0)
        if last_success > 0:
            from datetime import datetime
            last_used = datetime.fromtimestamp(last_success).strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_used = "从未使用"

        tokens_info.append({
            "index": idx,
            "key": token_info.get("token", "")[:20] + "...",
            "status": status,
            "status_color": status_color,
            "last_used": last_used,
            "failure_count": token_info.get("failure_count", 0),
            "success_rate": token_info.get("success_rate", "0%"),
            "token_type": token_info.get("token_type", "unknown"),
        })

    context = {
        "request": request,
        "tokens": tokens_info,
    }

    return templates.TemplateResponse("components/token_pool.html", context)


@router.get("/recent-logs", response_class=HTMLResponse)
async def get_recent_logs(request: Request):
    """获取最近的请求日志（HTML 片段）"""
    # TODO: 从数据库或日志文件读取
    logs = [
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "endpoint": "/v1/chat/completions",
            "model": "gpt-4o",
            "status": 200,
            "duration": "1.23s",
            "provider": "zai",
        }
    ]

    context = {
        "request": request,
        "logs": logs,
    }

    return templates.TemplateResponse("components/recent_logs.html", context)


@router.post("/config/save")
async def save_config(request: Request):
    """保存配置到 .env 文件并热重载"""
    try:
        form_data = await request.form()

        # 构建 .env 内容
        env_lines = [
            "# Z.AI2API 配置文件",
            "",
            "# ========== 服务器配置 ==========",
            f"SERVICE_NAME={form_data.get('service_name', 'Z.AI2API')}",
            f"LISTEN_PORT={form_data.get('listen_port', '8080')}",
            f"DEBUG_LOGGING={'true' if 'debug_logging' in form_data else 'false'}",
            "",
            "# ========== 认证配置 ==========",
            f"AUTH_TOKEN={form_data.get('auth_token', 'sk-your-api-key')}",
            f"SKIP_AUTH_TOKEN={'true' if 'skip_auth_token' in form_data else 'false'}",
            f"ANONYMOUS_MODE={'true' if 'anonymous_mode' in form_data else 'false'}",
            "",
            "# ========== 功能配置 ==========",
            f"TOOL_SUPPORT={'true' if 'tool_support' in form_data else 'false'}",
            f"SCAN_LIMIT={form_data.get('scan_limit', '200000')}",
            "",
            "# ========== Token 池配置 ==========",
            f"TOKEN_FAILURE_THRESHOLD={form_data.get('token_failure_threshold', '3')}",
            f"TOKEN_RECOVERY_TIMEOUT={form_data.get('token_recovery_timeout', '1800')}",
            "",
            "# ========== 提供商配置 ==========",
            f"DEFAULT_PROVIDER={form_data.get('default_provider', 'zai')}",
        ]

        # LongCat Token（可选）
        longcat_token = form_data.get('longcat_token', '').strip()
        if longcat_token:
            env_lines.append(f"LONGCAT_TOKEN={longcat_token}")

        # 写入 .env 文件
        with open(".env", "w", encoding="utf-8") as f:
            f.write("\n".join(env_lines))

        logger.info("✅ 配置文件已保存")

        # 热重载配置
        await reload_settings()

        return HTMLResponse("""
        <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
            <strong class="font-bold">成功！</strong>
            <span class="block sm:inline">配置已保存并重载成功</span>
        </div>
        """)

    except Exception as e:
        logger.error(f"❌ 配置保存失败: {str(e)}")
        return HTMLResponse(f"""
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
            <strong class="font-bold">错误！</strong>
            <span class="block sm:inline">保存失败: {str(e)}</span>
        </div>
        """)


@router.get("/env-preview")
async def get_env_preview():
    """获取 .env 文件预览"""
    try:
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(f"<pre>{content}</pre>")
    except FileNotFoundError:
        return HTMLResponse("<pre># .env 文件不存在</pre>")
    except Exception as e:
        return HTMLResponse(f"<pre># 读取失败: {str(e)}</pre>")


@router.get("/provider-status", response_class=HTMLResponse)
async def get_provider_status(request: Request):
    """获取提供商状态详情（HTML 片段）"""
    from app.services.token_dao import get_token_dao

    dao = get_token_dao()

    # 获取所有提供商的统计信息
    providers = ["zai", "k2think", "longcat"]
    provider_stats_list = []

    for provider in providers:
        stats = await dao.get_provider_stats(provider)
        tokens = await dao.get_tokens_by_provider(provider, enabled_only=False)

        # 计算成功率
        total_requests = stats.get("total_requests", 0) or 0
        successful_requests = stats.get("successful_requests", 0) or 0
        failed_requests = stats.get("failed_requests", 0) or 0

        if total_requests > 0:
            success_rate = f"{(successful_requests / total_requests * 100):.1f}%"
        else:
            success_rate = "N/A"

        # Token 类型统计
        user_tokens = sum(1 for t in tokens if t.get("token_type") == "user")
        guest_tokens = sum(1 for t in tokens if t.get("token_type") == "guest")
        unknown_tokens = sum(1 for t in tokens if t.get("token_type") == "unknown")

        provider_stats_list.append({
            "name": provider,  # 小写名称（用于 URL 参数）
            "name_upper": provider.upper(),  # 大写名称（用于显示）
            "display_name": {
                "zai": "Z.AI",
                "k2think": "K2Think",
                "longcat": "LongCat"
            }.get(provider, provider.upper()),
            "total_tokens": stats.get("total_tokens", 0) or 0,
            "enabled_tokens": stats.get("enabled_tokens", 0) or 0,
            "user_tokens": user_tokens,
            "guest_tokens": guest_tokens,
            "unknown_tokens": unknown_tokens,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": success_rate,
        })

    context = {
        "request": request,
        "providers": provider_stats_list,
    }

    return templates.TemplateResponse("components/provider_status.html", context)


@router.get("/live-logs", response_class=HTMLResponse)
async def get_live_logs():
    """获取实时日志（最新 50 行）"""
    import os
    from datetime import datetime

    logs = []

    # 尝试读取日志文件
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')], reverse=True)
        if log_files:
            log_file = os.path.join(log_dir, log_files[0])
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    # 读取最后 50 行
                    lines = f.readlines()[-50:]
                    logs = lines
            except Exception as e:
                logs = [f"# [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 读取日志失败: {str(e)}"]

    if not logs:
        logs = [f"# [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 暂无日志数据"]

    html = ""
    for log in logs:
        log_line = log.strip()
        if not log_line:
            continue

        # 根据日志级别设置颜色和样式
        if "ERROR" in log_line or "CRITICAL" in log_line:
            color_class = "text-red-400 font-semibold"
            icon = "❌"
        elif "WARNING" in log_line or "WARN" in log_line:
            color_class = "text-yellow-400"
            icon = "⚠️"
        elif "SUCCESS" in log_line or "✅" in log_line:
            color_class = "text-green-400"
            icon = "✅"
        elif "INFO" in log_line:
            color_class = "text-blue-400"
            icon = "ℹ️"
        elif "DEBUG" in log_line:
            color_class = "text-gray-400 text-xs"
            icon = "🔍"
        else:
            color_class = "text-gray-300"
            icon = "•"

        # 转义 HTML 特殊字符
        log_escaped = log_line.replace('<', '&lt;').replace('>', '&gt;')

        html += f'<div class="{color_class} py-0.5 hover:bg-gray-800 px-2 rounded transition-colors">{icon} {log_escaped}</div>'

    return HTMLResponse(html)


# ==================== Token 管理 API ====================

@router.get("/tokens/list", response_class=HTMLResponse)
async def get_tokens_list(request: Request, provider: str = "zai"):
    """获取 Token 列表（HTML 片段）"""
    from app.services.token_dao import get_token_dao

    dao = get_token_dao()
    tokens = await dao.get_tokens_by_provider(provider, enabled_only=False)

    context = {
        "request": request,
        "tokens": tokens,
        "provider": provider
    }

    return templates.TemplateResponse("components/token_list.html", context)


@router.post("/tokens/add")
async def add_tokens(request: Request):
    """添加 Token"""
    from app.services.token_dao import get_token_dao
    from app.utils.token_pool import get_token_pool

    form_data = await request.form()
    provider = form_data.get("provider", "zai")
    single_token = form_data.get("single_token", "").strip()
    bulk_tokens = form_data.get("bulk_tokens", "").strip()

    dao = get_token_dao()
    added_count = 0
    failed_count = 0

    # 添加单个 Token（带验证）
    if single_token:
        token_id = await dao.add_token(provider, single_token, validate=True)
        if token_id:
            added_count += 1
        else:
            failed_count += 1

    # 批量添加 Token（带验证）
    if bulk_tokens:
        # 支持换行和逗号分隔
        tokens = []
        for line in bulk_tokens.split('\n'):
            line = line.strip()
            if ',' in line:
                tokens.extend([t.strip() for t in line.split(',') if t.strip()])
            elif line:
                tokens.append(line)

        success, failed = await dao.bulk_add_tokens(provider, tokens, validate=True)
        added_count += success
        failed_count += failed

    # 同步 Token 池状态（如果有新增成功的 Token）
    if added_count > 0:
        pool = get_token_pool()
        if pool:
            await pool.sync_from_database(provider)
            logger.info(f"✅ Token 池已同步，新增 {added_count} 个 Token ({provider})")

    # 生成响应
    if added_count > 0 and failed_count == 0:
        return HTMLResponse(f"""
        <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
            <strong class="font-bold">成功！</strong>
            <span class="block sm:inline">已添加 {added_count} 个有效 Token</span>
        </div>
        """)
    elif added_count > 0 and failed_count > 0:
        return HTMLResponse(f"""
        <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative" role="alert">
            <strong class="font-bold">部分成功！</strong>
            <span class="block sm:inline">已添加 {added_count} 个 Token，{failed_count} 个失败（可能是重复、无效或匿名 Token）</span>
        </div>
        """)
    else:
        return HTMLResponse("""
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
            <strong class="font-bold">失败！</strong>
            <span class="block sm:inline">所有 Token 添加失败（可能是重复、无效或匿名 Token）</span>
        </div>
        """)


@router.post("/tokens/toggle/{token_id}")
async def toggle_token(token_id: int, enabled: bool):
    """切换 Token 启用状态"""
    from app.services.token_dao import get_token_dao
    from app.utils.token_pool import get_token_pool

    dao = get_token_dao()
    await dao.update_token_status(token_id, enabled)

    # 同步 Token 池状态
    pool = get_token_pool()
    if pool:
        # 获取 Token 的提供商信息
        async with dao.get_connection() as conn:
            cursor = await conn.execute("SELECT provider FROM tokens WHERE id = ?", (token_id,))
            row = await cursor.fetchone()
            if row:
                provider = row[0]
                await pool.sync_from_database(provider)
                logger.info(f"✅ Token 池已同步 ({provider})")

    # 根据状态返回不同样式的按钮
    if enabled:
        button_class = "bg-green-100 text-green-800 hover:bg-green-200"
        indicator_class = "bg-green-500"
        label = "已启用"
        next_state = "false"
    else:
        button_class = "bg-red-100 text-red-800 hover:bg-red-200"
        indicator_class = "bg-red-500"
        label = "已禁用"
        next_state = "true"

    return HTMLResponse(f"""
    <button hx-post="/admin/api/tokens/toggle/{token_id}?enabled={next_state}"
            hx-swap="outerHTML"
            class="inline-flex items-center px-2.5 py-0.5 text-xs font-semibold rounded-full transition-colors {button_class}">
        <span class="h-2 w-2 rounded-full mr-1.5 {indicator_class}"></span>
        {label}
    </button>
    """)


@router.delete("/tokens/delete/{token_id}")
async def delete_token(token_id: int):
    """删除 Token"""
    from app.services.token_dao import get_token_dao
    from app.utils.token_pool import get_token_pool

    dao = get_token_dao()

    # 获取 Token 信息以确定提供商
    async with dao.get_connection() as conn:
        cursor = await conn.execute("SELECT provider FROM tokens WHERE id = ?", (token_id,))
        row = await cursor.fetchone()
        provider = row[0] if row else "zai"

    await dao.delete_token(token_id)

    # 同步 Token 池状态
    pool = get_token_pool()
    if pool:
        await pool.sync_from_database(provider)
        logger.info(f"✅ Token 池已同步 ({provider})")

    return HTMLResponse("")  # 返回空内容，让 htmx 移除元素


@router.get("/tokens/stats", response_class=HTMLResponse)
async def get_tokens_stats(request: Request, provider: str = "zai"):
    """获取 Token 统计信息（HTML 片段）"""
    from app.services.token_dao import get_token_dao

    dao = get_token_dao()

    # 获取提供商统计
    stats = await dao.get_provider_stats(provider)

    # 获取所有 Token 进行类型统计
    tokens = await dao.get_tokens_by_provider(provider, enabled_only=False)

    user_tokens = sum(1 for t in tokens if t.get("token_type") == "user")
    guest_tokens = sum(1 for t in tokens if t.get("token_type") == "guest")
    unknown_tokens = sum(1 for t in tokens if t.get("token_type") == "unknown")

    stats_data = {
        "total_tokens": stats.get("total_tokens", 0) or 0,
        "enabled_tokens": stats.get("enabled_tokens", 0) or 0,
        "user_tokens": user_tokens,
        "guest_tokens": guest_tokens,
        "unknown_tokens": unknown_tokens,
        "total_requests": stats.get("total_requests", 0) or 0,
        "successful_requests": stats.get("successful_requests", 0) or 0,
        "failed_requests": stats.get("failed_requests", 0) or 0,
    }

    context = {
        "request": request,
        "stats": stats_data,
        "provider": provider
    }

    return templates.TemplateResponse("components/token_stats.html", context)


@router.post("/tokens/validate")
async def validate_tokens(request: Request):
    """批量验证 Token"""
    from app.services.token_dao import get_token_dao

    form_data = await request.form()
    provider = form_data.get("provider", "zai")

    dao = get_token_dao()

    # 执行批量验证
    stats = await dao.validate_all_tokens(provider)

    valid_count = stats.get("valid", 0)
    guest_count = stats.get("guest", 0)
    invalid_count = stats.get("invalid", 0)

    # 生成通知消息
    if guest_count > 0:
        message_class = "bg-yellow-100 border-yellow-400 text-yellow-700"
        message = f"验证完成：有效 {valid_count} 个，匿名 {guest_count} 个，无效 {invalid_count} 个。匿名 Token 已标记。"
    elif invalid_count > 0:
        message_class = "bg-blue-100 border-blue-400 text-blue-700"
        message = f"验证完成：有效 {valid_count} 个，无效 {invalid_count} 个。"
    else:
        message_class = "bg-green-100 border-green-400 text-green-700"
        message = f"验证完成：所有 {valid_count} 个 Token 均有效！"

    return HTMLResponse(f"""
    <div class="{message_class} border px-4 py-3 rounded relative" role="alert">
        <strong class="font-bold">批量验证完成！</strong>
        <span class="block sm:inline">{message}</span>
    </div>
    """)


@router.post("/tokens/validate-single/{token_id}")
async def validate_single_token(request: Request, token_id: int):
    """验证单个 Token 并返回更新后的行"""
    from app.services.token_dao import get_token_dao

    dao = get_token_dao()

    # 验证 Token
    is_valid = await dao.validate_and_update_token(token_id)

    # 获取更新后的 Token 信息
    async with dao.get_connection() as conn:
        cursor = await conn.execute("""
            SELECT t.*, ts.total_requests, ts.successful_requests, ts.failed_requests,
                   ts.last_success_time, ts.last_failure_time
            FROM tokens t
            LEFT JOIN token_stats ts ON t.id = ts.token_id
            WHERE t.id = ?
        """, (token_id,))
        row = await cursor.fetchone()

    if row:
        # 返回更新后的单行 HTML
        token = dict(row)
        context = {
            "request": request,
            "token": token,
        }
        # 使用单行模板渲染
        return templates.TemplateResponse("components/token_row.html", context)
    else:
        return HTMLResponse("")


@router.post("/tokens/health-check")
async def health_check_tokens(request: Request):
    """执行 Token 池健康检查"""
    from app.utils.token_pool import get_token_pool

    form_data = await request.form()
    provider = form_data.get("provider", "zai")

    pool = get_token_pool()

    if not pool:
        return HTMLResponse("""
        <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative" role="alert">
            <strong class="font-bold">提示！</strong>
            <span class="block sm:inline">Token 池未初始化，请重启服务。</span>
        </div>
        """)

    # 执行健康检查
    await pool.health_check_all()

    # 获取健康状态
    status = pool.get_pool_status()
    healthy_count = status.get("healthy_tokens", 0)
    total_count = status.get("total_tokens", 0)

    if healthy_count == total_count:
        message_class = "bg-green-100 border-green-400 text-green-700"
        message = f"所有 {total_count} 个 Token 均健康！"
    elif healthy_count > 0:
        message_class = "bg-blue-100 border-blue-400 text-blue-700"
        message = f"健康检查完成：{healthy_count}/{total_count} 个 Token 健康。"
    else:
        message_class = "bg-red-100 border-red-400 text-red-700"
        message = f"警告：0/{total_count} 个 Token 健康，请检查配置。"

    return HTMLResponse(f"""
    <div class="{message_class} border px-4 py-3 rounded relative" role="alert">
        <strong class="font-bold">健康检查完成！</strong>
        <span class="block sm:inline">{message}</span>
    </div>
    """)


@router.post("/tokens/sync-pool")
async def sync_token_pool(request: Request):
    """手动同步 Token 池（从数据库重新加载）"""
    from app.utils.token_pool import get_token_pool

    form_data = await request.form()
    provider = form_data.get("provider", "zai")

    pool = get_token_pool()

    if not pool:
        return HTMLResponse("""
        <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative" role="alert">
            <strong class="font-bold">提示！</strong>
            <span class="block sm:inline">Token 池未初始化，请重启服务。</span>
        </div>
        """)

    # 从数据库同步
    await pool.sync_from_database(provider)

    # 获取同步后的状态
    status = pool.get_pool_status()
    total_count = status.get("total_tokens", 0)
    available_count = status.get("available_tokens", 0)
    user_count = status.get("user_tokens", 0)

    logger.info(f"✅ Token 池手动同步完成: {provider}, 总计 {total_count} 个 Token, 可用 {available_count} 个, 认证用户 {user_count} 个")

    if total_count == 0:
        message_class = "bg-yellow-100 border-yellow-400 text-yellow-700"
        message = f"同步完成：当前没有可用的 {provider.upper()} Token，请在数据库中启用 Token。"
    elif available_count == 0:
        message_class = "bg-orange-100 border-orange-400 text-orange-700"
        message = f"同步完成：共 {total_count} 个 Token，但无可用 Token（可能都已禁用）。"
    else:
        message_class = "bg-green-100 border-green-400 text-green-700"
        message = f"同步完成：共 {total_count} 个 Token，{available_count} 个可用，{user_count} 个认证用户。"

    return HTMLResponse(f"""
    <div class="{message_class} border px-4 py-3 rounded relative" role="alert">
        <strong class="font-bold">Token 池同步完成！</strong>
        <span class="block sm:inline">{message}</span>
    </div>
    """)
