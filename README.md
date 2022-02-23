## OPENAPI DOCUMENT GENERATOR

This program is a simple cli command to generate from a Postman collection the OpenAPI 
document

### PREREQUIREMENTS

- Python 3.9
- virtualenv

### INSTALLATION

```
pip install virtualenv
python -m virtualenv venv
```
activate venv and launch
```
pip install -r requirements.txt
```

### USAGE

`python openapi_generator.py -pc 'postman collection path' -pe 'postman environment path' -o 'openapi doc path'`

---

#### NOTES
1. Postman collection folders will become tags for the endpoint
2. Path params have to be variables in a environment
3. Response structure will be built from a real call to the service, so we recommend you to use on development API
4. OpenAPI schemas are composed by method - postman endpoint name - response / request
