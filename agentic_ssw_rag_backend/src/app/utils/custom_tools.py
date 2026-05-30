"""
企业级工具扩展示例。

你可以在这里接入：
- ERP 查询
- CRM 客户信息
- 工单系统
- MySQL / Kingbase / 达梦数据库
- 审批流
- 邮件发送
- 日程创建

然后在 agent.py 里把工具加入 ReActAgent(tools=[...])。
"""


def query_erp_order(order_no: str) -> str:
    """根据订单号查询 ERP 订单信息。"""
    return f"ERP order {order_no}: TODO"
