from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limits=None):
        super().__init__(app)
        self.request_counts = defaultdict(list)
        self.limits = limits or {
            '/api/auth/login': {'limit': 5, 'window': 60},
            '/api/auth/register': {'limit': 3, 'window': 300}
        }
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        endpoint = request.url.path
        
        if endpoint in self.limits:
            limit_config = self.limits[endpoint]
            current_time = time.time()
            
            self.request_counts[client_ip] = [
                t for t in self.request_counts[client_ip] 
                if current_time - t < limit_config['window']
            ]
            
            if len(self.request_counts[client_ip]) >= limit_config['limit']:
                raise HTTPException(
                    status_code=429, 
                    detail="Too many requests"
                )
            
            self.request_counts[client_ip].append(current_time)
        
        return await call_next(request)
