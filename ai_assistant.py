"""
AI助手模块 - 集成智谱GLM大模型
"""

import requests
import json
import streamlit as st

class AIAssistant:
    def __init__(self, api_key=None):
        """
        初始化AI助手
        """
        # 如果没有传入api_key，尝试从环境变量或Streamlit secrets获取
        self.api_key = api_key or st.secrets.get("ZHIPU_API_KEY", "")
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.model = "glm-4"  # 使用GLM-4模型
        
    def ask_question(self, question, context=""):
        """
        向AI提问并获取回答
        
        参数:
            question: 用户的问题
            context: 上下文信息（当前应用状态、参数等）
            
        返回:
            AI的回答文本
        """
        if not self.api_key:
            return "⚠️ 未设置API Key，请先在代码中配置或通过侧边栏输入。"
        
        # 构建完整的提示词
        full_prompt = self._build_prompt(question, context)
        
        # 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 准备请求数据
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.3,  # 较低的温度，让回答更稳定
            "max_tokens": 1000   # 限制回答长度
        }
        
        try:
            # 发送请求
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=data,
                timeout=30
            )
            
            # 解析响应
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    return f"❌ AI响应格式异常: {result}"
            else:
                return f"❌ API请求失败 (状态码: {response.status_code}): {response.text}"
                
        except requests.exceptions.Timeout:
            return "⏱️ 请求超时，请稍后重试。"
        except Exception as e:
            return f"❌ 发生错误: {str(e)}"
    
    def _build_prompt(self, question, context=""):
        """
        构建提示词
        这是最基础版本，后续会大幅优化
        """
        base_prompt = f"""
        你是一位数据分析助手，帮助用户理解延边黄牛肉商业分析模型。
        
        当前应用信息：{context}
        
        用户提问：{question}
        
        请用专业但易懂的语言回答用户问题。如果你需要更多信息才能准确回答，可以礼貌地询问。
        """
        return base_prompt
    
    def get_system_prompt(self):
        """
        获取系统提示词（可在后续优化）
        """
        return """你是一位资深的畜牧业数据分析专家，专注于延边黄牛养殖与销售业务分析。"""


# 工具函数：获取当前应用状态的文本描述
def get_app_context(params_dict):
    """
    将应用参数转换为文本描述，供AI理解上下文
    
    参数:
        params_dict: 包含所有参数的字典，例如：
            {
                "investment_unit": 10000,
                "sales_price": 198,
                "sales_achievement": 0.75,
                ...
            }
    """
    if not params_dict:
        return "当前参数未设置或未知。"
    
    context_lines = ["当前分析模型参数设置："]
    
    # 定义参数的中文描述
    param_descriptions = {
        "investment_unit": "投资单元金额（元/头）",
        "return_rate": "保底收益率（%）", 
        "sales_price": "销售单价（元/斤）",
        "sales_achievement": "销量达成率（%）",
        "mortality_rate": "牛只死亡率（%）",
        "marketing_budget": "营销预算（万元）",
        "use_advanced_model": "是否使用高级风险模型"
    }
    
    for param_key, param_value in params_dict.items():
        if param_key in param_descriptions:
            # 格式化显示
            desc = param_descriptions[param_key]
            if param_key == "use_advanced_model":
                value_str = "是" if param_value else "否"
            elif param_key in ["sales_achievement", "mortality_rate", "return_rate"]:
                value_str = f"{param_value*100:.1f}%" if isinstance(param_value, float) else f"{param_value}%"
            elif param_key == "marketing_budget":
                value_str = f"{param_value}万元"
            elif param_key == "investment_unit":
                value_str = f"¥{param_value:,}"
            elif param_key == "sales_price":
                value_str = f"¥{param_value}"
            else:
                value_str = str(param_value)
            
            context_lines.append(f"- {desc}: {value_str}")
    
    return "\n".join(context_lines)


# 测试函数
def test_ai_assistant():
    """测试AI助手功能"""
    import os
    from dotenv import load_dotenv
    
    # 尝试从环境变量加载API Key
    load_dotenv()
    api_key = os.getenv("ZHIPU_API_KEY")
    
    if not api_key:
        print("⚠️ 未找到API Key，请设置环境变量 ZHIPU_API_KEY")
        return
    
    assistant = AIAssistant(api_key)
    
    # 测试问题
    test_question = "你好，请介绍一下你自己。"
    print(f"用户: {test_question}")
    
    response = assistant.ask_question(test_question)
    print(f"AI: {response}")


if __name__ == "__main__":
    # 直接运行此文件进行测试
    test_ai_assistant()