## Introduction

This system serves for the purpose of making an item catalog. 
All items are categories in categories, for easier filtering and finding of items.
Everything is defined in the database and the website will dynamically update when
the database is updated. 

Adding/editing categories or items can be done by logging into the system.

## Requirements

- Python 3 with PIP
- A SQL database 

## Installment and running

- Install the requirements from the `requirements.txt` file.
- Rename `config.py.example` to `config.py` and setup the config file. ([Check Config section](#Configuration))
- Run the python file with `python udacity_item_catalog.py`.

## Configuration
For making the program work some changes needs to be done in the config file.

### SECRET KEY
For generating the secret key run 
```
>>> import os; os.urandom(24)
```
and replace the result with the value in `SECRET_KEY`.

### SQLALCHEMY_DATABASE_URI
Replace the value with your database URI, an example for the url could be
```
mysql://root@localhost:3306/udacity_item_catalog
```

### GOOGLE_OAUTH_CLIENT
Replace `CLIENT_ID` and `CLIENT_SECRET` with your id and secret for Google.

## API

The API consists of 1 endpoint `/items.json`, which returns all items sorted in their categories.
This endpoint will return the data as JSON.

