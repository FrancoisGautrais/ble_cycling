from abc import ABC


class Loadable(ABC):

    @classmethod
    def get_id(cls):
        return f"{cls.__module__}.{cls.__name__}"

def get_loadable_class(id):
    module_name, _,name = id.rpartition("_")
    module = __import__(module_name)
    return getattr(module, name)

def instanciate_loadable_class(id, params):
    cls = get_loadable_class(id)
    return cls(**params)