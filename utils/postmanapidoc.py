import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Union, Tuple

from aiohttp import ClientSession

from utils.apidoc import APIDoc, Endpoint
from utils.common import read_json_file


class PostmanAPIDoc(APIDoc):
    class PostmanEndpoint(Endpoint):
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
            super().__init__(name=name,
                             path=path,
                             method=method,
                             tags=tags,
                             request_query_params=request_query_params,
                             request_path_params=request_path_params,
                             request_body=request_body,
                             response_example=response_example)

    @staticmethod
    def _compose_path(path_elems: List[str]) -> str:
        path = ''
        for path_elem in path_elems:
            if path_elem[0] != ':':
                path += f'/{path_elem}'
            else:
                path += '/{' + path_elem[1:] + '}'
        return path

    @staticmethod
    def _extract_env_variables(env: Dict[str, Any]) -> Dict[str, str]:
        vars = {}
        for var in env['values']:
            vars[var['key']] = var['value']
        return vars

    @staticmethod
    def _extract_path_params(variables: Dict[str, str]) -> Dict[str, str]:
        path_params = {}
        for var_name in variables:
            if var_name.startswith('__') and var_name.endswith('__'):
                path_params[var_name[2:len(var_name) - 2]] = variables[var_name]
        return None if not path_params else path_params

    @staticmethod
    async def _extract_endpoints(tags_endpoints_map: Dict[Tuple, Any],
                                 variables: Dict[str, str],
                                 auth: Dict[str, Any]) -> List[Endpoint]:
        coroutines = []
        for tags in tags_endpoints_map:
            coroutines.append(PostmanAPIDoc._build_endpoint(tags_endpoints_map, variables, auth, tags))
        results = await asyncio.gather(*coroutines)
        return list(results)

    @staticmethod
    async def _build_endpoint(tags_endpoints_map: Dict[Tuple, Any],
                              variables: Dict[str, str],
                              auth: Dict[str, Any],
                              tags: Tuple) -> PostmanEndpoint:
        try:
            endpoint = tags_endpoints_map[tags]
            name = endpoint['name']
            request = endpoint['request']
            method = request['method'].lower()
            path = PostmanAPIDoc._compose_path(request['url']['path'])
            request_query_params = None if 'query' not in request['url'] else {param['key']: param['value'] for param in
                                                                               request['url']['query']}
            request_path_params = PostmanAPIDoc._extract_path_params(variables)
            request_body = None if 'body' not in request else json.loads(request['body']['raw'])

            request_body_is_none = False
            if method == 'post' and request_body is None:
                request_body = ''
                request_body_is_none = True

            response_example = await PostmanAPIDoc._get_response_example(request, variables, request_body, auth)

            if request_body_is_none:
                request_body = None

            return PostmanAPIDoc.PostmanEndpoint(
                name=name,
                path=path,
                method=method,
                tags=tags[:-2],
                request_query_params=request_query_params,
                request_path_params=request_path_params,
                request_body=request_body,
                response_example=response_example
            )
        except Exception as e:
            print(f'Error with endpoint {endpoint["name"]} ---> {e}')

    @staticmethod
    def _build_url(url_tmp: Dict[str, Any],
                   variables: Dict[str, str]) -> str:
        url = variables[url_tmp['host'][0][2:len(url_tmp['host'][0]) - 2]]
        for path_elem in url_tmp['path']:
            if path_elem.startswith('{{') and path_elem.endswith('}}'):
                url += f'/{variables[path_elem[2:len(path_elem) - 2]]}'
            else:
                url += f'/{path_elem}'
        if 'query' in url_tmp:
            params = []
            for param in url_tmp['query']:
                params.append(f'{param["key"]}={param["value"]}')
            url += f'?{"&".join(params)}'
        return url

    @staticmethod
    async def _get_response_example(request: Dict[str, Any],
                                    variables: Dict[str, str],
                                    request_body: Dict[str, str],
                                    auth: Dict[str, Any]) -> Dict[str, Any]:
        url = PostmanAPIDoc._build_url(request['url'], variables)

        headers = {}
        if auth['position'] == 'header':
            headers.update(auth['params'])
        if 'header' in request:
            req_headers = PostmanAPIDoc._extract_headers(request['header'], variables)
            headers.update(req_headers)

        async with ClientSession() as session:
            if request['method'] == 'POST':
                http_call = session.post
            elif request['method'] == 'GET':
                http_call = session.get
            elif request['method'] == 'PUT':
                http_call = session.put
            elif request['method'] == 'DELETE':
                http_call = session.delete

            async with http_call(
                    url=url,
                    json=request_body,
                    headers=headers
            ) as response:
                resp = await response.json()
        return resp

    @staticmethod
    def _extract_headers(headers: List[Dict[str, str]],
                         variables: Dict[str, str]) -> Dict[str, Any]:
        headers_new = {}
        for header in headers:
            if header['key'].startswith('{{') and header['key'].endswith('}}'):
                key = variables[header['key'][2:-2]]
            else:
                key = header['key']
            if header['value'].startswith('{{') and header['value'].endswith('}}'):
                value = variables[header['value'][2:-2]]
            else:
                value = header['value']
            headers_new[key] = value
        return headers_new

    @staticmethod
    def _extract_auth(auth_tmp: Dict[str, Any],
                      variables: Dict[str, str]) -> Dict[str, Any]:
        auth = {
            "type": auth_tmp['type'],
        }
        if auth_tmp['type'] == 'apikey':
            for auth_param in auth_tmp['apikey']:
                if auth_param['key'] == 'key':
                    key = auth_param['value']
                elif auth_param['key'] == 'value':
                    value = variables[auth_param['value'][2:-2]] if auth_param[
                                                                        'value'].startswith(
                        '{{') and auth_param['value'].endswith('}}') else auth_param['value']
            auth['params'] = {key: value}
            auth['position'] = 'header'
        return auth

    @staticmethod
    def _extract_tags_endpoint(tags_endpoints_map: Dict[Tuple, Any],
                               collection: Dict[str, Any], tags: List[str] = []):
        for item in collection['item']:
            tags_new = []
            tags_new.extend(tags)
            tags_new.append(item['name'])
            if 'request' in item:
                tags_new.append(item['request']['method'])
                tags_endpoints_map[tuple(tags_new)] = item
            else:
                PostmanAPIDoc._extract_tags_endpoint(tags_endpoints_map, item, tags_new)

    @classmethod
    def factory(cls,
                path_postman_collection: Path,
                path_postman_environment: Path):
        environment = read_json_file(path_postman_environment)
        variables = PostmanAPIDoc._extract_env_variables(environment)
        collection = read_json_file(path_postman_collection)
        tags_endpoints_map = {}
        PostmanAPIDoc._extract_tags_endpoint(tags_endpoints_map, collection)
        auth = PostmanAPIDoc._extract_auth(collection['auth'], variables)
        # asyncio.run(PostmanAPIDoc._extract_endpoints(endpoints, tags_endpoints_map, variables, auth))
        loop = asyncio.get_event_loop()
        endpoints = loop.run_until_complete(PostmanAPIDoc._extract_endpoints(tags_endpoints_map, variables, auth))
        return cls(collection['info']['name'], [endpoint for endpoint in endpoints if endpoint])
