# Working with Templates

The template system in GSConfig allows you to generate structured configuration files based on data retrieved from Google Sheets. Templates are especially useful when you need to transform data into a specific format for use in game engines.

## Template Class

`Template` is the main class for working with templates. It loads a template from a file and fills it with data using the `render()` method.

```python
class Template(object):
    def __init__(self, path='', body='', pattern=None, strip=True, jsonify=False):
        """
        Template initialization

        :param path: path to template file
        :param body: template as a string (alternative to path)
        :param pattern: pattern for finding variables in the template
        :param strip: whether to trim quotes from strings during substitution
        :param jsonify: whether to convert the result to a JSON object
        """
```

Example usage:

### Template from File

Let's say we have a template `MobSettings.template`:

```json
{
  "_maxHealth": {% health!float %},
  "_botRewards": {% bot_rewards %},
  "RectilinearCowardlyStateSettings": {
    "DelayCaptured": {% captured_delay!int %}
  }
}
```

Code for loading and filling the template:

```python
import gsconfig

# Creating a template from a file
template = gsconfig.Template('templates/MobSettings.template')

# Data for filling the template
data = {
    'health': 100,
    'bot_rewards': {'gold': 10},
    'captured_delay': 2.7  # will be converted to 2 by the int command
}

# Filling the template with data
result = template.render(data)

# Saving the result to a file
gsconfig.tools.save_json(result, 'SheepSettings', 'json')
```

Result:
```json
{
  "_maxHealth": 100.0,
  "_botRewards": {"gold": 10},
  "RectilinearCowardlyStateSettings": {
    "DelayCaptured": 2
  }
}
```

### Template from String

You can also pass a template directly as a string:

```python
import gsconfig

# Template as a string
template_body = """
{
  "name": "{% monster_name %}",
  "stats": {
    "health": {% health!float %}
  }
}
"""

# Creating a template from a string
template = gsconfig.Template(body=template_body, jsonify=True)

# Data for filling the template
data = {
    'monster_name': 'Goblin',
    'health': 50
}

# Filling the template with data and getting the result as JSON
result = template.render(data)
print(result)
```

Result:
```json
{
  "name": "Goblin",
  "stats": {
    "health": 50.0
  }
}
```

## Commands in Template Keys

In templates, you can use commands to transform values during substitution. Commands are specified after the key through the `!` symbol:

```
{key!command}
```

For example:
```
{health!float}
```

### Commands

- **float** - converts a value to a floating-point number
  ```
  {speed!float}  # 10 -> 10.0
  ```
- **int** - converts a value to an integer, discarding the fractional part
  ```
  {health!int}  # 10.9 -> 10
  ```
- **json** - saves a structure as JSON (applies json.dumps())
  ```
  {stats!json}  # {"health": 100} -> "{\"health\": 100}"
  ```
- **list** - wraps a value in a list if it's not already a list
  ```
  {weapon!list}  # "sword" -> ["sword"], [1, 2] remains unchanged
  ```
- **extract** - extracts an element from a list if it's a single-length list
  ```
  {item!extract}  # [{"name": "sword"}] -> {"name": "sword"}
  ```
- **wrap** - wraps in an additional list if the first element is not a list
  ```
  {items!wrap}  # [1, 2, 3] -> [[1, 2, 3]]
  ```
- **string** - forcibly wraps a string in quotes
  ```
  {name!string}  # John -> "John"
  ```
- **get_N** - gets an element from a list by index N
  ```
  {items!get_2}  # ["a", "b", "c"] -> "c"
  ```
- **extract_N** - gets an element from a list by index N (similar to get_N)
  ```
  {items!extract_1}  # ["a", "b", "c"] -> "b"
  ```
- **none** or **null** - returns None for empty strings
  ```
  {empty_value!none}  # "" -> null in JSON
  ```

### Command Chains

Commands can be combined in chains, applying them sequentially:

```
{% characters!get_1!float %}
```

This construction sequentially applies commands from left to right:
1. Gets the first element (`get_1`) from the `items` list
2. Converts the resulting value to (`float`)

Data:

```python
data = {
    'characters': ['knight', 100, 'sword']
}
```

And a template with a command chain:

```json
{
  "warrior_health": {% characters!get_1!float %}
}
```

Step-by-step execution of the command chain:

- Initial value: `['knight', 100, 'sword']`
- `get_1` returns `100`
- `float` converts the obtained value to `100.0`

Result:

```json
{
  "warrior_health": 100.0
}
```

### Custom Commands in Template Keys

See the section [Custom Extensions](07-Custom_Extensions.md)

## Template String Control Commands

Templates support special commands for controlling strings:

### if

Preserves a block between `if` and `endif` if the condition is true (`has_weapon = True`):

```
{% if has_weapon %}
"weapon": {
  "name": "{% weapon_name %}",
  "damage": {% weapon_damage!int %}
},
{% endif %}
```

