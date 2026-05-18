import os

guard = '\n    <script>\n        document.addEventListener("DOMContentLoaded", async function() {\n            var u = await Auth.checkSession();\n            if (!u) { window.location.href = "/"; }\n        });\n    </script>'

# Map pages to their specific auth.js tag pattern
pages_with_patterns = {
    'comparison.html':  'js/sidebar.js"></script>',
    'contacts.html':    'js/auth.js?v=2.4"></script>',
    'calendar.html':    'js/auth.js?v=2.4"></script>',
    'settings.html':    'js/auth.js?v=2.4"></script>',
    'attachments.html': 'js/auth.js?v=2.4"></script>',
    'drafts.html':      'js/auth.js?v=2.4"></script>',
}

for page, needle in pages_with_patterns.items():
    path = os.path.join('ui', page)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'Auth.checkSession' in content:
        print('Already has guard: ' + page)
        continue
    if needle in content:
        content = content.replace(needle, needle + guard, 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Guard added: ' + page)
    else:
        print('Pattern not found in: ' + page + ' [' + needle + ']')
