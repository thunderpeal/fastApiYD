from core.repository import Repository
from databases import Database
import logging
import json
from core.helpers import json_serial
from datetime import timedelta
from fastapi import HTTPException

logging.basicConfig(filename='app.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)


class NodesRepository(Repository):
    def __init__(self, connection_string):
        # initialize database connection
        self._connection_string = connection_string
        self._connection = Database(connection_string)

    async def connect(self):
        await self._connection.connect()

    async def disconnect(self):
        await self._connection.disconnect()

    async def create_node(self, query_values):
        id_to_add = query_values['id']
        logging.info(f"Attempting to add node {id_to_add}")

        query = "INSERT INTO disk_tree (id, url, type, size, date, full_route, parent_id) " \
                "VALUES (:id, :url, :type, :size, :date, :full_route, :parent_id) RETURNING id"

        try:
            node_id = await self._connection.execute(query=query, values=query_values)
            logging.info(f"Successfully added node {node_id}")
            await self.bump_node_to_history(query_values)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add node {id_to_add}: {e}")

    async def read_node(self, query_values):
        id_to_read = query_values['id']
        logging.info(f"Attempting to read node {id_to_read}")
        query = "SELECT * FROM disk_tree WHERE id = :node_id"
        values = {"node_id": id_to_read}
        try:
            result = await self._connection.fetch_one(query=query, values=values)
            logging.info(f"Successfully read node {id_to_read}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch node {id_to_read} from database: {e}")
        return result

    async def read_children(self, query_values):
        id_to_read = query_values['id']
        logging.info(f"Attempting to read children of node {id_to_read}")
        query = "SELECT * FROM disk_tree WHERE parent_id = :parent_id"
        values = {"parent_id": id_to_read}
        try:
            result = await self._connection.fetch_all(query=query, values=values)
            logging.info(f"Successfully read children of node {id_to_read}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch children of {id_to_read} from database: {e}")
        return result

    async def read_children_by_route(self, query_values):
        id_to_read = query_values['id']
        route = query_values['route']
        logging.info(f"Attempting to read children of node {id_to_read}")
        query = f"SELECT * FROM disk_tree WHERE full_route LIKE '%{route}%'"
        try:
            result = await self._connection.fetch_all(query=query)
            logging.info(f"Successfully read children of node {id_to_read}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch children of {id_to_read} from database: {e}")
        return result

    async def update_node(self, query_values):
        id_to_update = query_values['id']
        date = query_values['date']
        size = query_values['size']
        url = query_values['url'] if 'url' in query_values else None
        parent_id = query_values['parent_id']
        logging.info(f"Attempting to update node {id_to_update}")
        query = "UPDATE disk_tree SET date = :date, url = :url, size = :size, " \
                "parent_id = :parent_id WHERE id = :node_id"
        values = {"node_id": id_to_update, "date": date, "size": size, "parent_id": parent_id, "url": url}
        try:
            await self._connection.execute(query=query, values=values)
            logging.info(f"Successfully updated node {id_to_update}")
            await self.bump_node_to_history(query_values)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update node {id_to_update} from database: {e}")

    async def delete_node(self, query_values):
        id_to_delete = query_values['id']
        logging.info(f"Attempting to delete node {id_to_delete}")
        query = "DELETE FROM disk_tree WHERE id = :node_id"
        values = {"node_id": id_to_delete}
        try:
            await self._connection.execute(query=query, values=values)
            logging.info(f"Successfully deleted node {id_to_delete}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete node {id_to_delete} from database: {e}")

    async def updates_till_date(self, query_values):
        date = query_values['date']
        logging.info(f"Attempting to get history: 24H back from {date}")
        query = "SELECT * FROM disk_tree WHERE date <= :end_date and date >= :start_date"
        values = {"start_date": date - timedelta(hours=24), "end_date": date}
        try:
            nodes = await self._connection.fetch_all(query=query, values=values)
            logging.info(f"Successfully fetched history 24H back from {date}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch history 24H back from {date}: {e}")
        return nodes

    async def node_to_history(self, query_values):
        id_to_add = query_values['id']
        logging.info(f"Attempting to put node {id_to_add} to history")

        query = "INSERT INTO node_history (id, content, date) " \
                "VALUES (:id, :content, :date) RETURNING id"

        try:
            node_id = await self._connection.execute(query=query, values=query_values)
            logging.info(f"Successfully put node {node_id} to history")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to put node {id_to_add} to history: {e}")

    async def bump_node_to_history(self, query_values):
        query_values['parentId'] = query_values['parent_id']
        if 'full_route' in query_values:
            del query_values['full_route']
        history_json = json.dumps(query_values, default=json_serial)
        query_value_history = {'id': query_values['id'], 'content': history_json, 'date': query_values['date']}
        await self.node_to_history(query_value_history)

    async def get_history_per_node(self, query_values):
        id_to_find = query_values['id']
        logging.info(f"Attempting to get history for element {id_to_find}")
        query = "SELECT * FROM node_history WHERE id = :id and (date <= :date_end and date >= :date_start)"
        try:
            nodes = await self._connection.fetch_all(query=query, values=query_values)
            logging.info(f"Successfully fetched history for element {id_to_find}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch history for element {id_to_find}: {e}")
        return nodes

