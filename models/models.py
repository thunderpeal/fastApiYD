from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Union
import pytz
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator


class SystemItemType(Enum):
    FILE = 'FILE'
    FOLDER = 'FOLDER'


class SystemItem(BaseModel):
    id: str = Field(..., description='Уникальный идентфикатор', example='элемент_1_1')
    url: Union[str, None] = Field(
        None, description='Ссылка на файл. Для папок поле равнно null.'
    )
    date: datetime = Field(
        ...,
        description='Время последнего обновления элемента.',
        example='2022-05-28T21:12:01.000Z',
    )
    parentId: Union[str, None] = Field(
        None, description='id родительской папки', example='элемент_1_1'
    )
    type: SystemItemType
    size: Union[int, None] = Field(
        None, description='Целое число, для папки - это суммарный размер всех элеметов.'
    )
    children: Optional[List[SystemItem]] = Field(
        None, description='Список всех дочерних элементов. Для файлов поле равно null.'
    )


class SystemItemImport(BaseModel):
    class Config:
        extra = "forbid"

    id: str = Field(..., description='Уникальный идентфикатор', example='элемент_1_1')
    url: Union[str, None] = Field(
        None, description='Ссылка на файл. Для папок поле равнно null.'
    )
    parentId: Union[str, None] = Field(
        None, description='id родительской папки', example='элемент_1_1'
    )
    type: SystemItemType
    size: Union[int, None] = Field(
        ge=0, description='Целое число, для папок поле должно содержать null.'
    )


class SystemItemImportRequest(BaseModel):
    class Config:
        extra = "forbid"

    items: List[SystemItemImport] = Field(
        ..., description='Импортируемые элементы'
    )
    updateDate: datetime = Field(
        ...,
        description='Время обновления добавляемых элементов.',
        example='2022-05-28T21:12:01.000Z',
    )

    @field_validator("updateDate")
    def validate_date(cls, time, values, **kwargs):
        if time < datetime.utcnow().replace(tzinfo=pytz.utc):
            raise RequestValidationError("The date must not be in the past")
        return time


class SystemItemHistoryUnit(BaseModel):
    id: str = Field(..., description='Уникальный идентфикатор', example='элемент_1_1')
    url: Union[str, None] = Field(
        None, description='Ссылка на файл. Для папок поле равнно null.'
    )
    parentId: Union[str, None] = Field(
        None, description='id родительской папки', example='элемент_1_1'
    )
    type: SystemItemType
    size: Union[int, None] = Field(
        None,
        description='Целое число, для папки - это суммарный размер всех её элементов.',
    )
    date: datetime = Field(..., description='Время последнего обновления элемента.')


class SystemItemHistoryResponse(BaseModel):
    items: Optional[List[SystemItemHistoryUnit]] = Field(
        None, description='История в произвольном порядке.'
    )


class Error(BaseModel):
    code: int
    message: str
