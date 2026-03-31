def replace_in_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

replace_in_file(r'd:\bbms\templates\dashboard.html', [
    ('group" style="animation-delay: 0.1s;"', 'group stagger-1"'),
    ('group" style="animation-delay: 0.2s;"', 'group stagger-2"'),
    ('group" style="animation-delay: 0.3s;"', 'group stagger-3"'),
    ('{% endif %}" style="animation-delay: 0.4s;"', '{% endif %} stagger-4"'),
    ('group" style="animation-delay: 0.5s;"', 'group stagger-5"'),
    ('shadow-sm" style="animation-delay: 0.5s;"', 'shadow-sm stagger-5"'),
    ('shadow-sm" style="animation-delay: 0.6s;"', 'shadow-sm stagger-6"'),
    ('overflow-hidden" style="animation-delay: 0.7s;"', 'overflow-hidden stagger-7"'),
    ('overflow-hidden" style="animation-delay: 0.8s;"', 'overflow-hidden stagger-8"')
])
print('Done replacing.')
