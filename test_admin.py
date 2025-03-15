import os

# Read the .env file directly
with open('.env', 'r') as f:
    env_content = f.read()
    print("Content of .env file:")
    print(env_content)

# Extract the ADMIN_USER_ID value
for line in env_content.split('\n'):
    if line.startswith('ADMIN_USER_ID='):
        admin_ids_str = line.split('=')[1]
        break
else:
    admin_ids_str = ""

print(f"\nAdmin IDs string: {admin_ids_str}")

# Parse the admin IDs
admin_ids = [id.strip() for id in admin_ids_str.split(",")]
print(f"Admin IDs list: {admin_ids}")

def is_admin(user_id):
    """Check if a user is an admin"""
    return str(user_id) in admin_ids

# Test with the first admin ID
if admin_ids:
    first_admin_id = admin_ids[0]
    print(f"First admin ID: {first_admin_id}")
    print(f"Is first admin an admin? {is_admin(first_admin_id)}")

# Test with the second admin ID if available
if len(admin_ids) > 1:
    second_admin_id = admin_ids[1]
    print(f"Second admin ID: {second_admin_id}")
    print(f"Is second admin an admin? {is_admin(second_admin_id)}")

# Test with a non-admin ID
non_admin_id = "123456789"
print(f"Non-admin ID: {non_admin_id}")
print(f"Is non-admin an admin? {is_admin(non_admin_id)}") 