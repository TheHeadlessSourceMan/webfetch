"""
all http method verbs
"""
import typing
from enum import Enum

class HttpMethod(Enum):
    """
    all http method verbs
    """
    GET="GET" # used to get data
    POST="POST" # used to create data
    UPDATE="UPDATE" # used to modify data
    DELETE="DELETE" # used to delete data
    OPTIONS="OPTIONS" # used to ask what the interface supports

MimeType=str

WebFetchResult=typing.Tuple[bytes,MimeType]
