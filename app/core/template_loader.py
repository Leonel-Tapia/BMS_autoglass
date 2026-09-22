# /app/core/template_loader.py | Updated: 2026-09-22
import os
from fastapi.templating import Jinja2Templates

# 1. Get the absolute path of 'app/core/'
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Go up one level to 'app/' and enter 'templates/'
templates_path = os.path.normpath(os.path.join(current_dir, "..", "templates"))

# 3. Robust initialization
jinja = Jinja2Templates(directory=templates_path)

# Confirmation for console
print(f"INFO: BMS Autoglass templates location: {templates_path}")