# Recipes and Examples

This section presents examples of typical usage scenarios for GSConfig to solve specific tasks.

## Config Generation Automation

Automating the export of data from Google Sheets to JSON files for use in a game:

```python
import gsconfig
import os

# Client setup
client = gsconfig.GoogleOauth().client

# Document ID
document_id = "1H8vkzaZZVOgtYrtWHm792FGWaSBhJZNiB0ckco_RGp0"

# Creating a config
config = gsconfig.GameConfigLite(document_id, client)

# Directory for saving configs
output_folder = 'game_configs'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Export all document pages
for page in config:
    # Skip pages without .json extension
    if not page.title.endswith('.json'):
        continue
    
    # Get data
    data = page.get()
    
    # Save to file
    filename = page.name  # Without extension
    gsconfig.tools.save_json(data, filename, output_folder)
    print(f"Saved {filename}.json")
```

## Working with Multiple Documents

Using `GameConfig` to work with multiple related documents:

```python
import gsconfig
import os

# Document IDs
document_ids = {
    'mobs': '1a5326Sg3LYhzRGACp160zEdcvKirXMl5avP2USIq2PE',
    'items': '1dbmmds9IIAqT2rDxXSPLm8g6VhEorS5_8_fvd6A22rs',
    'levels': '1yBJUmNDj9yjJCl6X8HYe1XpjUL_Ju55MqoEngLbQqnw'
}

# Client setup
client = gsconfig.GoogleOauth().client

# Creating a config
config = gsconfig.GameConfig(list(document_ids.values()), client)

# Access to documents by name
mobs_doc = config['mobs']
items_doc = config['items']
levels_doc = config['levels']

# Export all pages from all documents
output_folder = 'configs'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Save each document to a separate subfolder
for doc in config:
    doc_folder = os.path.join(output_folder, doc.title)
    if not os.path.exists(doc_folder):
        os.makedirs(doc_folder)
        
    for page in doc:
        if page.title.endswith('.json'):
            page.save(doc_folder)
            print(f"Exported {doc.title}/{page.title}")
```

> **Important!** Best practice is to organize data directly in Google Sheets tables, not in Python code. All relationships between entities and additional calculations should be implemented using formulas and service sheets in the tables themselves. GSConfig should perform minimal data transformation - only export and format conversion.
> 
> Ideally, the structure of JSON obtained from Google Sheets should exactly match the required structure of the game config, and even templates may not be needed.

## Data Templating

Using templates to generate configuration files:

```python
import gsconfig
import os

# Client and config setup
client = gsconfig.GoogleOauth().client
document_id = "1H8vkzaZZVOgtYrtWHm792FGWaSBhJZNiB0ckco_RGp0"
config = gsconfig.GameConfigLite(document_id, client)

# Folders for templates and output data
templates_folder = 'templates'
output_folder = 'configs'

# Make sure the folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Templates for different data types
mob_template = gsconfig.Template(os.path.join(templates_folder, 'MobSettings.template'))
area_template = gsconfig.Template(os.path.join(templates_folder, 'AreaBotConfig.template'))

# Getting mob data
mobs_page = config['mobs.json']
mob_data = mobs_page.get()

# Generating config for each mob
for mob in mob_data:
    # Filling the template with data
    mob_config = mob_template.make(mob)
    
    # Saving to file
    gsconfig.tools.save_json(mob_config, mob['name'], output_folder)
    print(f"Generated config for {mob['name']}")

# Getting area data
areas_page = config['areas.json']
area_data = areas_page.get()

# Generating config for each area
for area in area_data:
    # Filling the template with data
    area_config = area_template.make(area)
    
    # Saving to file
    gsconfig.tools.save_json(area_config, area['name'], output_folder)
    print(f"Generated config for {area['name']}")
```

## Automating Config Updates When Data Changes

Example script for periodically updating configs when data changes in Google Sheets:

```python
import gsconfig
import time
import os
import hashlib
import json
from datetime import datetime

def calculate_hash(data):
    """Calculates data hash to detect changes"""
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

def log_update(message):
    """Writes a message to the log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    with open("config_updates.log", "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def monitor_and_update_configs():
    # Client setup
    client = gsconfig.GoogleOauth("service_account.json").client
    
    # Document ID
    document_id = "1H8vkzaZZVOgtYrtWHm792FGWaSBhJZNiB0ckco_RGp0"
    
    # Creating a config
    config = gsconfig.GameConfigLite(document_id, client)
    
    # Folders for templates and output data
    templates_folder = 'templates'
    output_folder = 'configs'
    
    # Make sure folders exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Dictionary for storing data hashes
    data_hashes = {}
    
    log_update("Starting config monitoring service")
    
    try:
        while True:
            try:
                # Check all document pages
                for page in config:
                    # Skip pages without .json extension
                    if not page.title.endswith('.json'):
                        continue
                    
                    # Get data and calculate hash
                    data = page.get()
                    current_hash = calculate_hash(data)
                    
                    # If the hash has changed, update the config
                    if page.title not in data_hashes or data_hashes[page.title] != current_hash:
                        log_update(f"Changes detected in {page.title}")
                        
                        # Choose a template depending on the page
                        template_path = os.path.join(templates_folder, f"{page.name}.template")
                        
                        # If a template exists, use it
                        if os.path.exists(template_path):
                            template = gsconfig.Template(template_path)
                            
                            # For a list of objects, process each element
                            if isinstance(data, list):
                                for item in data:
                                    if 'name' in item:
                                        config_data = template.make(item)
                                        gsconfig.tools.save_json(config_data, item['name'], output_folder)
                                        log_update(f"Updated config for {item['name']}")
                            else:
                                # For a single object
                                config_data = template.make(data)
                                gsconfig.tools.save_json(config_data, page.name, output_folder)
                                log_update(f"Updated config for {page.name}")
                        else:
                            # If no template, save data as is
                            gsconfig.tools.save_json(data, page.name, output_folder)
                            log_update(f"Saved raw data for {page.name}")
                        
                        # Update hash
                        data_hashes[page.title] = current_hash
                
                # Wait before the next check
                log_update("Waiting for next check cycle")
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                log_update(f"Error during update: {str(e)}")
                time.sleep(60)  # Wait a minute before trying again
    
    except KeyboardInterrupt:
        log_update("Monitoring service stopped by user")

if __name__ == "__main__":
    monitor_and_update_configs()
```

This script can be run as a background process on a server, and it will automatically update configs when data changes in Google Sheets.