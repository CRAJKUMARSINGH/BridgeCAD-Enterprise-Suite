import ast, os, re, sys

with open(os.path.join('bridgecad_core', 'models.py'), encoding='utf-8') as f:
    models_src = f.read()
models_tree = ast.parse(models_src)

# Collect all enum names imported from .types
imported_enums = []
for node in ast.iter_child_nodes(models_tree):
    if isinstance(node, ast.ImportFrom) and node.module == '.types':
        for alias in node.names:
            imported_enums.append(alias.name)

# Collect ALL name references that appear inside type annotations
# Strategy: walk AST, find every Name node in annotation-context
annotation_names = set()
for node in ast.walk(models_tree):
    if isinstance(node, ast.AnnAssign):
        for sub in ast.walk(node.annotation):
            if isinstance(sub, ast.Name):
                annotation_names.add(sub.id)
    if isinstance(node, ast.FunctionDef):
        # Check return type and parameter annotations
        if node.returns:
            for sub in ast.walk(node.returns):
                if isinstance(sub, ast.Name):
                    annotation_names.add(sub.id)
        for arg in node.args.args:
            if arg.annotation:
                for sub in ast.walk(arg.annotation):
                    if isinstance(sub, ast.Name):
                        annotation_names.add(sub.id)

# Also find string forward references via dump dump
dump = ast.dump(models_tree)
str_fwds = re.findall(r"annotation=u?'([A-Z][A-Za-z0-9_]*)'", dump)
annotation_names.update(str_fwds)

# Now filter: which ones look like enums? capitalized, not base Python types
skip = {'Optional','Union','list','List','Dict','dict','Tuple','tuple','Set','set',
        'Decimal','date','datetime','time','str','int','float','bool','bytes','Type',
        'BaseModel','ConfigDict','Field','FieldInfo','Any','Enum','classmethod',
        'staticmethod','property','ModelComputedFieldInfo','Self'}

used_enumlike = {n for n in annotation_names if n and n[0].isupper() and n not in skip}

print("USED in type annotations (enum-like):")
for n in sorted(used_enumlike):
    imported = n in imported_enums
    print(f"  {'[IMPORTED]' if imported else '[NOT IMPORTED!!]':<18} {n}")

print()
print("IMPORTED but NOT used in annotations (might be used in validator/value):")
used_all = annotation_names | set(imported_enums)
# Do extra scan for name usage anywhere in source (including validators)
# Also check if name appears at least once outside of import block (non-comment)
names_used_anywhere = set()
# Tokenize roughly (avoid comments/strings):
src_no_strings = re.sub(r'#.*$', '', models_src, flags=re.M)
src_no_strings = re.sub(r'"[^"]*"', '', src_no_strings)
src_no_strings = re.sub(r"'[^']*'", '', src_no_strings)
for name in imported_enums:
    if re.search(r'\b' + re.escape(name) + r'\b', src_no_strings):
        names_used_anywhere.add(name)

for n in sorted(imported_enums):
    if n not in names_used_anywhere:
        print(f"  [UNUSED] {n}")
