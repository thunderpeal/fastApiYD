from abc import ABC, abstractmethod


class Repository(ABC):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def create_node(self, query_values):
        pass

    @abstractmethod
    async def read_node(self, query_values):
        pass

    @abstractmethod
    async def read_children(self, query_values):
        pass

    @abstractmethod
    async def read_children_by_route(self, query_values):
        pass

    @abstractmethod
    async def update_node(self, query_values):
        pass

    @abstractmethod
    async def delete_node(self, query_values):
        pass

    @abstractmethod
    async def updates_till_date(self, query_values):
        pass
