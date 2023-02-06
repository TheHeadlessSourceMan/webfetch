import typing
from enum import Enum

class HttpMethod(Enum):
    GET="GET" # used to get data
    POST="POST" # used to create data
    UPDATE="UPDATE" # used to modify data
    DELETE="DELETE" # used to delete data
    OPTIONS="OPTIONS" # used to ask what the interface supports

MimeType=str

WebFetchResult=typing.Tuple[bytes,MimeType]