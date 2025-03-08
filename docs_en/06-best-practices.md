# Best Practices

This section presents recommendations for effective use of GSConfig and organization of work with game configurations.

## Document Organization

1. **Logical Separation** - separate data into different documents by logical groups:
   - Game balance tables
   - Character and mob settings
   - Level configurations
   - Items and economy
   - Localization and texts

2. **Documentation** - create separate pages or documents with data structure descriptions:
   - Add comments to complex fields
   - Describe dependencies between tables
   - Document changes in data structure

3. **Access Rights** - configure access rights according to team roles:
   - Developers - full access
   - Designers - access to balance and gameplay settings
   - QA - read access for testing

## Page Naming

1. **Use Extensions** to indicate the format:
   - `mobs.json` - data will be parsed into JSON
   - `translations.csv` - data will be processed as CSV
   - `debug.raw` - data will be returned without processing

2. **Prefixes for Service Pages**:
   - Start with `#` or `.` for service pages that don't need to be exported
   - For example: `#calculation`, `.notes`, `#temp`

3. **Clear and Consistent Names**:
   - Use a unified naming style (e.g., camelCase or snake_case)
   - Add prefixes to group related pages
   - Use suffixes to indicate data variants

## Data Structure

1. **Data Schemas**:
   - For simple key-value pairs, use the schema `('key', 'data')`
   - For data with variants, use a schema with multiple data columns
   - For tables with multiple records, use free format with headers

2. **Intermediate Format**:
   - Use parser version v1 for compatibility with old code
   - Use version v2 for new projects with more natural dictionary handling
   - Avoid overly complex nested structures
   - Use `!list`, `!dlist` commands for explicit format control

3. **Templates**:
   - Create separate templates for different entity types
   - Use `{% if %}` conditional blocks for optional data
   - Apply `{% foreach %}` loops to generate repeating elements
   - Fix data types with commands like `!float`, `!int`, etc.

## Performance Tips

1. **Caching**:
   - GSConfig automatically caches page data after the first request
   - For reloading data, create a new Page or GameConfigLite object

2. **Data Organization**:
   - Split large tables into logical groups
   - Use related tables instead of duplicating data
   - Create auxiliary tables for calculations and validations

3. **Template Optimization**:
   - Use `jsonify=True` in templates to get Python structures instead of strings
   - For large volumes of data, divide templates into smaller parts

4. **Working with Large Tables**:
   - Use `Page.set_schema()` to extract only the needed columns
   - Apply data filtering on the Python side instead of loading the entire table
   - For very large tables, consider splitting them into multiple pages