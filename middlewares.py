#!/usr/bin/env python3
"""
RioVPN Middlewares
"""

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to inject database session"""
    
    def __init__(self, sessionmaker):
        self.sessionmaker = sessionmaker
        super().__init__()
    
    async def __call__(self, handler, event, data):
        async with self.sessionmaker() as session:
            data['session'] = session
            return await handler(event, data)


class AdminMiddleware(BaseMiddleware):
    """Middleware to check admin status"""
    
    async def __call__(self, handler, event, data):
        # For now, just add a placeholder admin status
        # In a real implementation, you would check against the database
        data['admin'] = False
        return await handler(event, data)


class CaptchaMiddleware(BaseMiddleware):
    """Middleware to handle captcha"""
    
    async def __call__(self, handler, event, data):
        # For now, just add a placeholder captcha status
        # In a real implementation, you would check captcha completion
        data['captcha'] = True
        return await handler(event, data)


def register_middleware(dispatcher, sessionmaker=None):
    """
    Register all middlewares with the dispatcher
    """
    try:
        if sessionmaker:
            dispatcher.message.middleware(DatabaseMiddleware(sessionmaker))
            dispatcher.callback_query.middleware(DatabaseMiddleware(sessionmaker))
        
        dispatcher.message.middleware(AdminMiddleware())
        dispatcher.callback_query.middleware(AdminMiddleware())
        
        dispatcher.message.middleware(CaptchaMiddleware())
        dispatcher.callback_query.middleware(CaptchaMiddleware())
        
        logger.info("✅ Middlewares registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to register middlewares: {e}")
        return False


if __name__ == "__main__":
    print("Middlewares module loaded successfully")
