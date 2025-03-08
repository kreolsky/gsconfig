# GSConfig Documentation

GSConfig is a Python library that provides a convenient interface for working with game configurations stored in Google Sheets. Built on top of [gspread](https://docs.gspread.org/en/latest/). The library solves several key challenges:

1. **Data Access**: Simple and reliable access to game configuration data in Google Sheets
2. **Simplified Data Syntax**: Specially designed intermediate format with concise syntax for convenient entry in tables, supporting lists, dictionaries, and nested structures, which is automatically converted to standard JSON
3. **Templating**: Using templates to generate game configs with specific structures
4. **Workflow Integration**: Allows game designers to set up their own workflows and formulas in Google Sheets, creating a convenient admin panel for the game

GSConfig simplifies the game configuration development workflow, automates routine tasks, and reduces the likelihood of errors when transferring data from spreadsheets to game systems.

## Key Features

- **Convenient Syntax for Tables**: Simplified format for writing complex data (lists, dictionaries, nested structures) without cumbersome JSON syntax, which eliminates most manual input errors
- **Support for Various Data Schemas**: Works with different data organization structures in tables
- **Powerful Template System**: Generation of complex configuration files using templates
- **Unified Interface**: Work with one or multiple documents through a unified API

## Table of Contents

1. [Quick Start](01-quick-start.md)
2. [Core Abstractions](02-core-abstractions.md)
3. [Intermediate Format and Conversion](03-intermediate-format.md)
4. [Data Extraction and Schemas](04-data-extraction.md)
5. [Working with Templates](05-working-with-templates.md)
6. [Best Practices](06-best-practices.md)
7. [Custom Extensions](07-custom-extensions.md)
8. [Recipes and Examples](08-recipes-and-examples.md)
9. [API Reference](09-api-reference.md)