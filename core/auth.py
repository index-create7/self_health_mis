# core/auth.py
from typing import Optional, Tuple, Dict, Any
from data.dal.user_dal import register_user, login_user


def validate_user_credentials(username: str, password: str) -> Dict[str, Any]:
    """
    验证用户凭据（用户名和密码）的公共逻辑
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        Dict: 包含验证结果的字典，格式为 {"status": bool, "message": str}
    """
    # 参数类型校验
    if not isinstance(username, str) or not isinstance(password, str):
        return {"status": False, "message": "用户名和密码必须是字符串类型"}
    
    # 输入清理
    username = username.strip() if username else ""
    
    # 基本非空校验
    if not username or not password:
        return {"status": False, "message": "用户名或密码不能为空"}
    
    # 长度校验
    if len(username) < 3:
        return {"status": False, "message": "用户名长度不能少于3位"}
    if len(password) < 6:
        return {"status": False, "message": "密码长度不能少于6位"}
    
    return {"status": True, "message": "验证通过"}

# 注册用户（添加业务校验：用户名长度、密码强度）
def user_register(username: str, password: str) -> Dict[str, Any]:
    """
    用户注册功能
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        Dict: 包含status(布尔值)和message(字符串)的字典
    """
    try:
        # 使用公共验证函数验证基本凭据
        validation_result = validate_user_credentials(username, password)
        if not validation_result["status"]:
            return validation_result
        
        # 用户名格式校验（只允许字母、数字、下划线）
        if not username.isalnum() and '_' not in username:
            return {"status": False, "message": "用户名只能包含字母、数字和下划线"}
        
        # 调用DAL层完成注册，并捕获可能的异常
        result = register_user(username, password)
        if result:
            return {"status": True, "message": "注册成功"}
        else:
            return {"status": False, "message": "注册失败，用户名可能已存在"}
    except Exception as e:
        return {"status": False, "message": f"注册过程中发生错误: {str(e)}"}

# 用户登录（封装DAL层，统一返回逻辑）
def user_login(username: str, password: str) -> Dict[str, Any]:
    """
    用户登录功能
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        Dict: 包含status(布尔值)、user_id(整数或None)和message(字符串)的字典
    """
    try:
        # 使用公共验证函数验证基本凭据
        validation_result = validate_user_credentials(username, password)
        if not validation_result["status"]:
            # 为登录接口添加user_id字段
            return {"status": False, "user_id": None, "message": validation_result["message"]}
        
        # 调用DAL层进行登录，并捕获可能的异常
        user_id = login_user(username, password)
        if user_id is None:
            return {"status": False, "user_id": None, "message": "用户名或密码错误"}
        return {"status": True, "user_id": user_id, "message": "登录成功"}
    except Exception as e:
        return {"status": False, "user_id": None, "message": f"登录过程中发生错误: {str(e)}"}