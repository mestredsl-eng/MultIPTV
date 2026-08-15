"""Check if the new route is registered."""

from app.app import create_app

app = create_app()

print("App created successfully")
print("\nAvailable maintenance routes:")
print("=" * 60)

with app.app_context():
    from flask import current_app
    maintenance_routes = []
    for rule in current_app.url_map.iter_rules():
        if 'maintenance' in rule.rule:
            maintenance_routes.append((rule.rule, rule.methods))
    
    # Sort by route
    maintenance_routes.sort(key=lambda x: x[0])
    
    for route, methods in maintenance_routes:
        print(f"{route} - {methods}")
    
    # Check specifically for our new route
    print("\n" + "=" * 60)
    target_route = '/api/maintenance/blacklist-duplicates-lowest-quality'
    if any(target_route in route for route, _ in maintenance_routes):
        print(f"✅ Route '{target_route}' is registered!")
    else:
        print(f"❌ Route '{target_route}' NOT found!")
