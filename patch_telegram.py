import os
import sys

def patch_file(file_path, search_text, replace_text):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        if search_text in content:
            new_content = content.replace(search_text, replace_text)
            with open(file_path, 'w') as file:
                file.write(new_content)
            print(f"Successfully patched: {file_path}")
        else:
            print(f"Search text not found in: {file_path}")
    except Exception as e:
        print(f"Error patching {file_path}: {str(e)}")

# Find the site-packages directory
site_packages = None
for path in sys.path:
    if path.endswith('site-packages'):
        site_packages = path
        break

if not site_packages:
    print("Could not find site-packages directory")
    sys.exit(1)

# Patch inputfile.py to handle missing imghdr
inputfile_path = os.path.join(site_packages, 'telegram', 'files', 'inputfile.py')
if os.path.exists(inputfile_path):
    patch_file(
        inputfile_path,
        'import imghdr',
        'try:\n    import imghdr\nexcept ImportError:\n    imghdr = None'
    )
    
    # Also patch the usage of imghdr.what
    patch_file(
        inputfile_path,
        'imghdr.what(',
        '(imghdr.what(' if 'imghdr.what(' in open(inputfile_path).read() else 'imghdr and imghdr.what('
    )

# Additional patches for urllib3 issues
request_py = os.path.join(site_packages, 'telegram', 'utils', 'request.py')
if os.path.exists(request_py):
    patch_file(
        request_py,
        'import urllib3.contrib.appengine as appengine',
        'try:\n    import urllib3.contrib.appengine as appengine\nexcept ImportError:\n    appengine = None'
    )

print("Patching complete!")
