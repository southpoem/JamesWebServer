from jinja2 import Environment, FileSystemLoader

try:
    env = Environment(loader=FileSystemLoader(r'C:\PycharmProjects\JamesWebServer\templates'))
    template = env.get_template('infinite_assets.html')
    print("Template syntax is valid!")
except Exception as e:
    print(f"Error: {e}")
