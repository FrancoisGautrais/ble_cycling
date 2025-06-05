from abc import ABC, abstractmethod


class BaseDriver(ABC):


    @abstractmethod
    def get_status(self):  pass

    @abstractmethod
    def get_controller_name(self):
        pass


    @abstractmethod
    def use_controller(self, name):
        pass


    @abstractmethod
    def start(self, ): pass

    @abstractmethod
    def pause(self, ): pass

    @abstractmethod
    def resume(self, ): pass

    @abstractmethod
    def stop(self, ): pass

    @abstractmethod
    def ctrl_set_prop(self, name, value): pass

    @abstractmethod
    def ctrl_get_prop(self, name): pass

    @abstractmethod
    def ctrl_call_function(self, name, data): pass

