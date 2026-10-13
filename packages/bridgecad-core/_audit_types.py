import ast, os, sys, re

with open(os.path.join('bridgecad_core', 'types.py'), encoding='utf-8') as f:
    types_src = f.read()
types_tree = ast.parse(types_src)
types_classnames = set()
for node in ast.walk(types_tree):
    if isinstance(node, ast.ClassDef):
        types_classnames.add(node.name)

with open(os.path.join('bridgecad_core', 'models.py'), encoding='utf-8') as f:
    models_src = f.read()
models_tree = ast.parse(models_src)

imported_from_types = set()
for node in ast.iter_child_nodes(models_tree):
    if isinstance(node, ast.ImportFrom) and node.module == '.types':
        for alias in node.names:
            imported_from_types.add(alias.name)

used_typenames = set()
for node in ast.walk(models_tree):
    if isinstance(node, ast.AnnAssign):
        ann = node.annotation
        for sub in ast.walk(ann):
            if isinstance(sub, ast.Name):
                used_typenames.add(sub.id)

optional_types = re.findall(r'Optional\[([A-Z][A-Za-z0-9_]*)\]', models_src)
used_typenames.update(optional_types)
list_types = re.findall(r'list\[([A-Z][A-Za-z0-9_]*)\]', models_src)
used_typenames.update(list_types)

print('IMPORTED FROM TYPES BUT CLASS NOT IN TYPES.PY:')
for name in sorted(imported_from_types):
    if name not in types_classnames:
        print(f'  MISSING: {name}')

print()
print('TYPE NAMES USED IN ANNOTATIONS BUT NOT DEFINED IN TYPES:')
skip = {'Optional','Union','list','List','Dict','Tuple','Set','Date','datetime','Decimal',
        'BaseModel','ConfigDict','Field','FieldInfo','Any','Type','Enum','date','int','str',
        'float','bool','LabeledEnum','RangeBoundedEnum','UnitHaverEnum','ModelComputedFieldInfo'}
for name in sorted(used_typenames):
    if name and name[0].isupper() and name not in skip and name not in types_classnames:
        alt1 = name.rstrip('Type') if name.endswith('Type') else name + 'Type'
        alt2 = name.rstrip('Class') if name.endswith('Class') else name + 'Class'
        alt3 = name.rstrip('Category') if name.endswith('Category') else name + 'Category'
        found_alt = None
        for v in [alt1, alt2, alt3]:
            if v in types_classnames:
                found_alt = v
                break
        if found_alt:
            print(f'  MISMATCH: models.py uses {name!r} => types.py has {found_alt!r}')
        else:
            print(f'  MISSING ENTIRELY: {name!r}')
