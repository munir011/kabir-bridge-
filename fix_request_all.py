import os
import re

# Path to the request.py
file_path = "venv_py311/lib/python3.11/site-packages/telegram/utils/request.py"

# Read the content of the file
with open(file_path, "r") as file:
    content = file.read()

# Extract and fix the problematic section
pattern = r"try:\s+import urllib3\.contrib\.appengine as appengine"
replacement = "try:\n        import urllib3.contrib.appengine as appengine"

if re.search(pattern, content):
    fixed_content = re.sub(pattern, replacement, content)
    
    # Write the fixed content back to the file
    with open(file_path, "w") as file:
        file.write(fixed_content)
    
    print("Fixed the try-except block in request.py")
else:
    print("Could not find the problematic pattern in request.py") 