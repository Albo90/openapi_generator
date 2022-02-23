from pathlib import Path

from utils.openapidoc import OpenAPIDoc
from utils.postmanapidoc import PostmanAPIDoc

import argparse

parser = argparse.ArgumentParser(prog='openapi_generator',
                                    description='Generate in a simple way your openapi doc',
                                    allow_abbrev=False)

parser.add_argument('--postman-collection',
                       '-pc',
                       type=str,
                       help='Postman collection path',
                       required=True)

parser.add_argument('--postman-environment',
                       '-pe',
                       type=str,
                       help='Postman environment path')

parser.add_argument('--output',
                       '-o',
                       type=str,
                       help='Path for generated openapi doc',
                       required=True)


args = parser.parse_args()
postman_collection_path = args.postman_collection
postman_environment_path = args.postman_environment
openapi_path = args.output

print(postman_environment_path, postman_collection_path, openapi_path)

postman_doc = PostmanAPIDoc.factory(postman_collection_path, postman_environment_path)
openapi_doc = OpenAPIDoc.create_from_postman_doc(postman_doc)

openapi_doc.to_yaml(openapi_path)