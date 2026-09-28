# Core Abstractions

The GSConfig library is built on four main abstractions, which are organized in a hierarchy from high-level to low-level components.

## GameConfig

`GameConfig` is the highest-level class that manages a set of Google Sheets documents that form a complete game configuration. This class is suitable for complex game projects where data is distributed across multiple tables.

```python
class GameConfig(object):
    def __init__(self, spreadsheet_ids: list, client: GoogleOauth, params: dict = {}):
        """
        Initialization of game configuration

        :param spreadsheet_ids: List of Google Sheets IDs
        :param client: GoogleOauth authentication client
        :param params: Additional configuration parameters
        """
```

Key features:
- Manages multiple game configuration documents
- Loads documents in parallel for improved performance
- Provides a unified interface for accessing all data
- Supports iteration over all documents
- Allows access to documents by their names

Usage example:
```python
import gsconfig

# List of Google Sheets document IDs
document_ids = [
    '1a5326Sg3LYhzRGACp160zEdcvKirXMl5avP2USIq2PE',
    '1dbmmds9IIAqT2rDxXSPLm8g6VhEorS5_8_fvd6A22rs'
]

# Creating a client and config
client = gsconfig.GoogleOauth().client
config = gsconfig.GameConfig(document_ids, client)

# Accessing a document by name
tables_doc = config['tables']

# Iterating through all documents
for document in config:
    print(document.title)
```

## GameConfigLite

`GameConfigLite` is a simplified version of `GameConfig` that works with a single Google Sheets document. This class is ideal for small projects or when the entire game config is contained in one spreadsheet.

```python
class GameConfigLite(Document):
    def __init__(self, spreadsheet_id: str, client=None, params: dict = {}):
        """
        Initialization of game configuration

        :param spreadsheet_id: Google Sheets ID
        :param client: GoogleOauth authentication client
        :param params: Additional configuration parameters
        """
```

Key features:
- Works with a single config document
- Inherits from the Document class, extending its functionality
- Simplified interface for small projects
- Access to pages by their names

Usage example:
```python
import gsconfig

# Google Sheets document ID
document_id = "1H8vkzaZZVOgtYrtWHm792FGWaSBhJZNiB0ckco_XXXX"

# Creating a client and config
client = gsconfig.GoogleOauth().client
config = gsconfig.GameConfigLite(document_id, client)

# Accessing a page by name
mobs_page = config['mobs.json']

# Getting data
mobs_data = mobs_page.get()

# Saving data
mobs_page.save('json')
```

## Document

`Document` is a wrapper around `gspread.Spreadsheet` that provides additional methods for working with the spreadsheet as a game configuration document.

```python
class Document(object):
    def __init__(self, spreadsheet):
        self.spreadsheet = spreadsheet  # Source gspread.Spreadsheet object
        self.page_skip_letters = set()
        self.key_skip_letters = set()
        self.parser_version = None
```

Key features:
- Access to document pages by their names
- Filtering pages by prefixes (ability to exclude service pages)
- Filtering keys by prefixes (ability to exclude comments)
- Setting the parser version
- Iteration over document pages

Usage example:
```python
import gsconfig

# Creating a client
client = gsconfig.GoogleOauth().client

# Opening a document by ID
spreadsheet = client.open_by_key("1H8vkzaZZVOgtYrtWHm792FGWaSBhJZNiB0ckco_RGp0")

# Creating a Document object
document = gsconfig.Document(spreadsheet)

# Setting prefixes for skipping pages and keys
document.set_page_skip_letters(['#', '.'])
document.set_key_skip_letters(['#', '.'])

# Setting parser version
document.set_parser_version('v2')

# Getting a page by name
page = document['mobs.json']

# Iterating through all main pages (not starting with # or .)
for page in document:
    print(page.title)

# Iterating through all pages, including service pages
for page in document.pages:
    print(page.title)
```

## Page

`Page` is the lowest-level class of the main abstractions, representing a wrapper around `gspread.Worksheet`. This class provides methods for extracting and converting data from a spreadsheet sheet.

```python
class Page(object):
    def __init__(self, worksheet):
        self.worksheet = worksheet  # Source gspread.Worksheet object
        self.key_skip_letters = set()
        self.parser_version = None
        self.schema = ('key', 'data')  # Schema for storing data in two columns
        self.is_raw = False  # By default will always parse data when saving to json 
        self._format = None
        self._cache = None
        self._name_and_format = None
        self._extractor = Extractor()
```

Key features:
- Extracting data from a spreadsheet sheet in various formats (JSON, CSV, RAW)
- Caching data for performance optimization
- Converting data using parser and schema
- Determining format by extension in page name
- Saving data to files

Usage example:
```python
import gsconfig

# Creating a client
client = gsconfig.GoogleOauth().client

# Opening a document and getting a sheet
spreadsheet = client.open_by_key("1H8vkzaZZVOgtYrtWHm792FGWaSBhJZNiB0ckco_XXXX")
worksheet = spreadsheet.worksheet("mobs.json")

# Creating a Page object
page = gsconfig.Page(worksheet)

# Setting data schema
page.set_schema(('key', 'data'))

# Setting parser version
page.set_parser_version('v2')

# Getting data
data = page.get()

# Saving data
page.save('json')
```

See details on retrieving data from Google Sheets in the [Data Extraction](04-Data_Extraction.md) section