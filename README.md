## OPENAPI DOCUMENT GENERATOR

This program is a simple cli command to generate from a Postman collection the OpenAPI 
document

### PREREQUIREMENTS

- Python 3.9
- virtualenv

### BUILD

```
pip install build
```
<br>
launch command from the root of project

```
python -m build
```
<br>
install package in your enviroment

```
pip install path-to-dist-file
```


### USAGE

`openapi_generator -pc 'postman collection path' -pe 'postman environment path' -o 'openapi doc path'`

---

#### NOTES
1. Postman collection folders will become tags for the endpoint
2. Path params have to be variables in a environment
3. Response structure will be built from a real call to the service, so we recommend you to use on development API
4. OpenAPI schemas are composed by method - postman endpoint name - response / request
