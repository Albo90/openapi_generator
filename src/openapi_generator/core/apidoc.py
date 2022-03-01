from typing import Any, Dict, Union, List, Tuple


class Endpoint:
    def __init__(self,
                 *,
                 name: str,
                 path: str,
                 method: str,
                 tags: Tuple[str] = None,
                 request_query_params: Union[Dict[str, Any], None],
                 request_path_params: Union[Dict[str, Any], None],
                 request_body: Union[Dict[str, Any], None],
                 response_example: Dict[str, Any]):
        self.name = name
        self.path = path
        self.method = method
        self.tags = tags
        self.request_query_params = request_query_params
        self.request_path_params = request_path_params
        self.request_body = request_body
        self.response_example = response_example

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str):
        self._path = path

    @property
    def method(self) -> str:
        return self._method

    @method.setter
    def method(self, method: str):
        self._method = method

    @property
    def tags(self) -> Tuple[str]:
        return self._tags

    @tags.setter
    def tags(self, tags: Tuple[str]):
        self._tags = tags

    @property
    def request_query_params(self) -> Dict[str, Any]:
        return self._request_query_params

    @request_query_params.setter
    def request_query_params(self, request_query_params: Dict[str, Any]):
        self._request_query_params = request_query_params

    @property
    def request_path_params(self) -> Dict[str, Any]:
        return self._request_path_params

    @request_path_params.setter
    def request_path_params(self, request_path_params: Dict[str, Any]):
        self._request_path_params = request_path_params

    @property
    def request_body(self) -> Dict[str, Any]:
        return self._request_body

    @request_body.setter
    def request_body(self, request_body: Dict[str, Any]):
        self._request_body = request_body

    @property
    def response_example(self) -> Dict[str, Any]:
        return self._response_example

    @response_example.setter
    def response_example(self, response_example: Dict[str, Any]):
        self._response_example = response_example

    def __str__(self):
        return f'{self.method.upper()} {self.path}: {self.name}'


class APIDoc:
    def __init__(self,
                 name: str,
                 endpoints: List[Endpoint]):
        self.name = name
        self.endpoints = endpoints

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def endpoints(self) -> List[Endpoint]:
        return self._endpoints

    @endpoints.setter
    def endpoints(self, endpoints: List[Endpoint]):
        self._endpoints = endpoints
