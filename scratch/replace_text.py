import os, re
ui_dir = r'c:\Users\22001\Desktop\procurement\Executive-RFQ-Assistant-main\ui'
for root, _, files in os.walk(ui_dir):
    for f in files:
        if f.endswith(('.html', '.js')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            if 'RFI' in content:
                new_content = re.sub(r'\bRFI\b', 'Procurement', content)
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
print("Replacement completed successfully.")
