# Intermediate Format and Conversion

One of the key features of GSConfig is the conversion of data from an "intermediate format," which is convenient for filling in Google Sheets, to structured JSON used in game systems.

## Data Format

The intermediate format was specifically designed to solve problems faced by game designers when working with game configurations. When a game has hundreds or thousands of entities with various parameters (items, abilities, enemies, etc.), manually editing JSON files becomes extremely labor-intensive, especially when mass changes need to be made.

### Main Features

The intermediate format is a simplified version of JSON with a more flexible syntax that is easier to fill in tables. Unlike standard JSON, it uses only one type of brackets for data blocks `{}`, and the type of content (dictionary or list) is automatically determined based on the content of the block.

Features of this format:

- **Simplified syntax** - fewer brackets and quotes, which reduces the likelihood of errors during manual input
- **Flexible separators** - ability to customize block and element separation symbols
- **Automatic type detection** - numbers and boolean values are converted automatically
- **Support for nested structures** - ability to create multi-level data hierarchies
- **Ease of compilation in tables** - optimized for use in Google Sheets
- **Human readability** - the format is designed to be easy for humans to write and read

### Value Lists

The simplest type of data in the intermediate format is a list of values. They represent an enumeration of elements separated by commas inside curly braces:

```
{wool, meat, bone}
```

This entry is converted to JSON:
```json
[
  "wool",
  "meat",
  "bone"
]
```

Lists can contain numbers, strings, and even lists. Any nesting is allowed:

```
{10, 15, 20, sword_01, sword_02, sword_03, {4, 6, 8}}
```

Will be converted to JSON:

```json
[
  10,
  15,
  20,
  "sword_01",
  "sword_02",
  "sword_03",
  [
    4,
    6,
    8
  ]
]
```

### Dictionaries (Objects)

If there is a key-value separator `=` inside a block, then the block is interpreted as a dictionary:

```
# Simple dictionary notation
stats = {health = 100, speed = 1.5, strength = 25}
```

In v1 version, dictionaries are always wrapped in a list. This is done deliberately, as game configurations often require working with lists of objects (for example, prices for different currencies or lists of required resources):

```json
{
  "stats": [
    {
      "health": 100,
      "speed": 1.5,
      "strength": 25
    }
  ]
}
```

In v2 version, dictionaries are not wrapped automatically:

```json
{
  "stats": {
    "health": 100,
    "speed": 1.5,
    "strength": 25
  }
}
```

For v2, commands for fine-grained control of data types are supported.

### Mixed Structures

Any mix of blocks inside is possible. For example:

```
# Game item entry with nested structures
item = {
  name = Sword of Truth, 
  type = weapon, 
  stats = {damage = 50, speed = 1.2}, 
  price = {gold = 100, gems = 2}, 
  drop_sources = {Dragon, Chest, Shop}
}
```

Converts to JSON (v1):
```json
{
  "item": [
    {
      "name": "Sword of Truth",
      "type": "weapon",
      "stats": [
        {
          "damage": 50,
          "speed": 1.2
        }
      ],
      "price": [
        {
          "gold": 100,
          "gems": 2
        }
      ],
      "drop_sources": [
        "Dragon",
        "Chest",
        "Shop"
      ]
    }
  ]
}
```

Within a single block, you can mix list elements and key-value pairs. In this case, the parsing algorithm will automatically separate them:

```
# Mixed data in one block
9.1, 6.0, 6 | 7 = 7, zero = 0, one, two = {2 = dva}, tree = {2 = dva | 3 = tree} | a, b, f
```

Converts to JSON (v2):
```json
[
  [
    9.1,
    6.0,
    6
  ],
  [
    "one",
    {
      "7": 7,
      "zero": 0,
      "two": {
        "2": "dva"
      },
      "tree": [
        {
          "2": "dva"
        },
        {
          "3": "tree"
        }
      ]
    }
  ],
  [
    "a",
    "b",
    "f"
  ]
]
```

### Syntactic Sugar

To simplify the notation of complex nested structures, the format supports a special block separator `|`, which acts as syntactic sugar:

```
# Simplified notation with block separator
0, 6| 7 = 7, zr = 0, one, tw = {2 = d}, tv = {2 = dv | 3 = tr} | a, b
```

This notation is equivalent to the more complex structure:
```
{0, 6}, {7 = 7, zr = 0, one, tw = {2 = d}, tv = {{2 = dv}, {3 = tr}}}, {a, b}
```

This approach significantly simplifies the game designer's work, allowing them to quickly create and edit configurations directly in Google Sheets, avoiding complexities with JSON syntax and minimizing the likelihood of errors.

## ConfigJSONConverter

`ConfigJSONConverter` is the class responsible for converting the intermediate format to JSON. It analyzes strings in the intermediate format and creates corresponding Python data structures (dictionaries, lists, values).