### foreach

Loop. Repeats a block between `foreach` and `endforeach`.

The `foreach` command iterates through elements in the list specified in the parameter (`drops` in the example below). The reserved variable `$item` is used for iteration through elements, which inside the block is replaced with the current list element.

Template:

```json
{
  "monster": {
    "name": "Dragon",
    "drops": [
    {% foreach drops %}
      {
        "item": "{% $item!get_0 %}"
      }
    {% endforeach %}
    ]
  }
}
```

For the data:
```python
data = {
    'drops': [
        ['sword', 0.5, 1],
        ['shield', 0.3, 1],
        ['potion', 0.7, 2]
    ]
}
```

The result will be:
```json
{
  "monster": {
    "name": "Dragon",
    "drops": [
      {
        "item": "sword"
      },
      {
        "item": "shield"
      },
      {
        "item": "potion"
      }
    ]
  }
}
```

#### Features of Working with the $item Variable:

When a list element is a simple type (string or number), then `$item` is directly replaced with the value of that element
  ```python
  # If drops = ['sword', 'shield', 'potion']
  {% foreach drops %}
    "item_$item",  # Result: "item_sword", "item_shield", "item_potion"
  {% endforeach %}
  ```

For list and dictionary structures, `$item` is replaced with a construction that allows accessing the element through an index
  ```python
  # If drops = [['sword', 0.5, 1], ['shield', 0.3, 1], ['potion', 0.7, 2]]
  {% foreach drops %}
    {
      "item": "{% $item!get_0 %}",  # Access to the first element of the current nested list
      "chance": {% $item!get_1!float %},
      "count": {% $item!get_2!int %}
    }
  {% endforeach %}
  ```

The system automatically removes the last comma in the generated list, which is useful when creating JSON structures

### for

Repeats a block between `for` and `endfor` a specified number of times.

The `for` command executes a loop a specified number of times, determined by the numeric value of the parameter (e.g., `spawn_count`). Inside the block, the reserved variable `$i` is available, which contains the current iteration index.

Template:

```json
{
  "spawn_points": [
  {% for spawn_count %}
    {
      "x": {% spawn_x!get_$i!float %}
    }
  {% endfor %}
  ]
}
```

For the data:
```python
data = {
    'spawn_count': 3,
    'spawn_x': [10.5, 20.3, 15.7]
}
```

The result will be:
```json
{
  "spawn_points": [
    {
      "x": 10.5
    },
    {
      "x": 20.3
    },
    {
      "x": 15.7
    }
  ]
}
```

#### Features of Using the $i Variable:

The `$i` variable takes values from 0 to n-1, where n is the value of the `spawn_count` parameter
  ```
  # If spawn_count = 3
  {% for spawn_count %}
    "position_$i",  # Result: "position_0", "position_1", "position_2"
  {% endfor %}
  ```

The `$i` variable is especially useful for accessing array elements by index:
  ```
  # If spawn_x = [10.5, 20.3, 15.7] and spawn_count = 3
  {% for spawn_count %}
    {
      "x": {% spawn_x!get_$i!float %},  # Get element from spawn_x with index 0, 1, 2
    },
  {% endfor %}
  ```

You can combine multiple arrays to create structured data
  ```
  # If spawn_x = [10.5, 20.3, 15.7], spawn_y = [5.1, 8.4, 3.2], spawn_count = 3
  {% for spawn_count %}
    {
      "x": {% spawn_x!get_$i!float %},
      "y": {% spawn_y!get_$i!float %}
    }
  {% endfor %}
  ```

Just like with `foreach`, the system automatically removes the last comma in the generated list

## Comments in Templates

GSConfig supports two ways to add comments to templates:

### Single-line Comments

To add single-line comments, use the syntax:

```
{# This is a comment that will be removed during template processing #}
```

Example of using single-line comments:

```
{
  "_maxHealth": {health!float}, {# Maximum mob health #}
  "_timeToStartRegeneration": {time_before_regen!float}, {# Time until regeneration begins #}
  "_regenerationSpeed": {regen_speed!float} {# Health regeneration speed #}
}
```

### Multi-line Comments

For multi-line comments, use the `comment` command:

```
{% comment %}
This is a multi-line comment,
which will be removed during template processing.
Useful for temporarily disabling
large blocks of the template.
{% endcomment %}
```

Example of using multi-line comments:

```
{
  "_mainSettings": {
    "health": {health!float},
    "speed": {speed!float}
  },
  
  {% comment %}
  This block with additional parameters
  is temporarily disabled as it needs refinement
  "_additionalSettings": {
    "armor": {armor!float},
    "resistance": {resistance!float}
  },
  {% endcomment %}
  
  "_visualSettings": {
    "scale": {scale!float}
  }
}
```

Both types of comments are completely removed during template processing and do not appear in the final result.

### Custom String Control Commands

See the section [Custom Extensions](07-Custom_Extensions.md)