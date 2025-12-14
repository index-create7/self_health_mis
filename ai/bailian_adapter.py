import os
from dashscope import Application

def call_with_session_d(user_input):
    """
    调用百炼AI模型获取回复
    
    Args:
        user_input: 用户输入的文本
        
    Returns:
        str: AI助手的回复文本，如果失败则返回错误信息
    """
    try:
        # 调用AI模型获取回复
        response = Application.call(
            api_key="sk-13ce462ef2a04a0ab4195a3af98492da",
            app_id='041e4994ed74499b94cc3a847b83053b',
            prompt=user_input)

        # 检查响应是否成功
        if hasattr(response, 'output') and hasattr(response.output, 'text'):
            # 直接返回用户问题的回答
            assistant_reply = response.output.text
            print(f'AI助手回复: {assistant_reply}')
            return assistant_reply
        else:
            # 处理错误响应
            print(f'request_id={getattr(response, "request_id", "未知")}')
            print(f'message={getattr(response, "message", "未知错误")}')
            print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
            return f"调用失败：{getattr(response, 'message', '未知错误')}"



    except Exception as e:
        print(f"调用百炼AI模型时发生异常：{e}")
        return f"调用失败：{str(e)}"

def call_with_session_a(user_input):
    """
    调用百炼AI模型获取流式回复
    【修复核心】：统一返回类型，避免生成器被错误检查status_code
    
    Args:
        user_input: 用户输入的文本
        
    Returns:
        - generator: 流式响应生成器（成功且stream=True时）
        - dict: 错误字典（异常响应，含message）
        - str: 非流式成功响应的文本内容
    """
    try:
        # 调用百炼AI模型
        response = Application.call(
            api_key="sk-13ce462ef2a04a0ab4195a3af98492da",  # 建议生产环境用环境变量
            app_id='f7f17875f8094d66bf3fa4af4f5d51cd',      # 替换为实际AppID
            prompt=user_input,
            stream=True
        )
        
        # ========== 关键：提前处理响应类型，避免上层错误 ==========
        # 1. 流式响应（生成器）：处理流式响应，从每个ApplicationResponse中提取文本
        if hasattr(response, '__iter__') and not isinstance(response, (str, list, tuple, dict)):
            print(f"[DEBUG] bailian_adapter: 返回流式生成器，类型={type(response).__name__}")
            
            # 创建一个新的生成器来处理流式响应
            def stream_processor():
                try:
                    for chunk in response:
                        print(f"[DEBUG] bailian_adapter: 流式分片类型={type(chunk).__name__}")
                        # 检查分片是否是ApplicationResponse对象
                        if hasattr(chunk, 'status_code') and chunk.status_code == 200:
                            # 从分片的output.text中提取文本
                            if hasattr(chunk, 'output') and hasattr(chunk.output, 'text'):
                                yield chunk.output.text
                                print(f"[DEBUG] bailian_adapter: 提取到文本={chunk.output.text[:20]}...")
                            else:
                                print(f"[DEBUG] bailian_adapter: 分片没有output.text属性")
                        else:
                            # 处理错误响应
                            error_msg = getattr(chunk, 'message', '未知错误')
                            print(f"[DEBUG] bailian_adapter: 流式响应错误={error_msg}")
                            yield f"\n\n⚠️ 流式响应错误：{error_msg}"
                except Exception as e:
                    print(f"[DEBUG] bailian_adapter: 流式处理异常={e}")
                    yield f"\n\n⚠️ 流式处理异常：{str(e)}"
            
            return stream_processor()
        
        # 2. 非流式响应：检查是否成功
        elif hasattr(response, 'output') and hasattr(response.output, 'text'):
            # 成功响应→提取文本
            text = response.output.text
            print(f"[DEBUG] bailian_adapter: 非流式成功响应，文本={text[:50]}...")
            return text
        else:
             # 错误响应→标准化字典
             print(f"[DEBUG] bailian_adapter: 返回错误响应")
             return {
                 "message": getattr(response, 'message', '百炼API返回错误'),
                 "request_id": getattr(response, 'request_id', '')
             }

    # 全局异常捕获→标准化错误字典
    except Exception as e:
        error_msg = f"百炼API调用异常：{str(e)}"
        print(f"[ERROR] bailian_adapter: {error_msg}")
        return {
            "message": error_msg,
            "exception": str(e)
        }