```python
class ConfigJSONConverter:
    def __init__(self, params={}):
        self.default_params = {
            'br_list': '[]',
            'br_block': '{}',
            'sep_func': '!',
            'sep_block': '|',
            'sep_base': ',',
            'sep_dict': '=',
            'raw_pattern': '"',
            'to_num': True,
            'parser_version': 'v1',
            'is_raw': False
        }
        self.params = {**self.default_params, **params}
        self.parser = BlockParser(self.params)

    def jsonify(self, string: str, is_raw: bool = False) -> dict | list:
        """
        Method that converts a config string to JSON
        - string -- source string for conversion
        - is_raw -- if True, the string will not be converted and is returned as is
        """
```

## Converter Parameters

When creating `ConfigJSONConverter`, you can set various parameters to change the converter's behavior:

```python
params = {
    'br_list': '[]',  # Type of brackets for lists
    'br_block': '{}',  # Type of brackets for blocks
    'sep_func': '!',  # Separator for functions
    'sep_block': '|',  # Block separator
    'sep_base': ',',  # Base element separator
    'sep_dict': '=',  # Key-value separator
    'raw_pattern': '"',  # Symbol for raw strings
    'to_num': True,  # Whether to convert strings to numbers
    'parser_version': 'v2',  # Parser version
    'is_raw': False  # Whether to parse the string
}

converter = gsconfig.ConfigJSONConverter(params)
```

**Important!** It is not recommended to change the default value of `br_list` as this can lead to parsing errors.

## Converter Versions

GSConfig has two converter versions which differ in how they handle dictionaries:

### v1 (default)
- All dictionaries are always wrapped in a list
- Example: `five = {three = 3, two = 2}` becomes `{"five": [{"three": 3, "two": 2}]}`

### v2
- Unwraps lists of single length
- To wrap in a list, you need to explicitly specify the `!list` command or use the syntactic sugar `[]`
- Example: `five = {three = 3, two = 2}` becomes `{"five": {"three": 3, "two": 2}}`
- Example with explicit wrapping: `five!list = {three = 3, two = 2}` or `five[] = {three = 3, two = 2}`

## v2 Converter Commands

In the intermediate format, you can use special commands to control data conversion. They are added after the key name through a separator (default '!'):

```
Command   | Description                                  | Example Usage             | Result
----------|----------------------------------------------|---------------------------|--------------------------------
list      | Wraps the value in a list,                   | key!list = value          | {"key": ["value"]}
          | if it's not already a list                   |                           |
dlist     | Wraps only dictionaries in a list            | key!dlist = {a = 1}       | {"key": [{"a": 1}]}
flist     | Always wraps in an additional list           | key!flist = [1, 2]        | {"key": [[1, 2]]}
string    | Converts the value to a string               | key!string = 123          | {"key": "123"}
int       | Converts the value to an integer             | key!int = 10.9            | {"key": 10}
float     | Converts the value to a floating-point number| key!float = 10            | {"key": 10.0}
json      | Converts the value to a JSON string          | key!json = {a = 1}        | {"key": "{\"a\":1}"}
```

### Short Commands (Syntactic Sugar)

For convenience, you can use a short syntax for commands, adding certain symbols to the end of a key name:

```
Symbols | Equivalent Command | Example           | Result
--------|-------------------|-------------------|---------------------------
[]      | dlist             | key[] = {a = 1}   | {"key": [{"a": 1}]}
()      | list              | key() = value     | {"key": ["value"]}
{}      | flist             | key{} = [1, 2]    | {"key": [[1, 2]]}
```

## Special Value Processing

The converter automatically recognizes certain string values:

```
String                | Converts to
----------------------|------------------
none, nan, null       | null (None in Python)
true                  | true (True in Python)
false                 | false (False in Python)
```

## Converter Usage Examples

### Example 1: Simple Dictionary

```python
string = 'name = Sheep, health = 100, speed = 1.5'
result = converter.jsonify(string)
# Result: {"name": "Sheep", "health": 100, "speed": 1.5}
```

### Example 2: Nested Structures (v1)

```python
string = 'stats = {health = 100, speed = 1.5}, drops = {wool = 3, meat = 2}'
result = converter.jsonify(string)
# Result: {"stats": [{"health": 100, "speed": 1.5}], "drops": [{"wool": 3, "meat": 2}]}
```

### Example 3: Nested Structures (v2)

```python
# Setting version v2
params['parser_version'] = 'v2'
converter = ConfigJSONConverter(params)

string = 'stats = {health = 100, speed = 1.5}, drops[] = {wool = 3, meat = 2}'
result = converter.jsonify(string)
# Result: {"stats": {"health": 100, "speed": 1.5}, "drops": [{"wool": 3, "meat": 2}]}
```

### Example 4: Emulating v1 in v2

```python
# Setting version v2
params['parser_version'] = 'v2'
converter = ConfigJSONConverter(params)

string = 'stats[] = {health = 100, speed = 1.5}, drops[] = {wool = 3, meat = 2}'
result = converter.jsonify(string)
# Result: {"stats": [{"health": 100, "speed": 1.5}], "drops": [{"wool": 3, "meat": 2}]}
```

### Example 5: Processing Raw Strings

```python
string = '"<color=#6aefff>New round</color> has | begun"'
result = converter.jsonify(string)
# Result: "<color=#6aefff>New round</color> has | begun"
```