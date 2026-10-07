import os
import re

# 1. Update plugins
plugins_dir = "/home/boss/File-Store/plugins/auto_uploader"
for root, dirs, files in os.walk(plugins_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read()
            
            # Imports
            content = re.sub(r'from database import db\n?', '', content)
            content = re.sub(r'from config import Config\n?', '', content)
            
            # Logic
            content = re.sub(r'\bdb\.', 'client.auto_db.', content)
            content = re.sub(r'Config\.OWNERS', 'client.admins', content)
            content = re.sub(r'Config\.LOG_CHANNEL', 'client.db_channel_id', content)
            content = re.sub(r'Config\.GLOBAL_DUMP_CHANNEL', 'client.db_channel_id', content)
            content = re.sub(r'Config\.', 'getattr(client, "config_", None)', content) # safety for other configs
            
            # Rename settings command in handlers to not conflict
            if "settings.py" in file or "commands.py" in file:
                content = content.replace('command("settings")', 'command("auto_settings")')
            
            with open(path, "w") as f:
                f.write(content)

# 2. Update utils
utils_dir = "/home/boss/File-Store/utils"
for root, dirs, files in os.walk(utils_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read()
            
            content = re.sub(r'from database import db\n?', '', content)
            content = re.sub(r'from config import Config\n?', '', content)
            
            content = re.sub(r'\bdb\.', 'client.auto_db.', content)
            content = re.sub(r'Config\.OWNERS', 'client.admins', content)
            content = re.sub(r'Config\.GLOBAL_DUMP_CHANNEL', 'getattr(client, "db_channel_id", None)', content)
            
            with open(path, "w") as f:
                f.write(content)

# 3. Update helper/auto_db.py
db_path = "/home/boss/File-Store/helper/auto_db.py"
with open(db_path, "r") as f:
    content = f.read()

content = content.replace("from config import Config", "")
content = re.sub(r'db = Database\(.*?\)', '', content)
content = re.sub(r'Config\.OWNERS', '[]', content) # handled in plugin layer mostly

with open(db_path, "w") as f:
    f.write(content)

