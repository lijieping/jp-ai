"""Conversation Schemas 模块 - 对话相关数据模型"""
from app.conversation.schemas.conversation_schema import ConvIn, ConvOut
from app.conversation.schemas.message_schema import MsgCreate, MsgOut

__all__ = ["ConvIn", "ConvOut", "MsgCreate", "MsgOut"]

