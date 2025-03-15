import os

# Path to the inputfile.py
file_path = "venv_py311/lib/python3.11/site-packages/telegram/files/inputfile.py"

# Read the content of the file
with open(file_path, "r") as file:
    content = file.read()

# Fix the syntax error
fixed_content = content.replace("image = (imghdr.what(None, stream)", "image = imghdr.what(None, stream) if imghdr else None")

# Write the fixed content back to the file
with open(file_path, "w") as file:
    file.write(fixed_content)

print("Fixed the syntax error in inputfile.py") 