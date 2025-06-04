import asyncio
import copy
import inspect
import threading
from abc import ABC, abstractmethod

import uvicorn
from fastapi import FastAPI, routing


class Route:
    POST = "post"
    GET = "get"
    PUT = "put"
    DELETE = "delete"

    _all_methods = [POST, GET, PUT, DELETE]
    _method_ = None
    def __init__(self, method, url):
        self.methods = []
        if method is None:
            self.methods = self._method_
        if not isinstance(method, (list, tuple, set)):
            self.methods = [self.methods]
        self.url = url
        self.function = None
        self._parent = None

        unmanageable_methods = [x for x in self.methods if x not in self._all_methods]
        if unmanageable_methods:
            raise ValueError(f"Impossible de gérér les méthodes: {unmanageable_methods}")

    def __get__(self, instance, owner):
        ret = copy.copy(self)
        ret._parent = instance
        ret.function = ret.function.__get__(instance, owner)
        return ret

    def __call__(self, *args, **kwargs):
        if self._parent:
            return self.function(*args, **kwargs)
        else:
            function, *_ = args
            ret = copy.copy(self)
            ret.function = function
            return ret

class TypedRoute(Route):
    def __init__(self, url):
        super().__init__(None, url)

class Get(TypedRoute):
    _method_ = Route.GET

class Post(TypedRoute):
    _method_ = Route.POST

class Put(TypedRoute):
    _method_ = Route.PUT

class Delete(TypedRoute):
    _method_ = Route.DELETE


class BaseServer(ABC):

    _autostart_server_ = False
    _autostart_server_threaded_ = True
    def __init__(self):
        self._setup_route()
        if self._autostart_server_:
            self.run_server(self._autostart_server_threaded_)

    def _setup_route(self, cls=None):
        cls = cls or self.__class__

        for x in cls.__bases__:
            self._setup_route(x)

        for k, v in vars(cls).items():
            if isinstance(v, Route):
                self._add_route(v)


    def run_server(self, thread=True):
        if thread:
            self._server_thread = threading.Thread(target=self.run_server, args=(False,))
            self._server_thread.start()
        else:
            self.server_start()
    @abstractmethod
    def server_start(self):
        pass

    @abstractmethod
    def server_stop(self):
        pass

    @abstractmethod
    def _add_route(self, route : Route):
        pass

class Annotation: pass

class JsonBody(Annotation):
    pass


class CustomRootClass(routing.APIRoute):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class Routing(routing.APIRouter):

    def __init__(self, *args, **kwargs):
        kwargs["route_class"] = CustomRootClass
        super().__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


    def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class CustomFastAPI(FastAPI):

    def setup(self) -> None:
        self.router.route_class = CustomRootClass
        return super().setup()



class HttpBaseServer(BaseServer):

    def __init__(self, host=None, port=None):
        self.host = host or "127.0.0.1"
        self.port = port or 8000
        self._server_app = CustomFastAPI(webhooks=Routing())
        self._server = None
        self._server_thread = None
        super().__init__()

    def server_start(self):
        config = uvicorn.Config(self._server_app, host=self.host, port=self.port, log_level="error")
        self._server = uvicorn.Server(config)
        asyncio.run(self._server.serve())

    def server_stop(self):
        if self._server:
            self._server.should_exit = True


    def _add_route(self, route : Route):
        for m in route.methods:
            fct  = getattr(self._server_app, m)(route.url)
            fct(route.function.__get__(self, self))

def main():
    MyServer().run_server(False)


if __name__ == '__main__':
    main()
    print(f"Done !")
