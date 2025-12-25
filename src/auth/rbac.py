from fastapi import Depends, HTTPException, status
from functools import wraps
from .models import UserRole

class RBACService:
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [
            "create_user", "delete_user", "update_user", 
            "access_all_data", "manage_system"
        ],
        UserRole.EDITOR: [
            "create_content", "edit_content", 
            "view_analytics", "manage_recommendations"
        ],
        UserRole.ANALYST: [
            "view_analytics", "generate_reports", 
            "access_insights"
        ],
        UserRole.USER: [
            "view_own_content", "generate_personal_recommendations"
        ]
    }

    @classmethod
    def check_permissions(cls, required_permissions):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
                user_role = UserRole(current_user.role)
                user_permissions = cls.ROLE_PERMISSIONS.get(user_role, [])
                
                if not all(perm in user_permissions for perm in required_permissions):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )
                
                return await func(*args, current_user=current_user, **kwargs)
            return wrapper
        return decorator
