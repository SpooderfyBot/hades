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



