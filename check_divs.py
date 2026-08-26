import subprocess
result = subprocess.run(['git', 'show', 'HEAD:templates/infinite_assets.html'], capture_output=True, text=True, encoding='utf-8')
for i, line in enumerate(result.stdout.splitlines()):
    if '</div>' in line:
        print(f"{i+1}: {line.strip()}")
