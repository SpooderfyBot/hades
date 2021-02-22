from functools import wraps
from fastapi import Request, responses


def login_required(func):
    """
    A simple decorator that checks the incoming request and makes sure the user
    has got a valid session otherwise forcing them to login and then redirecting
    them back to the endpoint.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        session = request.session.get('info')
        if session is None:
            return responses.RedirectResponse(f"/login?redirect_to={request.url.path}")
        return await func(*args, **kwargs)
    return wrapper


def enforce_authorization(value: str):
    def wrap_dec(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if request.headers.get("authorization") != value:
                return responses.ORJSONResponse(
                    {"status": 401, "data": "Un-Authorized request"},
                    status_code=401
                )

            return await func(*args, **kwargs)
        return wrapper
    return wrap_dec

