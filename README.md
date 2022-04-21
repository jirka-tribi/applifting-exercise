# Applifting Exercise

Simple app for handling users, product and their offers with prices

Also, every minute get new price and items in stock of each product from offers service


## API endpoints with prefix `/api/v1`

## Administration endpoints

### /register
store new user with hashed password into database and return jwt token  
method: POST  
json data: `{"username": string with length from 3 to 100 chars, "password": string with length from 10 to 100 chars}`   
return: `{"token": encoded_jwt_token}`

### /login
verify user and password and generate jwt token used for auth of products endpoints  
method: POST  
json data: `{"username": string with length from 3 to 100 chars, "password": string with length from 10 to 100 chars}`    
return: `{"token": encoded_jwt_token}`

## Products endpoints

### /products
create and store new product into database and register it into offers service  
required `Authorization: Bearer %encoded_jwt_token%` header -> encoded_jwt_token from register or login endpoint  
method: POST  
json_data: `{"name": string with length from 3 to 100 chars, "description": string}`  
return: `{"id": product_id}`  

### /products/{product_id}
return product of given product_id  
method: GET  
return: `{"id": int, "name": string, "description": string}`

### /products/{product_id}
update product of given product_id  
required `Authorization: Bearer %encoded_jwt_token%` header -> encoded_jwt_token from register or login endpoint  
method: PUT  

### /products/{product_id}
delete product of given product_id  
required `Authorization: Bearer %encoded_jwt_token%` header -> encoded_jwt_token from register or login endpoint  
method: DELETE

### /products/{product_id}/offers
get the latest offers of given product_id  
method: GET  
return: `{"offers": [{"id": int, "price": int, "items_in_stock": int}]}`

### /products/{product_id}/offers_all
get all stored offers of given product_id  
method: GET  
return: `{"offers": [{"id": int, "price": int, "items_in_stock": int}]}`

### /products/{product_id}/prices
get all prices of given product_id between dates from input data  
return also computed rise/fall in percentage  
method: GET  
return: `{"prices": [int], "percentage": int}`

## Status endpoint without prefix

### /status
Return code 200 when app is alive and connected to database else 500  
method: GET


## Deployment
For quick deployment app it is possible use docker compose command
```bash
docker compose --env-file .env up
```

Required fields in .env file:  
`APP_INTERNAL_TOKEN` - Secret password used for encoding and decoding jwt token  
`POSTGRES_DBNAME`  
`POSTGRES_USERNAME`  
`POSTGRES_PASSWORD`  

Optional fields in .env file:  
`OFFERS_SERVICES_URL` - Url of offers service

## Development
App is development in python 3.8 and use Poetry for managing app dependencies

Install poetry
```bash
pip install poetry
```
Install App
```bash
poetry install
```

## Tests
App is covered with E2E tests and with pylint and mypy coding styles  
Also html with coverage report is generated  
Could be start with poetry
```bash
poetry run pytest
```
