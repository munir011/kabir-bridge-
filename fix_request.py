import os

# Path to the request.py
file_path = "venv_py311/lib/python3.11/site-packages/telegram/utils/request.py"

# Read the content of the file
with open(file_path, "r") as file:
    content = file.read()

# Find and fix the problematic code
if "import urllib3.contrib.appengine as appengine" in content:
    # Replace with properly indented version
    fixed_content = content.replace(
        "import urllib3.contrib.appengine as appengine",
        "    import urllib3.contrib.appengine as appengine"
    )
    
    # Write the fixed content back to the file
    with open(file_path, "w") as file:
        file.write(fixed_content)
    
    print("Fixed the indentation error in request.py")
else:
    print("Could not find the problematic line in request.py") 