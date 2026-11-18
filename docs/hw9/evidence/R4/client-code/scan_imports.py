import ast, sys, os, json
root = sys.argv[1]
std = set(sys.stdlib_module_names)
res = {}
for dp, _, fs in os.walk(os.path.join(root, "sqlite_utils")):
    for f in fs:
        if not f.endswith(".py"): continue
        p = os.path.join(dp, f); rel = os.path.relpath(p, root).replace(os.sep, "/")
        tree = ast.parse(open(p, encoding="utf8").read())
        parents = {}
        for n in ast.walk(tree):
            for c in ast.iter_child_nodes(n): parents[c] = n
        def optional(n):
            while n in parents:
                n = parents[n]
                if isinstance(n, ast.Try):
                    for h in n.handlers:
                        t = h.type
                        names = [] if t is None else [x.id for x in (t.elts if isinstance(t, ast.Tuple) else [t]) if isinstance(x, ast.Name)]
                        if t is None or any(x in ("ImportError", "ModuleNotFoundError") for x in names): return True
            return False
        for n in ast.walk(tree):
            mods = []
            if isinstance(n, ast.Import): mods = [a.name.split(".")[0] for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module: mods = [n.module.split(".")[0]]
            for m in mods:
                if m in std or m == "sqlite_utils": continue
                d = res.setdefault(m, {}).setdefault(rel, [])
                d.append(optional(n))
for m, fs in sorted(res.items()):
    print(m, {f: v for f, v in sorted(fs.items())})
