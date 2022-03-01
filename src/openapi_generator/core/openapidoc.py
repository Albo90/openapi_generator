from pathlib import Path
from typing import List, Any, Dict, Union, Tuple

import yaml
from genson import SchemaBuilder

from .apidoc import Endpoint, APIDoc
from .postmanapidoc import PostmanAPIDoc


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)


class OpenAPIDoc(APIDoc):
    class OpenAPIEndpoint(Endpoint):

        _PREFIX_COMPONENTS_SCHEMAS = '#/components/schemas/'
        _PREFIX_COMPONENTS_RESPONSES = '#/components/responses/'
        _REF_PREFIX = '#/components/schemas/'

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
        def _split_schema_in_subschemas(json_schema: Dict[str, Any],
                                        prefix: str, schema_name, schemas):
            props = json_schema['properties']
            properties = {}
            for prop_name in props:
                if props[prop_name]['type'] == 'object':
                    sub_component_name = f'{prefix}{prop_name[0].capitalize() + prop_name[1:]}'
                    properties[prop_name] = {
                        '$ref': f'{OpenAPIDoc.OpenAPIEndpoint._REF_PREFIX}{sub_component_name}'
                    }
                    OpenAPIDoc.OpenAPIEndpoint._split_schema_in_subschemas(props[prop_name], prefix, sub_component_name,
                                                                           schemas)
                elif props[prop_name]['type'] == 'array' and 'items' not in props[prop_name]:
                    print(
                        f'WARNING: Can not determine items type of {prop_name} in {prefix} default choose string type')
                    properties[prop_name] = props[prop_name]
                    properties[prop_name]['items'] = {'type': 'string'}
                elif props[prop_name]['type'] == 'array' and (
                        props[prop_name]['items']['type'] == 'array' or props[prop_name]['items']['type'] == 'object'):
                    sub_component_name = f'{prefix}{prop_name[0].capitalize() + prop_name[1:]}'
                    properties[prop_name] = {
                        'type': 'array',
                        'items': {
                            '$ref': f'{OpenAPIDoc.OpenAPIEndpoint._REF_PREFIX}{sub_component_name}'
                        }
                    }
                    OpenAPIDoc.OpenAPIEndpoint._split_schema_in_subschemas(props[prop_name]['items'], prefix,
                                                                           sub_component_name, schemas)
                elif props[prop_name]['type'] == 'null':
                    properties[prop_name] = {'type': 'object'}
                else:
                    properties[prop_name] = props[prop_name]

            if schema_name in schemas:
                print(f'WARNING: {schema_name} is already present in schemas please fix it manually')
            schemas[schema_name] = dict()
            # if 'required' in json_schema:
            #     schemas[schema_name]['required'] = json_schema['required']
            schemas[schema_name]['type'] = json_schema['type']
            schemas[schema_name]['properties'] = properties
            schemas[schema_name]['additionalProperties'] = False

        @staticmethod
        def generate_schemas_from_example(prefix: str,
                                          example: Dict[str, Any]) -> Dict[str, Any]:
            if example:
                builder = SchemaBuilder()
                builder.add_object(example)
                json_schema = builder.to_schema()
                del json_schema['$schema']
                schemas = {}
                OpenAPIDoc.OpenAPIEndpoint._split_schema_in_subschemas(json_schema, prefix,
                                                                       prefix, schemas)
                return schemas
            return {}

        @property
        def request_schemas(self) -> Dict[str, Any]:
            cap_name = f'{self.name[0].capitalize()}{self.name[1:]}'
            cap_method = f'{self.method[0].capitalize()}{self.method[1:]}'
            request_schema_ref = f'{cap_method}{cap_name}Request'
            return OpenAPIDoc.OpenAPIEndpoint.generate_schemas_from_example(request_schema_ref, self.request_body)

        def _get_response_200(self) -> Dict[str, Any]:
            return {
                'description': 'OK',
                'content': {
                    'application/json': {
                        'schema': {
                            '$ref': f'{OpenAPIDoc.OpenAPIEndpoint._PREFIX_COMPONENTS_SCHEMAS}{self.method[0].capitalize()}{self.method[1:]}{self.name[0].capitalize()}{self.name[1:]}Response'
                        },
                        'example': self.response_example
                    }
                }
            }

        def _get_parameters(self, position: str) -> List[Dict[str, Any]]:
            if position == 'query':
                params = self.request_query_params
            elif position == 'path':
                params = self.request_path_params

            parameters = []
            for param_name in params:
                param = dict()
                param['name'] = param_name
                param['in'] = position
                param['schema'] = {'type': 'string'}
                param['example'] = params[param_name]
                parameters.append(param)

            return parameters

        def _get_request_body(self) -> Dict[str, Any]:
            return {
                'content':
                    {
                        'application/json':
                            {
                                'schema':
                                    {
                                        '$ref': f'{OpenAPIDoc.OpenAPIEndpoint._PREFIX_COMPONENTS_SCHEMAS}{self.method[0].capitalize()}{self.method[1:]}{self.name[0].capitalize()}{self.name[1:]}Request'
                                    },
                                'example': self.request_body
                            }
                    },
                'required': True
            }

        def _insert_request_struct(self,
                                   openapi_path: Dict[str, Any]):
            if self.request_query_params or self.request_path_params:
                openapi_path['parameters'] = []
                if self.request_query_params:
                    openapi_path['parameters'].extend(self._get_parameters('query'))

                if self.request_path_params:
                    openapi_path['parameters'].extend(self._get_parameters('path'))

            if self.request_body:
                request_body = self._get_request_body()
                openapi_path['requestBody'] = request_body

        def _insert_responses_struct(self,
                                     openapi_path: Dict[str, Any]):
            responses = dict()
            responses['200'] = self._get_response_200()

            openapi_path['responses'] = responses

        def get_openapi_path(self) -> Dict[str, Any]:
            openapi_path = dict()
            openapi_path[self.path] = {}
            openapi_path[self.path][self.method] = {}
            if self.tags:
                openapi_path[self.path][self.method]['tags'] = list(self.tags)
            self._insert_request_struct(openapi_path[self.path][self.method])
            self._insert_responses_struct(openapi_path[self.path][self.method])
            return openapi_path

    @staticmethod
    def _build_path_and_endpoint_schemas(endpoint: OpenAPIEndpoint) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        cap_name = f'{endpoint.name[0].capitalize()}{endpoint.name[1:]}'
        cap_method = f'{endpoint.method[0].capitalize()}{endpoint.method[1:]}'

        schemas = {}
        if endpoint.request_body:
            schemas.update(endpoint.request_schemas)

        response_schema_ref = f'{cap_method}{cap_name}Response'
        response_schema = OpenAPIDoc.OpenAPIEndpoint.generate_schemas_from_example(response_schema_ref,
                                                                                   endpoint.response_example)
        schemas.update(response_schema)
        return endpoint.get_openapi_path(), schemas

    @classmethod
    def create_from_postman_doc(cls,
                                openapi_doc: PostmanAPIDoc):
        return cls(openapi_doc.name,
                   [OpenAPIDoc.OpenAPIEndpoint(name=endpoint.name,
                                               path=endpoint.path,
                                               method=endpoint.method,
                                               tags=endpoint.tags,
                                               request_query_params=endpoint.request_query_params,
                                               request_path_params=endpoint.request_path_params,
                                               request_body=endpoint.request_body,
                                               response_example=endpoint.response_example) for endpoint in
                    openapi_doc.endpoints])

    def to_yaml(self, file_path: Path):
        openapi_doc = {
            "openapi": "3.0.2",
            "info": {
                "title": self.name,
                "version": "0.5.0"
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        for endpoint in self.endpoints:
            path, endpoint_schemas = OpenAPIDoc._build_path_and_endpoint_schemas(endpoint)
            if endpoint.path in openapi_doc["paths"]:
                openapi_doc["paths"][endpoint.path].update(path[endpoint.path])
            else:
                openapi_doc['paths'].update(path)
            openapi_doc['components']['schemas'].update(endpoint_schemas)

        with open(file_path, 'w') as f:
            f.write(yaml.dump(openapi_doc, sort_keys=False))
