from datetime import datetime, date


async def update_parent(database, values, adding=True) -> None:
    parent_node = await database.read_node({'id': values['parent_id']})
    if parent_node:
        while parent_node:
            parent_size = parent_node.size if parent_node.size else 0
            child_size = values['size'] if values['size'] else 0
            if adding:
                parent_size += child_size
            else:
                parent_size -= child_size
            await database.update_node({'id': parent_node.id, 'date': values['date'], 'size': parent_size,
                                        'parent_id': parent_node.parent_id})
            if parent_node.parent_id:
                parent_node = await database.read_node({'id': parent_node.parent_id})
            else:
                parent_node = None


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))
