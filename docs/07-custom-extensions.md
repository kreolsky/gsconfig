# Custom Extensions

This section describes the possibilities of extending GSConfig functionality to adapt to the specific requirements of your project.

## Custom Template Functions

GSConfig allows you to add your own functions for data processing in templates. This can be done by extending the `key_command_handlers` dictionary in the `Template` class.

### Example of Adding Custom Template Functions

```python
import gsconfig
import math

# Create a template instance
template = gsconfig.Template('templates/MobSettings.template')

# Add a custom function for rounding to the nearest multiple of 5
def key_command_round5(value, command):
    """
    Rounds a number to the nearest multiple of 5.
    Example: 12 -> 10, 13 -> 15
    """
    return 5 * round(float(value) / 5)

# Add a function for calculating square root
def key_command_sqrt(value, command):
    """
    Calculates the square root of a number.
    """
    return math.sqrt(float(value))

# Add a function for converting to uppercase
def key_command_uppercase(value, command):
    """
    Converts a string to uppercase.
    """
    return str(value).upper()

# Register new functions in the template
template.key_command_handlers.update({
    'round5$': key_command_round5,
    'sqrt$': key_command_sqrt,
    'uppercase$': key_command_uppercase
})

# Now these functions can be used in the template:
"""
{
  "roundedHealth": {health!round5},
  "sqrtDamage": {damage!sqrt},
  "NAME": {name!uppercase}
}
"""
```

## Custom Template Block Commands

You can also add new string control commands by extending the `template_command_handlers` dictionary.

```python
import gsconfig
import random

# Create a template instance
template = gsconfig.Template('templates/MobSettings.template')

# Add a new command for random selection from a list
def template_command_random(params, content, balance):
    """
    Randomly selects one of several variants.
    
    Example:
    {% random 3 %}
    "variant": {$i}
    {% endrandom %}
    """
    try:
        count = int(params)
        chosen = random.randint(0, count-1)
        return content.replace('$i', str(chosen))
    except ValueError:
        return ""

# Register the new command
template.template_command_handlers['random'] = template_command_random

# Now this command can be used in the template
"""
{% random 3 %}
"randomFeature": "feature_{$i}"
{% endrandom %}
"""
```

## Custom Parser Commands

You can also add your own commands to the `ConfigJSONConverter` parser for processing the intermediate format.

```python
import gsconfig

# Create a converter instance
converter = gsconfig.ConfigJSONConverter()

# Add a new command for wrapping a key in a prefix
def handler_prefix(x, prefix):
    """
    Adds a prefix to each key in a dictionary.
    Example: key!prefix_item transforms {a: 1} into {item_a: 1}
    """
    if not isinstance(x, dict):
        return x
        
    result = {}
    prefix_value = prefix.split('_')[1] + '_'
    
    for key, value in x.items():
        result[prefix_value + key] = value
        
    return result

# Add a new command for summing all elements of a list
def handler_sum(x, command):
    """
    Sums all elements of a list.
    Example: [1, 2, 3]!sum transforms into 6
    """
    if not isinstance(x, list):
        return x
        
    return sum([float(item) for item in x if str(item).replace('.', '').isdigit()])

# Register new commands in the converter
converter.parser.command_handlers.update({
    'prefix_': handler_prefix,
    'sum': handler_sum
})

# Now you can use these commands in the intermediate format:
# stats!prefix_mob = {health = 100, speed = 1.5}
# damage!sum = {1, 2, 3, 4}
```

## Custom Data Formats

GSConfig allows you to extend the `Extractor` class to support your own data formats.

### Example of Creating a Custom Extractor for XML

```python
import gsconfig
from gsconfig.extractor import Extractor

# Create your own extractor class
class CustomExtractor(Extractor):
    def __init__(self):
        super().__init__()
        # Add a new format
        self.extractors['xml'] = self._extract_xml
    
    def _extract_xml(self, page_data, **params):
        """
        Parses data from a table into XML format.
        """
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        # Use the standard JSON parser
        data = self._extract_json(page_data, **params)
        
        # Convert to XML
        def dict_to_xml(parent, d):
            for key, value in d.items():
                if isinstance(value, dict):
                    child = ET.SubElement(parent, key)
                    dict_to_xml(child, value)
                elif isinstance(value, list):
                    child = ET.SubElement(parent, key)
                    for item in value:
                        if isinstance(item, dict):
                            item_elem = ET.SubElement(child, 'item')
                            dict_to_xml(item_elem, item)
                        else:
                            item_elem = ET.SubElement(child, 'item')
                            item_elem.text = str(item)
                else:
                    child = ET.SubElement(parent, key)
                    child.text = str(value)
        
        root = ET.Element('root')
        dict_to_xml(root, data if isinstance(data, dict) else {'items': data})
        
        # Pretty XML formatting
        xml_string = ET.tostring(root, 'utf-8')
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent='  ')
        
        return pretty_xml

# Create a Page class with a custom extractor
class CustomPage(gsconfig.Page):
    def __init__(self, worksheet):
        super().__init__(worksheet)
        self._extractor = CustomExtractor()

# Using the custom class
client = gsconfig.GoogleOauth().client
spreadsheet = client.open_by_key("1H8vkzaZZVOgtYrtWHm792FGWaSBhJZNiB0ckco_RGp0")
worksheet = spreadsheet.worksheet("items.json")

# Create a page with a custom extractor
page = CustomPage(worksheet)

# Set XML format
page.set_format('xml')

# Get data in XML format
xml_data = page.get()

# Save to file
with open('items.xml', 'w', encoding='utf-8') as f:
    f.write(xml_data)
```