# Quick Start

## Installation

```bash
git clone https://github.com/kreolsky/gsconfig
```

## Authentication

GSConfig uses the `gspread` library to work with Google Sheets API. You can use two authentication methods:

### 1. OAuth (recommended for local development)

```python
import gsconfig

# Interactive authentication via OAuth
client = gsconfig.GoogleOauth().client
```

The first time you run this, a browser window will open for Google authentication.

### 2. Service Account (recommended for servers)

```python
import gsconfig

# Authentication via service account
keyfile = 'path/to/credentials.json'
client = gsconfig.GoogleOauth(keyfile).client
```

To obtain `credentials.json`:
1. Create a project in Google Cloud Console
2. Enable the Google Sheets API
3. Create a service account and download a key in JSON format
4. Grant access to the service account for the necessary spreadsheets

## Getting Data from Google Sheets

A simple example of using GSConfig to load data from Google Sheets and save it as JSON:

```python
import gsconfig

# Google Sheets document ID
document_id = "1H8vkzaZZVOgtYrtWHm792FGWaSBhJZNiB0ckco_XXXX"

# Creating a client for authentication
client = gsconfig.GoogleOauth().client

# Initializing config from a single document
config = gsconfig.GameConfigLite(document_id, client)

# Getting a page with data (page name in the spreadsheet - "mobs.json")
page = config["mobs.json"]

# Displaying data in JSON format
print(page.get())

# Saving data to a JSON file
output_folder = 'json'
page.save(output_folder)
```

### Example Data in Google Sheets

Let's say in the Google Sheets table on the "mobs.json" page we have the following data:

```
 name          | type      | health | attack | speed | abilities                             
---------------|-----------|--------|--------|-------|---------------------------------------
 Goblin        | humanoid  | 20     | 5      | 30    | {stealth = 3, thievery = 4}           
 Skeleton      | undead    | 15     | 6      | 25    | {resistance = {fire = 2, ice = -1}}
```

### Resulting JSON

After executing the code, we'll get the following JSON document:

```json
[
    {
        "name": "Goblin",
        "type": "humanoid",
        "health": 20,
        "attack": 5,
        "speed": 30,
        "abilities": {
            "stealth": 3,
            "thievery": 4
        }
    },
    {
        "name": "Skeleton",
        "type": "undead",
        "health": 15,
        "attack": 6,
        "speed": 25,
        "abilities": {
            "resistance": {
                "fire": 2,
                "ice": -1
            }
        }
    }
]
```

Note that:
- Numeric values are automatically recognized as numbers
- Strings with syntax like `{key = value}` are converted to JSON objects
- Nested objects preserve their structure (e.g., `resistance` for Skeleton)
- Values like `true` are recognized as boolean types

### Example Tables

- https://docs.google.com/spreadsheets/d/1yBJUmNDj9yjJCl6X8HYe1XpjUL_Ju55MqoEngLbQqnw
- https://docs.google.com/spreadsheets/d/1X7OKMoIdIXtsDYI3QDkqr3Q9h3isS6vRaJ9noxT90lQ
- https://docs.google.com/spreadsheets/d/1yBJUmNDj9yjJCl6X8HYe1XpjUL_Ju55MqoEngLbQqnw

## Working with Templates

For using a template when saving, let's consider a detailed example:

```python
import gsconfig
import os

# Creating an output folder if it doesn't exist
output_folder = 'json'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Getting access to the spreadsheet
client = gsconfig.GoogleOauth().client
document_id = "1H8vkzaZZVOgtYrtWHm792FGWaSBhJZNiB0ckco_XXXX"
config = gsconfig.GameConfigLite(document_id, client)

# Getting the mobs.json page with mob data
config_page = config["mobs.json"]
mob_data = config_page.get()  # List of mobs from the table

# Loading the template
template = gsconfig.Template('templates/MobSettings.template')

# Building a config for each mob
for mob in mob_data:
    config = template.make(mob)
    gsconfig.tools.save_json(config, mob['name'], output_folder)
    print(f"{mob['name']} - was saved!")
```

### Example content of "mobs.json" page:

In Google Sheets, the page might look like this (using free format with headers):
```
name       | health | speed | bot_rewards                    | time_before_regen | regen_speed | weight | speed_walk_min | speed_walk_max | speed_run_min | speed_run_max | captured_delay | captured_angle | captured_range
-----------|--------|-------|--------------------------------|-------------------|-------------|--------|----------------|----------------|---------------|---------------|----------------|----------------|--------------
Sheep      | 100    | 1.5   | {wool = 3, meat = 2, gold = 5} | 3.0               | 1.0         | 80.0   | 0.8            | 1.2            | 2.0           | 2.5           | 2              | 30.0           | 5.0
Pig        | 120    | 1.2   | {meat = 4, leather = 1}        | 4.0               | 1.5         | 100.0  | 0.7            | 1.0            | 1.8           | 2.2           | 3              | 45.0           | 4.0
Cow        | 150    | 1.0   | {meat = 5, leather = 2}        | 5.0               | 2.0         | 150.0  | 0.6            | 0.9            | 1.6           | 2.0           | 4              | 60.0           | 3.0
```

### Example "MobSettings.template":

```json
{
  "_maxHealth": {% health!float %},
  "_timeToStartRegeneration": {% time_before_regen!float %},
  "_regenerationSpeed": {% regen_speed!float %},

  "_botRewards": {% bot_rewards %}
}
```

### Example resulting "Sheep.json" file:

```json
{
  "_maxHealth": 100.0,
  "_timeToStartRegeneration": 3.0,
  "_regenerationSpeed": 1.0,

  "_botRewards": {
    "wool": 3,
    "meat": 2,
    "gold": 5
  }
}
```

GSConfig allows you to:

1. Conveniently store game configuration data in a human-readable format in Google Sheets
2. Use templates to transform this data into the desired JSON structure
3. Convert data types (e.g., via `!float` or `!int`) to match the requirements of your game system
4. Batch generate configs for all entities