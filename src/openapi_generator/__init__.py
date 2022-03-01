import argparse

from openapi_generator.core.openapidoc import OpenAPIDoc
from openapi_generator.core.postmanapidoc import PostmanAPIDoc


def main():
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

    postman_doc = PostmanAPIDoc.factory(postman_collection_path, postman_environment_path)
    openapi_doc = OpenAPIDoc.create_from_postman_doc(postman_doc)

    openapi_doc.to_yaml(openapi_path)