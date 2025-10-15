"""
Captcha Solver Module
Supports multiple captcha solving services
"""
import httpx
import asyncio
import time
from typing import Optional, Dict, Any
from loguru import logger


class CaptchaSolver:
    """通用验证码求解器，支持多个验证码服务"""
    
    def __init__(self, service: str = "2captcha", api_key: Optional[str] = None):
        """
        初始化验证码求解器
        
        Args:
            service: 验证码服务 ('2captcha', 'anticaptcha', 'capsolver')
            api_key: API密钥
        """
        self.service = service.lower()
        self.api_key = api_key
        self.logger = logger.bind(service=service)
        
        # 服务配置
        self.config = {
            "2captcha": {
                "submit_url": "https://2captcha.com/in.php",
                "result_url": "https://2captcha.com/res.php",
                "method": "userrecaptcha"  # for reCAPTCHA
            },
            "anticaptcha": {
                "submit_url": "https://api.anti-captcha.com/createTask",
                "result_url": "https://api.anti-captcha.com/getTaskResult"
            },
            "capsolver": {
                "submit_url": "https://api.capsolver.com/createTask",
                "result_url": "https://api.capsolver.com/getTaskResult"
            }
        }
        
    async def solve_recaptcha_v2(
        self,
        site_key: str,
        page_url: str,
        timeout: int = 120
    ) -> Optional[str]:
        """
        解决 reCAPTCHA v2
        
        Args:
            site_key: reCAPTCHA site key
            page_url: 页面URL
            timeout: 超时时间（秒）
            
        Returns:
            验证码解决方案 token，失败返回 None
        """
        if not self.api_key:
            self.logger.error("❌ 未配置验证码服务 API Key")
            return None
            
        if self.service == "2captcha":
            return await self._solve_2captcha_recaptcha(site_key, page_url, timeout)
        elif self.service == "anticaptcha":
            return await self._solve_anticaptcha_recaptcha(site_key, page_url, timeout)
        elif self.service == "capsolver":
            return await self._solve_capsolver_recaptcha(site_key, page_url, timeout)
        else:
            self.logger.error(f"❌ 不支持的验证码服务: {self.service}")
            return None
            
    async def solve_hcaptcha(
        self,
        site_key: str,
        page_url: str,
        timeout: int = 120
    ) -> Optional[str]:
        """
        解决 hCaptcha
        
        Args:
            site_key: hCaptcha site key
            page_url: 页面URL
            timeout: 超时时间（秒）
            
        Returns:
            验证码解决方案 token，失败返回 None
        """
        if not self.api_key:
            self.logger.error("❌ 未配置验证码服务 API Key")
            return None
            
        if self.service == "2captcha":
            return await self._solve_2captcha_hcaptcha(site_key, page_url, timeout)
        elif self.service == "anticaptcha":
            return await self._solve_anticaptcha_hcaptcha(site_key, page_url, timeout)
        elif self.service == "capsolver":
            return await self._solve_capsolver_hcaptcha(site_key, page_url, timeout)
        else:
            self.logger.error(f"❌ 不支持的验证码服务: {self.service}")
            return None
            
    async def solve_cloudflare_turnstile(
        self,
        site_key: str,
        page_url: str,
        timeout: int = 120
    ) -> Optional[str]:
        """
        解决 Cloudflare Turnstile
        
        Args:
            site_key: Turnstile site key
            page_url: 页面URL
            timeout: 超时时间（秒）
            
        Returns:
            验证码解决方案 token，失败返回 None
        """
        if not self.api_key:
            self.logger.error("❌ 未配置验证码服务 API Key")
            return None
            
        if self.service == "2captcha":
            return await self._solve_2captcha_turnstile(site_key, page_url, timeout)
        elif self.service == "capsolver":
            return await self._solve_capsolver_turnstile(site_key, page_url, timeout)
        else:
            self.logger.error(f"❌ {self.service} 不支持 Cloudflare Turnstile")
            return None
            
    # ==================== 2Captcha Implementation ====================
    
    async def _solve_2captcha_recaptcha(
        self,
        site_key: str,
        page_url: str,
        timeout: int
    ) -> Optional[str]:
        """2Captcha reCAPTCHA v2 求解"""
        self.logger.info(f"🔐 使用 2Captcha 解决 reCAPTCHA v2...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 提交验证码任务
                submit_data = {
                    "key": self.api_key,
                    "method": "userrecaptcha",
                    "googlekey": site_key,
                    "pageurl": page_url,
                    "json": 1
                }
                
                response = await client.post(
                    self.config["2captcha"]["submit_url"],
                    data=submit_data
                )
                result = response.json()
                
                if result.get("status") != 1:
                    self.logger.error(f"❌ 提交验证码任务失败: {result.get('request')}")
                    return None
                    
                task_id = result.get("request")
                self.logger.info(f"✅ 验证码任务已提交，ID: {task_id}")
                
                # 轮询结果
                start_time = time.time()
                while time.time() - start_time < timeout:
                    await asyncio.sleep(5)  # 每5秒检查一次
                    
                    result_data = {
                        "key": self.api_key,
                        "action": "get",
                        "id": task_id,
                        "json": 1
                    }
                    
                    response = await client.get(
                        self.config["2captcha"]["result_url"],
                        params=result_data
                    )
                    result = response.json()
                    
                    if result.get("status") == 1:
                        solution = result.get("request")
                        self.logger.info(f"✅ 验证码解决成功！")
                        return solution
                    elif result.get("request") == "CAPCHA_NOT_READY":
                        continue
                    else:
                        self.logger.error(f"❌ 验证码求解失败: {result.get('request')}")
                        return None
                        
                self.logger.error(f"❌ 验证码求解超时")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 2Captcha 求解异常: {e}")
            return None
            
    async def _solve_2captcha_hcaptcha(
        self,
        site_key: str,
        page_url: str,
        timeout: int
    ) -> Optional[str]:
        """2Captcha hCaptcha 求解"""
        self.logger.info(f"🔐 使用 2Captcha 解决 hCaptcha...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 提交验证码任务
                submit_data = {
                    "key": self.api_key,
                    "method": "hcaptcha",
                    "sitekey": site_key,
                    "pageurl": page_url,
                    "json": 1
                }
                
                response = await client.post(
                    self.config["2captcha"]["submit_url"],
                    data=submit_data
                )
                result = response.json()
                
                if result.get("status") != 1:
                    self.logger.error(f"❌ 提交验证码任务失败: {result.get('request')}")
                    return None
                    
                task_id = result.get("request")
                self.logger.info(f"✅ 验证码任务已提交，ID: {task_id}")
                
                # 轮询结果（与 reCAPTCHA 相同）
                start_time = time.time()
                while time.time() - start_time < timeout:
                    await asyncio.sleep(5)
                    
                    result_data = {
                        "key": self.api_key,
                        "action": "get",
                        "id": task_id,
                        "json": 1
                    }
                    
                    response = await client.get(
                        self.config["2captcha"]["result_url"],
                        params=result_data
                    )
                    result = response.json()
                    
                    if result.get("status") == 1:
                        solution = result.get("request")
                        self.logger.info(f"✅ 验证码解决成功！")
                        return solution
                    elif result.get("request") == "CAPCHA_NOT_READY":
                        continue
                    else:
                        self.logger.error(f"❌ 验证码求解失败: {result.get('request')}")
                        return None
                        
                self.logger.error(f"❌ 验证码求解超时")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 2Captcha 求解异常: {e}")
            return None
            
    async def _solve_2captcha_turnstile(
        self,
        site_key: str,
        page_url: str,
        timeout: int
    ) -> Optional[str]:
        """2Captcha Cloudflare Turnstile 求解"""
        self.logger.info(f"🔐 使用 2Captcha 解决 Cloudflare Turnstile...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 提交验证码任务
                submit_data = {
                    "key": self.api_key,
                    "method": "turnstile",
                    "sitekey": site_key,
                    "pageurl": page_url,
                    "json": 1
                }
                
                response = await client.post(
                    self.config["2captcha"]["submit_url"],
                    data=submit_data
                )
                result = response.json()
                
                if result.get("status") != 1:
                    self.logger.error(f"❌ 提交验证码任务失败: {result.get('request')}")
                    return None
                    
                task_id = result.get("request")
                self.logger.info(f"✅ 验证码任务已提交，ID: {task_id}")
                
                # 轮询结果
                start_time = time.time()
                while time.time() - start_time < timeout:
                    await asyncio.sleep(5)
                    
                    result_data = {
                        "key": self.api_key,
                        "action": "get",
                        "id": task_id,
                        "json": 1
                    }
                    
                    response = await client.get(
                        self.config["2captcha"]["result_url"],
                        params=result_data
                    )
                    result = response.json()
                    
                    if result.get("status") == 1:
                        solution = result.get("request")
                        self.logger.info(f"✅ 验证码解决成功！")
                        return solution
                    elif result.get("request") == "CAPCHA_NOT_READY":
                        continue
                    else:
                        self.logger.error(f"❌ 验证码求解失败: {result.get('request')}")
                        return None
                        
                self.logger.error(f"❌ 验证码求解超时")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 2Captcha 求解异常: {e}")
            return None
            
    # ==================== AntiCaptcha Implementation ====================
    
    async def _solve_anticaptcha_recaptcha(
        self,
        site_key: str,
        page_url: str,
        timeout: int
    ) -> Optional[str]:
        """AntiCaptcha reCAPTCHA v2 求解"""
        self.logger.info(f"🔐 使用 AntiCaptcha 解决 reCAPTCHA v2...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 提交任务
                task_data = {
                    "clientKey": self.api_key,
                    "task": {
                        "type": "NoCaptchaTaskProxyless",
                        "websiteURL": page_url,
                        "websiteKey": site_key
                    }
                }
                
                response = await client.post(
                    self.config["anticaptcha"]["submit_url"],
                    json=task_data
                )
                result = response.json()
                
                if result.get("errorId") != 0:
                    self.logger.error(f"❌ 提交任务失败: {result.get('errorDescription')}")
                    return None
                    
                task_id = result.get("taskId")
                self.logger.info(f"✅ 任务已提交，ID: {task_id}")
                
                # 轮询结果
                start_time = time.time()
                while time.time() - start_time < timeout:
                    await asyncio.sleep(5)
                    
                    result_data = {
                        "clientKey": self.api_key,
                        "taskId": task_id
                    }
                    
                    response = await client.post(
                        self.config["anticaptcha"]["result_url"],
                        json=result_data
                    )
                    result = response.json()
                    
                    if result.get("status") == "ready":
                        solution = result.get("solution", {}).get("gRecaptchaResponse")
                        self.logger.info(f"✅ 验证码解决成功！")
                        return solution
                    elif result.get("status") == "processing":
                        continue
                    else:
                        self.logger.error(f"❌ 验证码求解失败: {result.get('errorDescription')}")
                        return None
                        
                self.logger.error(f"❌ 验证码求解超时")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ AntiCaptcha 求解异常: {e}")
            return None
            
    async def _solve_anticaptcha_hcaptcha(
        self,
        site_key: str,
        page_url: str,
        timeout: int
    ) -> Optional[str]:
        """AntiCaptcha hCaptcha 求解"""
        self.logger.info(f"🔐 使用 AntiCaptcha 解决 hCaptcha...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 提交任务
                task_data = {
                    "clientKey": self.api_key,
                    "task": {
                        "type": "HCaptchaTaskProxyless",
                        "websiteURL": page_url,
                        "websiteKey": site_key
                    }
                }
                
                response = await client.post(
                    self.config["anticaptcha"]["submit_url"],
                    json=task_data
                )
                result = response.json()
                
                if result.get("errorId") != 0:
                    self.logger.error(f"❌ 提交任务失败: {result.get('errorDescription')}")
                    return None
                    
                task_id = result.get("taskId")
                self.logger.info(f"✅ 任务已提交，ID: {task_id}")
                
                # 轮询结果（与 reCAPTCHA 类似）
                start_time = time.time()
                while time.time() - start_time < timeout:
                    await asyncio.sleep(5)
                    
                    result_data = {
                        "clientKey": self.api_key,
                        "taskId": task_id
                    }
                    
                    response = await client.post(
                        self.config["anticaptcha"]["result_url"],
                        json=result_data
                    )
                    result = response.json()
                    
                    if result.get("status") == "ready":
                        solution = result.get("solution", {}).get("gRecaptchaResponse")
                        self.logger.info(f"✅ 验证码解决成功！")
                        return solution
                    elif result.get("status") == "processing":
                        continue
                    else:
                        self.logger.error(f"❌ 验证码求解失败: {result.get('errorDescription')}")
                        return None
                        
                self.logger.error(f"❌ 验证码求解超时")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ AntiCaptcha 求解异常: {e}")
            return None
            
    # ==================== CapSolver Implementation ====================
    
    async def _solve_capsolver_recaptcha(
        self,
        site_key: str,
        page_url: str,
        timeout: int
    ) -> Optional[str]:
        """CapSolver reCAPTCHA v2 求解"""
        self.logger.info(f"🔐 使用 CapSolver 解决 reCAPTCHA v2...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 提交任务
                task_data = {
                    "clientKey": self.api_key,
                    "task": {
                        "type": "ReCaptchaV2TaskProxyLess",
                        "websiteURL": page_url,
                        "websiteKey": site_key
                    }
                }
                
                response = await client.post(
                    self.config["capsolver"]["submit_url"],
                    json=task_data
                )
                result = response.json()
                
                if result.get("errorId") != 0:
                    self.logger.error(f"❌ 提交任务失败: {result.get('errorDescription')}")
                    return None
                    
                task_id = result.get("taskId")
                self.logger.info(f"✅ 任务已提交，ID: {task_id}")
                
                # 轮询结果
                start_time = time.time()
                while time.time() - start_time < timeout:
                    await asyncio.sleep(5)
                    
                    result_data = {
                        "clientKey": self.api_key,
                        "taskId": task_id
                    }
                    
                    response = await client.post(
                        self.config["capsolver"]["result_url"],
                        json=result_data
                    )
                    result = response.json()
                    
                    if result.get("status") == "ready":
                        solution = result.get("solution", {}).get("gRecaptchaResponse")
                        self.logger.info(f"✅ 验证码解决成功！")
                        return solution
                    elif result.get("status") == "processing":
                        continue
                    else:
                        self.logger.error(f"❌ 验证码求解失败: {result.get('errorDescription')}")
                        return None
                        
                self.logger.error(f"❌ 验证码求解超时")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ CapSolver 求解异常: {e}")
            return None
            
    async def _solve_capsolver_hcaptcha(
        self,
        site_key: str,
        page_url: str,
        timeout: int
    ) -> Optional[str]:
        """CapSolver hCaptcha 求解"""
        self.logger.info(f"🔐 使用 CapSolver 解决 hCaptcha...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 提交任务
                task_data = {
                    "clientKey": self.api_key,
                    "task": {
                        "type": "HCaptchaTaskProxyLess",
                        "websiteURL": page_url,
                        "websiteKey": site_key
                    }
                }
                
                response = await client.post(
                    self.config["capsolver"]["submit_url"],
                    json=task_data
                )
                result = response.json()
                
                if result.get("errorId") != 0:
                    self.logger.error(f"❌ 提交任务失败: {result.get('errorDescription')}")
                    return None
                    
                task_id = result.get("taskId")
                self.logger.info(f"✅ 任务已提交，ID: {task_id}")
                
                # 轮询结果
                start_time = time.time()
                while time.time() - start_time < timeout:
                    await asyncio.sleep(5)
                    
                    result_data = {
                        "clientKey": self.api_key,
                        "taskId": task_id
                    }
                    
                    response = await client.post(
                        self.config["capsolver"]["result_url"],
                        json=result_data
                    )
                    result = response.json()
                    
                    if result.get("status") == "ready":
                        solution = result.get("solution", {}).get("gRecaptchaResponse")
                        self.logger.info(f"✅ 验证码解决成功！")
                        return solution
                    elif result.get("status") == "processing":
                        continue
                    else:
                        self.logger.error(f"❌ 验证码求解失败: {result.get('errorDescription')}")
                        return None
                        
                self.logger.error(f"❌ 验证码求解超时")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ CapSolver 求解异常: {e}")
            return None
            
    async def _solve_capsolver_turnstile(
        self,
        site_key: str,
        page_url: str,
        timeout: int
    ) -> Optional[str]:
        """CapSolver Cloudflare Turnstile 求解"""
        self.logger.info(f"🔐 使用 CapSolver 解决 Cloudflare Turnstile...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 提交任务
                task_data = {
                    "clientKey": self.api_key,
                    "task": {
                        "type": "AntiTurnstileTaskProxyLess",
                        "websiteURL": page_url,
                        "websiteKey": site_key
                    }
                }
                
                response = await client.post(
                    self.config["capsolver"]["submit_url"],
                    json=task_data
                )
                result = response.json()
                
                if result.get("errorId") != 0:
                    self.logger.error(f"❌ 提交任务失败: {result.get('errorDescription')}")
                    return None
                    
                task_id = result.get("taskId")
                self.logger.info(f"✅ 任务已提交，ID: {task_id}")
                
                # 轮询结果
                start_time = time.time()
                while time.time() - start_time < timeout:
                    await asyncio.sleep(5)
                    
                    result_data = {
                        "clientKey": self.api_key,
                        "taskId": task_id
                    }
                    
                    response = await client.post(
                        self.config["capsolver"]["result_url"],
                        json=result_data
                    )
                    result = response.json()
                    
                    if result.get("status") == "ready":
                        solution = result.get("solution", {}).get("token")
                        self.logger.info(f"✅ 验证码解决成功！")
                        return solution
                    elif result.get("status") == "processing":
                        continue
                    else:
                        self.logger.error(f"❌ 验证码求解失败: {result.get('errorDescription')}")
                        return None
                        
                self.logger.error(f"❌ 验证码求解超时")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ CapSolver 求解异常: {e}")
            return None


def get_captcha_solver(
    service: str = "2captcha",
    api_key: Optional[str] = None
) -> CaptchaSolver:
    """
    获取验证码求解器实例
    
    Args:
        service: 验证码服务名称
        api_key: API密钥
        
    Returns:
        CaptchaSolver 实例
    """
    return CaptchaSolver(service=service, api_key=api_key)

