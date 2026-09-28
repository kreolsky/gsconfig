# API Reference

This section provides a detailed description of the API for the main classes of the GSConfig library.

## GoogleOauth

Class for authentication in the Google API.

```python
class GoogleOauth():
    def __init__(self, keyfile=None) -> None:
        """
        Initialize authentication object.
        
        :param keyfile: Path to the service account key file. If None, 
                       interactive OAuth authentication is used.
        """
        
    @property
    @lru_cache(maxsize=1)
    def client(self):
        """
        Returns an authorized gspread client.
        The result is cached for reuse.
        
        :return: gspread.Client object
        """
```

## Page

Class for working with a Google Sheets worksheet.

```python
class Page(object):
    def __init__(self, worksheet):
        """
        Initialize Page object.
        
        :param worksheet: gspread.Worksheet object
        """
        
    @property
    def title(self):
        """
        Returns the original page name in the spreadsheet.
        
        :return: String with page name
        """
        
    @property
    def name(self):
        """
        Returns page name without extension.
        
        :return: String with page name without extension
        """
        
    @property
    def format(self):
        """
        Returns page format based on extension in the name.
        
        :return: String with format ('json', 'csv', 'raw')
        """
        
    def set_key_skip_letters(self, key_skip_letters):
        """
        Sets symbols for skipping keys.
        
        :param key_skip_letters: List or set of symbols
        """
        
    def set_parser_version(self, parser_version):
        """
        Sets parser version ('v1' or 'v2').
        
        :param parser_version: String with parser version
        """
        
    def set_schema(self, schema):
        """
        Sets data schema.
        
        :param schema: Tuple ('key', 'data') or dictionary {'key': 'key', 'data': ['value1', 'value2']}
        """
        
    def set_format(self, format='json'):
        """
        Forcibly sets format for the page.
        
        :param format: String with format ('json', 'csv', 'raw')
        """
        
    def set_raw_mode(self):
        """
        Sets a mode where data is not parsed.
        """
        
    def get(self, **params):
        """
        Returns page data according to format and schema.
        
        :param params: Additional parameters for the parser
        :return: Data in format corresponding to page settings
        """
        
    def save(self, path=''):
        """
        Saves page data to a file.
        
        :param path: Path for saving
        """
```

## Document

Class for working with a Google Sheets document.

```python
class Document(object):
    def __init__(self, spreadsheet):
        """
        Initialize Document object.
        
        :param spreadsheet: gspread.Spreadsheet object
        """
        
    def __getitem__(self, title):
        """
        Returns page by name.
        
        :param title: Page name
        :return: Page object
        """
        
    def __iter__(self):
        """
        Iterator through main document pages 
        (not starting with symbols in page_skip_letters).
        
        :yield: Page objects
        """
        
    @property
    def title(self):
        """
        Returns document name.
        
        :return: String with document name
        """
        
    @property
    def page1(self):
        """
        Returns the first main document page.
        
        :return: Page object
        """
        
    @property
    def pages(self):
        """
        Iterator through all document pages, including service ones.
        
        :yield: Page objects
        """
        
    def set_page_skip_letters(self, page_skip_letters):
        """
        Sets symbols for skipping pages.
        
        :param page_skip_letters: List or set of symbols
        """
        
    def set_key_skip_letters(self, key_skip_letters):
        """
        Sets symbols for skipping keys.
        
        :param key_skip_letters: List or set of symbols
        """
        
    def set_parser_version(self, parser_version):
        """
        Sets parser version ('v1' or 'v2').
        
        :param parser_version: String with parser version
        """
        
    def save(self, path='', mode=''):
        """
        Saves all main document pages.
        
        :param path: Path for saving
        :param mode: Save mode ('full' to save all pages)
        """
```

## GameConfigLite

Class for working with a game configuration from a single document.

```python
class GameConfigLite(Document):
    def __init__(self, spreadsheet_id: str, client=None, params: dict = {}):
        """
        Initialize game configuration.
        
        :param spreadsheet_id: Google Sheets ID
        :param client: GoogleOauth authentication client
        :param params: Additional configuration parameters
        """
        
    @property
    @lru_cache(maxsize=1)
    def spreadsheet(self) -> gspread.Spreadsheet:
        """
        Returns gspread.Spreadsheet object.
        The result is cached for reuse.
        
        :return: gspread.Spreadsheet object
        """
```

## GameConfig

Class for working with a game configuration from multiple documents.

