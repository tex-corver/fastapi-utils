from typing import List, Optional

from fastapi.requests import Request
from fastapi.routing import Match, Mount
from starlette.types import Scope
from starlette.routing import Route


def _get_route_name(
    scope: Scope, routes: List[Route], route_name: Optional[str] = None
) -> Optional[str]:
    """Gets route name for given scope taking mounts into account."""

    for route in routes:
        match, child_scope = route.matches(scope)
        if match == Match.FULL:
            route_name = route.path
            child_scope = {**scope, **child_scope}
            if isinstance(route, Mount) and route.routes:
                child_route_name = _get_route_name(
                    child_scope, route.routes, route_name
                )
                if child_route_name is None:
                    route_name = None
                else:
                    route_name += child_route_name
            return route_name
        elif match == Match.PARTIAL and route_name is None:
            route_name = route.path
    return None


def get_route_name(request: Request) -> Optional[str]:
    """Gets route name for given request taking mounts into account."""

    app = request.app
    scope = request.scope
    routes = app.routes
    route_name = _get_route_name(scope, routes)

    # Starlette magically redirects requests if the path matches a route name
    # with a trailing slash appended or removed. To not spam the transaction
    # names list, we do the same here and put these redirects all in the
    # same "redirect trailing slashes" transaction name.
    if not route_name and app.router.redirect_slashes and scope["path"] != "/":
        redirect_scope = dict(scope)
        if scope["path"].endswith("/"):
            redirect_scope["path"] = scope["path"][:-1]
            trim = True
        else:
            redirect_scope["path"] = scope["path"] + "/"
            trim = False

        route_name = _get_route_name(redirect_scope, routes)
        if route_name is not None:
            route_name = route_name + "/" if trim else route_name[:-1]
    return route_name
