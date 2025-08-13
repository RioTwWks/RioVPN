__all__ = ("router",)

from aiogram import Router

router = Router(name="handlers_main_router")

# Import handlers with error handling
try:
    from .start import router as start_router
    router.include_router(start_router)
except ImportError:
    pass

try:
    from .captcha import router as captcha_router
    router.include_router(captcha_router)
except ImportError:
    pass

try:
    from .profile import router as profile_router
    router.include_router(profile_router)
except ImportError:
    pass

try:
    from .pay import router as pay_router
    router.include_router(pay_router)
except ImportError:
    pass

try:
    from .donate import router as donate_router
    router.include_router(donate_router)
except ImportError:
    pass

try:
    from .coupons import router as coupons_router
    router.include_router(coupons_router)
except ImportError:
    pass

try:
    from .refferal import router as refferal_router
    router.include_router(refferal_router)
except ImportError:
    pass

try:
    from .fallback_router import fallback_router
    router.include_router(fallback_router)
except ImportError:
    pass