```python
class GameConfig(object):
    def __init__(self, spreadsheet_ids: list, client: GoogleOauth, params: dict = {}):
        """
        Initialize game configuration.
        
        :param spreadsheet_ids: List of Google Sheets IDs
        :param client: GoogleOauth authentication client
        :param params: Additional configuration parameters
        """
        
    @property
    @lru_cache(maxsize=1)
    def documents(self) -> list:
        """
        Returns a list of Document objects for all documents.
        The result is cached for reuse.
        
        :return: List of Document objects
        """
        
    def __iter__(self):
        """
        Iterator through configuration documents.
        
        :yield: Document objects
        """
        
    def __getitem__(self, title):
        """
        Returns document by name.
        
        :param title: Document name
        :return: Document object
        :raises KeyError: If document not found
        """
        
    def set_parser_version(self, parser_version):
        """
        Sets parser version ('v1' or 'v2').
        
        :param parser_version: String with parser version
        """
        
    def save(self, path='', mode=''):
        """
        Saves all configuration documents.
        
        :param path: Path for saving
        :param mode: Save mode ('full' to save all pages)
        """
```

## ConfigJSONConverter

Class for converting the intermediate format to JSON.

```python
class ConfigJSONConverter:
    AVAILABLE_VESRIONS = ('v1', 'v2')
    
    def __init__(self, params={}):
        """
        Initialize converter.
        
        :param params: Converter parameters
        """
        
    def jsonify(self, string: str, is_raw: bool = False) -> dict | list:
        """
        Converts a string in the intermediate format to Python data structures.
        
        :param string: String in intermediate format
        :param is_raw: If True, the string will not be converted
        :return: Dictionary or list with data
        """
```

## Template

Class for working with templates.

```python
class Template(object):
    def __init__(self, path='', body='', pattern=None, strip=True, jsonify=False):
        """
        Initialize template.
        
        :param path: Path to template file
        :param body: Template as a string (alternative to path)
        :param pattern: Pattern for finding variables in the template
        :param strip: Whether to trim quotes from strings during substitution
        :param jsonify: Whether to convert the result to a JSON object
        """
        
    @property
    def title(self) -> str:
        """
        Returns template file name.
        
        :return: String with template name
        """
        
    @property
    def keys(self) -> list:
        """
        Returns a list of keys used in the template.
        
        :return: List of strings with keys
        """
        
    @property
    def body(self) -> str:
        """
        Returns template body.
        
        :return: String with template body
        """
        
    def set_path(self, path=''):
        """
        Sets path to template file.
        
        :param path: Path to template file
        """
        
    def set_body(self, body=''):
        """
        Sets template body.
        
        :param body: Template as a string
        """
        
    def render(self, balance: dict):
        """
        Fills template with data.
        
        :param balance: Dictionary with data for substitution
        :return: Filled template as a string or data structure
        """
        
    # Alias for render method
    make = render
```

## Extractor

Class for extracting data from Google Sheets pages.

```python
class Extractor:
    def __init__(self):
        """
        Initialize extractor.
        """
        
    def get(self, page_data, format='json', **params):
        """
        Extracts data in the specified format.
        
        :param page_data: Two-dimensional data array (list of lists)
        :param format: Data format ('json', 'csv', 'raw')
        :param params: Additional parameters for the parser
        :return: Data in the specified format
        """
```

## tools

Module with utilities for working with data.

```python
def save_page(page, path=''):
    """
    Saves page to the specified path.
    
    :param page: Page object
    :param path: Path for saving object
    """
    
def save_csv(data, title, path=''):
    """
    Saves data in CSV format.
    
    :param data: Two-dimensional data array (list of lists)
    :param title: File name
    :param path: Path for saving
    """
    
def save_json(data, title, path=''):
    """
    Saves data in JSON format.
    
    :param data: Data for saving
    :param title: File name
    :param path: Path for saving
    """
    
def save_raw(data, title, path=''):
    """
    Saves data in raw format.
    
    :param data: Data for saving
    :param title: File name
    :param path: Path for saving
    """
    
def dict_to_str(source, tab='', count=0):
    """
    Converts dictionary to formatted string.
    
    :param source: Source dictionary
    :param tab: Tab character
    :param count: Initial nesting level
    :return: String with dictionary representation
    """
    
def load_json(filename, path=''):
    """
    Loads data from JSON file.
    
    :param filename: File name
    :param path: Path to file
    :return: Loaded data
    """
```