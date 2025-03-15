import os
import re

def fix_imports_in_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Replace 'from ..utils' with 'from utils'
    content = re.sub(r'from \.\.utils', r'from utils', content)
    
    # Replace 'from . import' with 'from handlers import'
    content = re.sub(r'from \. import', r'from handlers import', content)
    
    # Replace 'from bot.utils' with 'from utils'
    content = re.sub(r'from bot\.utils', r'from utils', content)
    
    # Replace 'from bot.handlers' with 'from handlers'
    content = re.sub(r'from bot\.handlers', r'from handlers', content)
    
    with open(file_path, 'w') as file:
        file.write(content)
    
    print(f"Fixed imports in {file_path}")

def fix_imports_in_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                fix_imports_in_file(file_path)

if __name__ == "__main__":
    # Fix imports in handlers directory
    fix_imports_in_directory('bot/handlers')
    print("All imports fixed successfully!") 