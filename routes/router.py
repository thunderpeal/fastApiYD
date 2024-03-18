from copy import copy
from fastapi import APIRouter
from fastapi.exceptions import RequestValidationError, HTTPException
from datetime import datetime
from core.nodes_repository import NodesRepository
from core.helpers import update_parent
from typing import Union
import os

from models.models import (
    SystemItem,
    SystemItemHistoryResponse, SystemItemHistoryUnit,
    SystemItemImportRequest, SystemItemType,
)

router = APIRouter()

DATABASE_URL = os.environ['database_url']
database = NodesRepository(DATABASE_URL)


@router.post('/imports')
async def post_imports(body: SystemItemImportRequest):
    request_ids = [item.id for item in body.items]
    if len(set(request_ids)) != len(request_ids):
        raise RequestValidationError("Can't have duplicate ids")

    """
    Валидацию следует утащить в pydantic
    """
    values_dict = {}
    to_update = {}
    for item in body.items:
        if item.parentId == item.id:
            raise RequestValidationError("Parent id can't be the same as id")
        if item.type == SystemItemType.FOLDER and (item.url is not None or item.size is not None):
            raise RequestValidationError("Folder can't have url or size")
        elif item.type == SystemItemType.FILE and (item.url is None or item.size <= 0):
            raise RequestValidationError("Item must have url and size")

        full_route = f'/{item.id}'
        if item.parentId:
            if item.parentId in values_dict:
                if values_dict[item.parentId]['type'] != SystemItemType.FOLDER.value:
                    raise RequestValidationError("Parent must exist and be a folder")
                full_route = values_dict[item.parentId]['full_route'] + full_route
            else:
                parent_node = await database.read_node({'id': item.parentId})
                if not parent_node or parent_node.type != SystemItemType.FOLDER.value:
                    raise RequestValidationError("Parent must exist and be a folder")
                full_route = parent_node.full_route + full_route

        existing_node = await database.read_node({'id': item.id})
        if existing_node:
            if existing_node.type != item.type.value:
                raise RequestValidationError("Can't change type")
            if existing_node.type == SystemItemType.FOLDER.value and existing_node.parent_id == item.parentId:
                raise RequestValidationError("Nothing to update")
            to_update[item.id] = existing_node

        values_dict[item.id] = {"id": item.id, "parent_id": item.parentId, "type": item.type.value,
                                "url": item.url, "date": body.updateDate, "size": item.size,
                                "full_route": full_route}

    for _, values in values_dict.items():
        if values['id'] in to_update:
            if values['type'] == SystemItemType.FOLDER.value:
                update_folder_values = dict(to_update[values['id']]._mapping)
                await update_parent(database, update_folder_values, adding=False)
                update_folder_values['parent_id'] = values['parent_id']
                await database.update_node(update_folder_values)
                values['size'] = update_folder_values['size']
            else:
                await database.update_node(values_dict[values['id']])
                if values['parent_id'] == to_update[values['id']].parent_id:
                    values['size'] = values['size'] - to_update[values['id']].size
                else:
                    # Обновляем ветку, откуда был перенесен файл
                    old_values = copy(values)
                    old_values['parent_id'] = to_update[values['id']].parent_id
                    await update_parent(database, old_values, adding=False)
        else:
            # if values['size'] is None:
            #    values['size'] = 0
            await database.create_node(values)
        await update_parent(database, values)


@router.delete('/delete/{id}', response_model=None)
async def delete_delete_id(id: str, date: datetime = ...) -> None:
    node = await database.read_node({'id': id})
    if node is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if node.parent_id:
        values_dict = dict(node._mapping)
        values_dict['date'] = date
        await update_parent(database, values_dict, adding=False)
    await database.delete_node({"id": id})


@router.get('/nodes/{id}')
async def get_nodes_id(id: str):
    node = await database.read_node({'id': id})
    if node is None:
        raise HTTPException(status_code=404, detail="Item not found")
    parent = SystemItem(id=node.id, type=node.type, url=node.url, size=node.size,
                        date=node.date, parentId=node.parent_id, children=[])

    """
    Следует добавить поле в БД для хранения полного пути и, как следствие,
    получения всех дочерних элементов через фильтрацию по подпути.
    """
    # children = await database.read_children_by_route({'route': node.full_route})
    async def check_children(element) -> None:
        children = await database.read_children({'id': element.id})
        element.children = [SystemItem(id=child.id, type=child.type, url=child.url, size=child.size,
                                       date=child.date, parentId=child.parent_id, children=[])
                            for child in children]
        for child in element.children:
            await check_children(child)

    await check_children(parent)

    return parent


@router.get('/node/{id}/history', response_model=SystemItemHistoryResponse)
async def get_node_id_history(id, date_start, date_end) -> Union[SystemItemHistoryResponse, None]:
    pass


@router.get('/updates', response_model=SystemItemHistoryResponse)
async def get_updates(date: datetime) -> SystemItemHistoryResponse:
    nodes = await database.updates_till_date({'date': date})
    items = [SystemItemHistoryUnit(id=node.id, type=node.type, url=node.url, size=node.size,
                                   date=node.date, parentId=node.parent_id) for node in nodes]
    return SystemItemHistoryResponse(items=items)
