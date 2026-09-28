# Data Extraction and Schemas

GSConfig provides flexible mechanisms for extracting data from spreadsheets, taking into account various data organization schemas and formats.

## Extractor

`Extractor` is a class responsible for extracting and parsing data from Google Sheets pages. It interprets the data structure on the page and converts it into a convenient format for use in Python.

```python
class Extractor:
    def __init__(self):
        # Set of extractors for different formats
        self.extractors = {
            'json': self._extract_json,
            'csv': self._extract_dummy,
            'raw': self._extract_dummy
        }
```

The extractor analyzes page data and applies the corresponding extraction method depending on the format. The main method for retrieving data:

```python
def get(self, page_data, format='json', **params):
    """
    Extracts data in the specified format.

    :param page_data: two-dimensional array (list of lists)
    :param format: data format ('json', 'csv', 'raw')
    :param params: additional parameters for the parser
    :return: filtered and converted data
    """
```

## Data Schemas

GSConfig supports various data organization schemas in spreadsheets. It's important to understand that the choice of schema depends on your data structure and parameters specified in the code.

### How Schema Selection Works

In the `Extractor` class, the logic for schema selection works as follows:

```python
# Simplified version of code from Extractor._extract_json
def _extract_json(self, page_data, **params):
    # Get parameters
    schema = params.get('schema')
    
    # Parse data according to complex schema
    if isinstance(schema, dict):
        return self._parse_complex_schema(page_data, parser, schema)
    
    # Parse according to simple schema
    if isinstance(schema, tuple) and all(x in page_data[0] for x in schema):
        return self._parse_simple_schema(page_data, parser, schema)
    
    # Processing in free format when there is no schema or required columns not found
    return self._parse_free_format(page_data, parser, key_skip_letters)
```

That is:
1. If the schema is defined as a dictionary, the complex schema is used
2. If the schema is defined as a tuple AND all elements of the tuple exist in the page headers, the simple schema is used
3. In other cases (schema not defined or required columns not found), free format is used

By default, in the `Page` class, the schema is set as `('key', 'data')`. This means that if there are columns named "key" and "data" in the page headers, the simple schema will be used. If such columns do not exist, the free format is automatically used.

### 1. Simple Schema (default)

Data is stored in two columns: key and value. The result is presented as a dictionary of key-value pairs.

Example data in the table:
```
key                | data
-------------------|------------------------------------
name               | Sheep
health             | 100
speed              | 1.5
stats              | {health = 100, speed = 1.5}
```

Code for data extraction:
```python
# Setting a simple schema
page.set_schema(('key', 'data'))
mob_data = page.get()

print(mob_data)
```

Result (JSON):
```json
{
  "name": "Sheep",
  "health": 100,
  "speed": 1.5,
  "stats": {
    "health": 100,
    "speed": 1.5
  }
}
```

### 2. Complex Schema

Data is organized with column headers. Each data column forms a separate dictionary in the result. You can specify a default column that is used if data in other columns is missing.

Example data in a table with missing values and specifying the value_1 column as the default value for the complex schema:
```
key                | value_1           | value_2
-------------------|-------------------|-------------------
name               | Sheep             | SheepFat
health             | 100               | 150
speed              | 1.5               | 
attack             |                   | 20
stats              | {health = 100}    | {health = 150}
```

Code for data extraction:
```python
# Setting a complex schema
page.set_schema({
    'key': 'key',  # Column name with keys
    'data': ['value_1', 'value_2'],  # List of columns with data
    'default': 'value_1'  # Default column
})
animals_data = page.get()

print(animals_data)
```

Result (JSON) using the default column:
```json
{
  "value_1": {
    "name": "Sheep",
    "health": 100,
    "speed": 1.5,
    "attack": "",  // Empty string since the value is missing in value_1
    "stats": {
      "health": 100
    }
  },
  "value_2": {
    "name": "SheepFat",
    "health": 150,
    "speed": 1.5,  // Taken from value_1 (default column)
    "attack": 20,
    "stats": {
      "health": 150
    }
  }
}
```

As seen in the example:
- When value is missing for the "speed" key in the value_2 column, the value from the value_1 column (default column) is used
- When value is missing for the "attack" key in the value_1 column, an empty string is left

### 3. Free Format

If no schema is specified or the data doesn't have columns matching the specified schema, the data is interpreted in a free format, where the first row contains headers and subsequent rows contain data. The result is presented as a list of dictionaries, where each dictionary corresponds to one row of data.

Example data in the table:
```
name       | health | speed | drops
-----------|--------|-------|---------------------------
Sheep      | 100    | 1.5   | {wool = 3, meat = 2}
Pig        | 120    | 1.2   | {meat = 4, leather = 1}
Cow        | 150    | 1.0   | {meat = 5, leather = 2}
```

Code for data extraction:
```python
# Free format doesn't require schema setting
# You can also explicitly disable the schema by setting None
page.set_schema(None)
mobs_data = page.get()

print(mobs_data)
```

Result (JSON):
```json
[
  {
    "name": "Sheep",
    "health": 100,
    "speed": 1.5,
    "drops": {
      "wool": 3,
      "meat": 2
    }
  },
  {
    "name": "Pig",
    "health": 120,
    "speed": 1.2,
    "drops": {
      "meat": 4,
      "leather": 1
    }
  },
  {
    "name": "Cow",
    "health": 150,
    "speed": 1.0,
    "drops": {
      "meat": 5,
      "leather": 2
    }
  }
]
```

## Data Filtering

GSConfig provides several ways to filter data during extraction.

### Skipping Pages

To skip certain pages when iterating through a document, use `page_skip_letters`:

```python
# Pages starting with '#' or '.' will be skipped
config = gsconfig.GameConfigLite(document_id, client)
config.set_page_skip_letters({'#', '.'})

# Now when iterating, pages like '#debug' or '.calculations' will be skipped
for page in config:
    print(page.title)  # Won't output pages starting with '#' or '.'
```

### Skipping Keys

To skip certain keys when extracting data, use `key_skip_letters`:

```python
# Keys starting with '#' or '.' will be skipped during data extraction
page = config['settings.json']
page.set_key_skip_letters({'#', '.'})

data = page.get()
# Keys like '#debug_mode' or '.internal_counter' won't be included in the result
```

This functionality is especially useful for adding comments or technical data to the table:

```
key              | data
-----------------|------------------
name             | Sheep
health           | 100
#debug_note      | Increase in next version
.internal_id     | MOB_001
speed            | 1.5
```

The result will only include `name`, `health`, and `speed`.

## Page Formats

The page format is determined by the extension in its name. GSConfig supports the following formats:

### json

Data is extracted and converted to Python structures using a parser. This format allows working with nested data structures.

```
Page name: mobs.json
```

### csv

Data is returned as a two-dimensional array without parsing. This format is convenient for tabular data without nested structures.

```
Page name: items.csv
```

### raw

Data is returned as a two-dimensional array without any processing. Useful for debugging or when you need the source data.

```
Page name: debug.raw
```

### Forced Format Specification

You can also force a format for the page:

```python
page.set_format('json')  # or 'csv', 'raw'
```

If no format is specified in the page name and not set explicitly, 'raw' is used by default.