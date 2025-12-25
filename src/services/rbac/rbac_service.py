"""
Role-Based Access Control (RBAC) Service

Complete RBAC implementation with:
- Comprehensive permission matrix
- Resource-level permissions
- Role hierarchy
- Permission checking decorators
- Dynamic permission assignment
"""
import logging
from typing import List, Set, Optional, Dict, Any
from enum import Enum
from functools import wraps
from fastapi import HTTPException, status, Depends

from src.models.user import User, UserRole

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Granular permissions for different resources and actions."""

    # User Management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    MANAGE_ROLES = "manage_roles"

    # Company Management
    CREATE_COMPANY = "create_company"
    READ_COMPANY = "read_company"
    UPDATE_COMPANY = "update_company"
    DELETE_COMPANY = "delete_company"

    # Competitor Management
    CREATE_COMPETITOR = "create_competitor"
    READ_COMPETITOR = "read_competitor"
    UPDATE_COMPETITOR = "update_competitor"
    DELETE_COMPETITOR = "delete_competitor"

    # Domain Management
    CREATE_DOMAIN = "create_domain"
    READ_DOMAIN = "read_domain"
    UPDATE_DOMAIN = "update_domain"
    DELETE_DOMAIN = "delete_domain"

    # Content Management
    CREATE_CONTENT = "create_content"
    READ_CONTENT = "read_content"
    UPDATE_CONTENT = "update_content"
    DELETE_CONTENT = "delete_content"

    # Report Management
    CREATE_REPORT = "create_report"
    READ_REPORT = "read_report"
    UPDATE_REPORT = "update_report"
    DELETE_REPORT = "delete_report"
    EXPORT_REPORT = "export_report"
    SCHEDULE_REPORT = "schedule_report"

    # Analytics & Insights
    VIEW_ANALYTICS = "view_analytics"
    VIEW_INSIGHTS = "view_insights"
    GENERATE_INSIGHTS = "generate_insights"

    # SEO Services
    ACCESS_SEO_TOOLS = "access_seo_tools"
    RUN_PAGESPEED = "run_pagespeed"
    RUN_SERP_ANALYSIS = "run_serp_analysis"

    # External API Access
    ACCESS_GNEWS_API = "access_gnews_api"
    ACCESS_GOOGLE_ANALYTICS = "access_google_analytics"
    ACCESS_EXTERNAL_APIS = "access_external_apis"

    # System Management
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"
    MANAGE_API_QUOTAS = "manage_api_quotas"
    CONFIGURE_SETTINGS = "configure_settings"

    # Data Management
    IMPORT_DATA = "import_data"
    EXPORT_DATA = "export_data"
    BULK_OPERATIONS = "bulk_operations"

    # Search & Discovery
    SEARCH_LINKS = "search_links"
    TRACK_SEARCH_HISTORY = "track_search_history"

    # Web Scraping
    INITIATE_SCRAPING = "initiate_scraping"
    VIEW_SCRAPED_CONTENT = "view_scraped_content"


class RBACService:
    """
    Role-Based Access Control Service.

    Manages permissions and authorization for different user roles.
    """

    # Comprehensive permission matrix
    ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
        UserRole.ADMIN: {
            # Admins have all permissions
            *list(Permission)
        },

        UserRole.MANAGER: {
            # Company & Team Management
            Permission.CREATE_COMPANY,
            Permission.READ_COMPANY,
            Permission.UPDATE_COMPANY,

            # Competitor Analysis (Full Access)
            Permission.CREATE_COMPETITOR,
            Permission.READ_COMPETITOR,
            Permission.UPDATE_COMPETITOR,
            Permission.DELETE_COMPETITOR,

            # Domain Management
            Permission.CREATE_DOMAIN,
            Permission.READ_DOMAIN,
            Permission.UPDATE_DOMAIN,
            Permission.DELETE_DOMAIN,

            # Content Management
            Permission.CREATE_CONTENT,
            Permission.READ_CONTENT,
            Permission.UPDATE_CONTENT,
            Permission.DELETE_CONTENT,

            # Reports (Full Access)
            Permission.CREATE_REPORT,
            Permission.READ_REPORT,
            Permission.UPDATE_REPORT,
            Permission.DELETE_REPORT,
            Permission.EXPORT_REPORT,
            Permission.SCHEDULE_REPORT,

            # Analytics
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_INSIGHTS,
            Permission.GENERATE_INSIGHTS,

            # SEO Tools
            Permission.ACCESS_SEO_TOOLS,
            Permission.RUN_PAGESPEED,
            Permission.RUN_SERP_ANALYSIS,

            # External APIs
            Permission.ACCESS_GNEWS_API,
            Permission.ACCESS_GOOGLE_ANALYTICS,
            Permission.ACCESS_EXTERNAL_APIS,

            # Data Operations
            Permission.IMPORT_DATA,
            Permission.EXPORT_DATA,
            Permission.BULK_OPERATIONS,

            # Search
            Permission.SEARCH_LINKS,
            Permission.TRACK_SEARCH_HISTORY,

            # Scraping
            Permission.INITIATE_SCRAPING,
            Permission.VIEW_SCRAPED_CONTENT,

            # User Management (Limited)
            Permission.READ_USER,
            Permission.UPDATE_USER,
        },

        UserRole.ANALYST: {
            # Read-only company access
            Permission.READ_COMPANY,

            # Competitor Analysis (Read & Create)
            Permission.READ_COMPETITOR,
            Permission.CREATE_COMPETITOR,
            Permission.UPDATE_COMPETITOR,

            # Domain (Read-only)
            Permission.READ_DOMAIN,

            # Content (Read & Create)
            Permission.READ_CONTENT,
            Permission.CREATE_CONTENT,

            # Reports (Create & Read)
            Permission.CREATE_REPORT,
            Permission.READ_REPORT,
            Permission.EXPORT_REPORT,

            # Analytics (Full Access)
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_INSIGHTS,
            Permission.GENERATE_INSIGHTS,

            # SEO Tools
            Permission.ACCESS_SEO_TOOLS,
            Permission.RUN_PAGESPEED,
            Permission.RUN_SERP_ANALYSIS,

            # External APIs
            Permission.ACCESS_GNEWS_API,
            Permission.ACCESS_GOOGLE_ANALYTICS,
            Permission.ACCESS_EXTERNAL_APIS,

            # Search
            Permission.SEARCH_LINKS,
            Permission.TRACK_SEARCH_HISTORY,

            # Scraping (View only)
            Permission.VIEW_SCRAPED_CONTENT,

            # Data Export
            Permission.EXPORT_DATA,
        },

        UserRole.USER: {
            # Basic read access
            Permission.READ_COMPANY,
            Permission.READ_COMPETITOR,
            Permission.READ_DOMAIN,
            Permission.READ_CONTENT,

            # Limited reporting
            Permission.READ_REPORT,

            # View analytics
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_INSIGHTS,

            # Basic search
            Permission.SEARCH_LINKS,

            # View scraped content
            Permission.VIEW_SCRAPED_CONTENT,
        }
    }

    @classmethod
    def get_user_permissions(cls, user: User) -> Set[Permission]:
        """Get all permissions for a user.

        Args:
            user: User object

        Returns:
            Set of permissions
        """
        if not user or not user.role:
            return set()

        role = UserRole(user.role) if isinstance(user.role, str) else user.role

        # Admin always gets all permissions
        if user.is_admin or role == UserRole.ADMIN:
            return cls.ROLE_PERMISSIONS[UserRole.ADMIN]

        return cls.ROLE_PERMISSIONS.get(role, set())

    @classmethod
    def has_permission(cls, user: User, permission: Permission) -> bool:
        """Check if user has a specific permission.

        Args:
            user: User object
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        user_permissions = cls.get_user_permissions(user)
        return permission in user_permissions

    @classmethod
    def has_any_permission(cls, user: User, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions.

        Args:
            user: User object
            permissions: List of permissions to check

        Returns:
            True if user has at least one permission, False otherwise
        """
        user_permissions = cls.get_user_permissions(user)
        return any(perm in user_permissions for perm in permissions)

    @classmethod
    def has_all_permissions(cls, user: User, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions.

        Args:
            user: User object
            permissions: List of permissions to check

        Returns:
            True if user has all permissions, False otherwise
        """
        user_permissions = cls.get_user_permissions(user)
        return all(perm in user_permissions for perm in permissions)

    @classmethod
    def check_resource_access(
        cls,
        user: User,
        resource_type: str,
        action: str,
        resource_owner_id: Optional[int] = None
    ) -> bool:
        """Check if user can access a specific resource.

        Args:
            user: User object
            resource_type: Type of resource (e.g., 'company', 'report')
            action: Action to perform (e.g., 'read', 'update', 'delete')
            resource_owner_id: Optional owner ID for ownership checks

        Returns:
            True if user has access, False otherwise
        """
        # Build permission string
        permission_str = f"{action}_{resource_type}".upper()

        try:
            permission = Permission(permission_str)
        except ValueError:
            logger.warning(f"Unknown permission: {permission_str}")
            return False

        # Check if user has the permission
        if not cls.has_permission(user, permission):
            return False

        # Additional ownership check for non-admin users
        if resource_owner_id and not user.is_admin:
            # Users can only modify their own resources unless they're managers
            if action in ['update', 'delete']:
                user_role = UserRole(user.role) if isinstance(user.role, str) else user.role
                if user_role == UserRole.USER and user.id != resource_owner_id:
                    return False

        return True

    @classmethod
    def require_permission(cls, *required_permissions: Permission):
        """Decorator to require specific permissions for endpoint access.

        Args:
            *required_permissions: One or more permissions required

        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, current_user: User = None, **kwargs):
                if current_user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )

                if not cls.has_all_permissions(current_user, list(required_permissions)):
                    missing_perms = [
                        perm.value for perm in required_permissions
                        if perm not in cls.get_user_permissions(current_user)
                    ]
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "error": "Insufficient permissions",
                            "required_permissions": [p.value for p in required_permissions],
                            "missing_permissions": missing_perms
                        }
                    )

                return await func(*args, current_user=current_user, **kwargs)
            return wrapper
        return decorator

    @classmethod
    def require_any_permission(cls, *required_permissions: Permission):
        """Decorator to require any of the specified permissions.

        Args:
            *required_permissions: One or more permissions (user needs at least one)

        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, current_user: User = None, **kwargs):
                if current_user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )

                if not cls.has_any_permission(current_user, list(required_permissions)):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "error": "Insufficient permissions",
                            "required_permissions": [p.value for p in required_permissions],
                            "message": "You need at least one of the specified permissions"
                        }
                    )

                return await func(*args, current_user=current_user, **kwargs)
            return wrapper
        return decorator

    @classmethod
    def require_role(cls, *required_roles: UserRole):
        """Decorator to require specific user roles.

        Args:
            *required_roles: One or more roles required

        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, current_user: User = None, **kwargs):
                if current_user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )

                user_role = UserRole(current_user.role) if isinstance(current_user.role, str) else current_user.role

                if user_role not in required_roles and not current_user.is_admin:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "error": "Insufficient role",
                            "required_roles": [r.value for r in required_roles],
                            "current_role": user_role.value
                        }
                    )

                return await func(*args, current_user=current_user, **kwargs)
            return wrapper
        return decorator

    @classmethod
    def get_permission_summary(cls, user: User) -> Dict[str, Any]:
        """Get a summary of user's permissions.

        Args:
            user: User object

        Returns:
            Dictionary with permission summary
        """
        permissions = cls.get_user_permissions(user)

        # Group permissions by category
        categories = {
            'user_management': [],
            'company_management': [],
            'competitor_management': [],
            'content_management': [],
            'report_management': [],
            'analytics': [],
            'seo_tools': [],
            'external_apis': [],
            'system_management': [],
            'data_operations': [],
            'search': [],
            'scraping': []
        }

        for perm in permissions:
            perm_lower = perm.value.lower()
            if 'user' in perm_lower:
                categories['user_management'].append(perm.value)
            elif 'company' in perm_lower:
                categories['company_management'].append(perm.value)
            elif 'competitor' in perm_lower:
                categories['competitor_management'].append(perm.value)
            elif 'content' in perm_lower:
                categories['content_management'].append(perm.value)
            elif 'report' in perm_lower:
                categories['report_management'].append(perm.value)
            elif 'analytics' in perm_lower or 'insights' in perm_lower:
                categories['analytics'].append(perm.value)
            elif 'seo' in perm_lower or 'pagespeed' in perm_lower or 'serp' in perm_lower:
                categories['seo_tools'].append(perm.value)
            elif 'api' in perm_lower:
                categories['external_apis'].append(perm.value)
            elif 'system' in perm_lower or 'logs' in perm_lower or 'settings' in perm_lower:
                categories['system_management'].append(perm.value)
            elif 'import' in perm_lower or 'export' in perm_lower or 'bulk' in perm_lower:
                categories['data_operations'].append(perm.value)
            elif 'search' in perm_lower:
                categories['search'].append(perm.value)
            elif 'scrap' in perm_lower:
                categories['scraping'].append(perm.value)

        return {
            'user_id': user.id,
            'role': user.role if isinstance(user.role, str) else user.role.value,
            'is_admin': user.is_admin,
            'total_permissions': len(permissions),
            'permissions_by_category': categories,
            'all_permissions': [p.value for p in permissions]
        }
