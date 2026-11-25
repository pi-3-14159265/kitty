"""Compile kitty Python scripts into a Scratch .sb3 file.

    kitty build script.py
    py -m kitty build script.py
    py -m kitty build stage.py cat.py -o game.sb3

Each file becomes a sprite. A file named stage.py, or a function decorated
with @kitty.stage, becomes the stage. Top-level statements run when the green
flag is clicked. kitty.say("Hello world!") becomes say [Hello world!].

A class that inherits kitty.Sprite is a sprite too. self.say(...) is that
block, self.score is a variable, and methods are scripts or custom blocks.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math as _math
import sys
import zipfile
from pathlib import Path

from kitty import BLOCKS, DECLARATIONS, MATH, MENUS, REQUIRED


class CompileError(Exception):
    """A kitty script cannot be compiled into Scratch blocks."""


_NOT_CONSTANT = object()

_NUMBER_TYPES = {
    "number": (4, "0"),
    "positive": (5, "1"),
    "whole": (6, "10"),
    "integer": (7, "1"),
    "angle": (8, "90"),
    "index": (7, "1"),
}
_TEXT_TYPES = {"text": (10, "")}

_EFFECTS = {
    "color": "COLOR",
    "fisheye": "FISHEYE",
    "whirl": "WHIRL",
    "pixelate": "PIXELATE",
    "mosaic": "MOSAIC",
    "brightness": "BRIGHTNESS",
    "ghost": "GHOST",
}
_SOUND_EFFECTS = {
    "pitch": "PITCH",
    "pan": "PAN",
    "pan left/right": "PAN",
}
_CURRENT = {
    "year": "YEAR",
    "month": "MONTH",
    "date": "DATE",
    "day of week": "DAYOFWEEK",
    "dayofweek": "DAYOFWEEK",
    "hour": "HOUR",
    "minute": "MINUTE",
    "second": "SECOND",
}
_SPECIAL_MENUS = {
    "mouse-pointer": "_mouse_",
    "mouse_pointer": "_mouse_",
    "mouse": "_mouse_",
    "random position": "_random_",
    "random_position": "_random_",
    "myself": "_myself_",
    "stage": "_stage_",
    "edge": "_edge_",
}
_KEYS = {
    "up": "up arrow",
    "down": "down arrow",
    "left": "left arrow",
    "right": "right arrow",
}
_ROTATION = {
    "left-right": "left-right",
    "left_right": "left-right",
    "all around": "all around",
    "all_around": "all around",
    "don't rotate": "don't rotate",
    "dont rotate": "don't rotate",
    "dont_rotate": "don't rotate",
}
_STOP = {
    "all": "all",
    "this script": "this script",
    "this_script": "this script",
    "other scripts": "other scripts in sprite",
    "other scripts in sprite": "other scripts in sprite",
    "other_scripts": "other scripts in sprite",
}
_DRAG = {
    "draggable": "draggable",
    "not draggable": "not draggable",
    "not_draggable": "not draggable",
}
_FRONT = {"front": "front", "back": "back"}
_LAYERS = {"forward": "forward", "backward": "backward"}
_PEN = {
    "color": "color",
    "saturation": "saturation",
    "brightness": "brightness",
    "transparency": "transparency",
}
_MATH_OPS = set(MATH.values()) | {"abs", "floor", "ceiling", "sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "ln", "log", "e ^", "10 ^"}
_RADIANS = {"sin", "cos", "tan"}
_INVERSE = {"asin", "acos", "atan"}
_RAD_TO_DEG = 180 / _math.pi
_DEG_TO_RAD = _math.pi / 180
_STAR_LIMIT = 8
_KW_LIMIT = 4

_COSTUME_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="28" fill="#4C97FF" stroke="#3373CC" stroke-width="2"/>
</svg>
""".encode()

_BACKDROP_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <rect width="480" height="360" fill="#FFFFFF"/>
</svg>
""".encode()


class Value:
    def __init__(self, kind, data, boolean=False):
        self.kind = kind
        self.data = data
        self.boolean = boolean


class Lit:
    def __init__(self, value):
        self.value = value


class Var:
    def __init__(self, name, vid, initial, shared):
        self.name = name
        self.vid = vid
        self.initial = initial
        self.shared = shared
        self.frame = None
        self.boolean = False


class Lst:
    def __init__(self, name, lid, initial, shared, shape=()):
        self.name = name
        self.lid = lid
        self.initial = initial
        self.shared = shared
        self.shape = shape
        self.frozen = False
        self.unique = False
        self.span = None
        self.span_ops = None
        self.ident = None
        self.heap = None
        self.ref_kind = None
        self.ephemeral = False


class Map:
    """A dictionary stored as a keys list and a values list."""

    def __init__(self, name, keys, values):
        self.name = name
        self.keys = keys
        self.values = values
        self.ident = None
        self.ref_kind = None


class DictLiteral:
    def __init__(self, pairs):
        self.pairs = pairs


class FrozenList(list):
    """A tuple stored as a Scratch list."""


class UniqueList(list):
    """A set stored as a Scratch list."""


class _NoDefault:
    pass


NO_DEFAULT = _NoDefault()


class Arg:
    def __init__(self, name, arg_id, boolean):
        self.name = name
        self.arg_id = arg_id
        self.boolean = boolean
        self.default = NO_DEFAULT
        self.keyword_only = False


class StarArgs:
    """Extra positional values. Each slot is its own block input, so calls do not share them."""

    def __init__(self, name, count, slots):
        self.name = name
        self.count = count
        self.slots = slots


class KwArgs:
    """Extra keyword values. Each pair is its own block input."""

    def __init__(self, name, count, pairs):
        self.name = name
        self.count = count
        self.pairs = pairs


class Proc:
    def __init__(self, name, params, warp, proccode):
        self.name = name
        self.params = params
        self.warp = warp
        self.proccode = proccode
        self.returns = None
        self.result = None
        self.results = []
        self.source = None
        self.fn = None
        self.user_params = []
        self.scope_args = []
        self.star = None
        self.kw = None
        self.label = name
        self.frame_arg = None
        self.frame_lists = []
        self.frame_result_vars = []
        self.free_list = None
        self.next_var = None
        self.ticket = None
        self.impl = None
        self.yields = None
        self.return_count = 1
        self.result_list = None
        self.result_dict = None
        self.span_lists = []
        self.owned = []


class Ids:
    def __init__(self):
        self._n = 0

    def _next(self, prefix):
        self._n += 1
        return f"{prefix}{self._n:018d}"

    def block(self):
        return self._next("b")

    def var(self):
        return self._next("v")

    def lst(self):
        return self._next("l")

    def broadcast(self):
        return self._next("c")


class Project:
    def __init__(self):
        self.ids = Ids()
        self.shared_vars = {}
        self.shared_lists = {}
        self.broadcasts = {}
        self.extensions = set()
        self.monitors = []
        self.assets = {}
        self.instances = {}
        self.remote_uses = set()
        self.targets_by_name = {}
        self.applied_decls = {}

    def asset(self, data):
        digest = hashlib.md5(data).hexdigest()
        return digest, self.assets.setdefault

    def add_asset(self, data, ext):
        digest = hashlib.md5(data).hexdigest()
        filename = f"{digest}.{ext}"
        self.assets[filename] = data
        return digest, filename


class SpriteClass:
    def __init__(self, name, node, path, kind):
        self.name = name
        self.node = node
        self.path = path
        self.kind = kind
        self.bases = []
        self.methods = {}
        self.method_order = []
        self.init = None
        self.aliases = {"kitty"}
        self.imported = set()
        self.math_aliases = set()
        self.math_names = {}
        self.module_decls = []


class Instance:
    def __init__(self, sprite_name, blueprint, const_args, node, path):
        self.sprite_name = sprite_name
        self.blueprint = blueprint
        self.const_args = const_args
        self.node = node
        self.path = path


_OF_PROPERTIES = {
    "x_position": "x position",
    "y_position": "y position",
    "direction": "direction",
    "costume_number": "costume #",
    "costume_name": "costume name",
    "size": "size",
    "volume": "volume",
}


def comp(scripts, output=None, warnings=None):
    """Compile one or more kitty Python scripts into an .sb3 file.

    scripts: a path, or a list of paths. A directory adds every .py file in it.
    output: the .sb3 to write. Defaults to the first script's name with a .sb3 suffix.
    warnings: optional list that receives non-fatal import warnings.
    Returns the output path.
    """
    warnings = [] if warnings is None else warnings
    paths = _script_paths(scripts)
    if not paths:
        raise CompileError("no Python scripts to compile")
    destination = Path(output) if output else _default_output(paths)
    project = Project()
    classes, units = _load_program(paths, warnings)
    instances = _program_instances(classes, units)
    stage = None
    sprites = []
    prepared = []
    loose_targets = []

    def take(target, owner):
        nonlocal stage
        if target.is_stage:
            if stage is not None:
                raise CompileError(f"{owner}: the project already has a stage")
            stage = target
        else:
            sprites.append(target)

    for inst in instances:
        if inst.sprite_name in project.instances:
            raise CompileError(f"{inst.path}:{inst.node.lineno}: sprite {inst.sprite_name} is already defined")
        project.instances[inst.sprite_name] = inst
        target = Target(project, inst.sprite_name, inst.blueprint.kind == "stage", inst.blueprint.path)
        target.prepare_sprite(inst)
        project.targets_by_name[inst.sprite_name] = target
        prepared.append((target, inst.path))
    for target, _owner in prepared:
        target.compile_sprite_scripts()
    for target, owner in prepared:
        take(target, owner)
    for path, loose, has_class in units:
        if has_class and not _has_code(loose) and not any(_is_target_function(stmt) for stmt in loose):
            continue
        for target in _compile_file(path, project, loose):
            loose_targets.append(target)
            take(target, path)
    named = {}
    for target in [item for item, _owner in prepared] + loose_targets:
        if target.name in named:
            raise CompileError(f"{target.path}: sprite {target.name} is already defined")
        named[target.name] = target
        target.add_remote_receivers()
    for target, _owner in prepared:
        target.finish_assets()
    if stage is None:
        stage = Target(project, "Stage", True, paths[0])
        stage.finish_assets()
    built = [stage.emit(0)]
    built.extend(sprite.emit(index) for index, sprite in enumerate(sprites, start=1))
    payload = {
        "targets": built,
        "monitors": project.monitors,
        "extensions": sorted(project.extensions),
        "meta": {"semver": "3.0.0", "vm": "3.0.0-kitty", "agent": "kitty"},
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("project.json", encoded)
        for name, data in project.assets.items():
            archive.writestr(name, data)
    return destination


def _script_paths(scripts):
    if isinstance(scripts, (str, Path)):
        scripts = [scripts]
    paths = []
    for item in scripts:
        path = Path(item)
        if not path.exists():
            raise CompileError(f"not found: {path}")
        if path.is_dir():
            found = sorted(file for file in path.glob("*.py") if file.name not in {"comp.py", "kitty.py", "decomp.py"})
            if not found:
                raise CompileError(f"no Python scripts in {path}")
            paths.extend(found)
        else:
            if not path.is_file():
                raise CompileError(f"Python script not found: {path}")
            paths.append(path)
    return paths


def _default_output(paths):
    if len(paths) == 1:
        return paths[0].with_suffix(".sb3")
    return Path("project.sb3")


def _compile_file(path, project, body=None):
    if body is None:
        source = path.read_text(encoding="utf-8-sig")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            raise CompileError(f"{path}:{exc.lineno}: {exc.msg}") from exc
        body = tree.body
    sprite_functions = []
    loose = []
    for stmt in body:
        if _is_target_function(stmt):
            sprite_functions.append(stmt)
        else:
            loose.append(stmt)
    targets = []
    file_is_stage = path.stem.lower() == "stage"
    if sprite_functions:
        for fn in sprite_functions:
            kind, name = _target_decorator(fn, path)
            target = Target(project, name or _safe_sprite_name(fn.name), kind == "stage", path)
            target.compile_body(fn.body)
            targets.append(target)
        if _has_code(loose):
            target = Target(project, _safe_sprite_name(path.stem), file_is_stage, path)
            target.compile_body(loose)
            targets.append(target)
    else:
        target = Target(project, "Stage" if file_is_stage else _safe_sprite_name(path.stem), file_is_stage, path)
        target.compile_body(body)
        targets.append(target)
    for target in targets:
        target.finish_assets()
    return targets


def _load_program(paths, warnings=None):
    parsed = []
    class_nodes = {}
    for path in paths:
        source = path.read_text(encoding="utf-8-sig")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            raise CompileError(f"{path}:{exc.lineno}: {exc.msg}") from exc
        parsed.append((path, tree))
        for stmt in tree.body:
            if isinstance(stmt, ast.ClassDef):
                if stmt.name in class_nodes:
                    other = class_nodes[stmt.name][1]
                    raise CompileError(f"{path}:{stmt.lineno}: class {stmt.name} is already defined in {other}")
                class_nodes[stmt.name] = (stmt, path)
    classes = {}
    for name, (node, path) in class_nodes.items():
        kind = _sprite_kind(name, class_nodes)
        if kind is None:
            continue
        if node.decorator_list:
            raise CompileError(f"{path}:{node.lineno}: sprite classes do not take decorators")
        classes[name] = SpriteClass(name, node, path, kind)
    for cls in classes.values():
        for base in _base_names(cls.node):
            if base in classes:
                cls.bases.append(classes[base])
    for cls in classes.values():
        _fill_class(cls)
    units = []
    for path, tree in parsed:
        aliases, imported, math_aliases, math_names = _module_imports(tree, path, warnings)
        loose = []
        decls = []
        file_classes = []
        has_class = False
        for stmt in tree.body:
            if isinstance(stmt, ast.ClassDef) and stmt.name in classes:
                classes[stmt.name].aliases = aliases
                classes[stmt.name].imported = imported
                classes[stmt.name].math_aliases = set(math_aliases)
                classes[stmt.name].math_names = dict(math_names)
                has_class = True
                file_classes.append(classes[stmt.name])
                continue
            if _instance_assign(stmt, classes, path) is not None:
                has_class = True
                continue
            loose.append(stmt)
        if file_classes:
            kept = []
            for stmt in loose:
                if _is_file_declaration(stmt, aliases, imported):
                    decls.append(stmt)
                else:
                    kept.append(stmt)
            loose = kept
            for cls in file_classes:
                cls.module_decls = decls
        units.append((path, loose, has_class))
    return classes, units


def _program_instances(classes, units):
    instances = []
    used = set()
    for path, _loose, _has_class in units:
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(path))
        for stmt in tree.body:
            inst = _instance_assign(stmt, classes, path)
            if inst is None:
                continue
            inst.path = path
            instances.append(inst)
            used.add(inst.blueprint.name)
    parents = set()
    for cls in classes.values():
        for base in cls.bases:
            parents.add(base.name)
    for cls in classes.values():
        if cls.name in used or cls.name in parents:
            continue
        instances.append(Instance(cls.name, cls, [], cls.node, cls.path))
        used.add(cls.name)
    return instances


def _instance_assign(stmt, classes, path):
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        return None
    if not isinstance(stmt.targets[0], ast.Name) or not isinstance(stmt.value, ast.Call):
        return None
    name = _class_name_of(stmt.value.func)
    if name not in classes:
        return None
    if stmt.value.keywords:
        raise CompileError(f"{path}:{stmt.lineno}: sprite constructors take plain values")
    args = []
    for arg in stmt.value.args:
        value = _constant(arg)
        if value is _NOT_CONSTANT:
            raise CompileError(f"{path}:{stmt.lineno}: sprite constructors take numbers, text, or lists")
        args.append(value)
    return Instance(stmt.targets[0].id, classes[name], args, stmt, path)


def _class_name_of(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _base_names(node):
    names = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute) and base.attr in {"Sprite", "Stage"}:
            names.append(base.attr)
        else:
            names.append(None)
    return names


def _sprite_kind(name, class_nodes, stack=()):
    if name == "Sprite":
        return "sprite"
    if name == "Stage":
        return "stage"
    if name in stack:
        raise CompileError(f"class {name} inherits itself")
    if name not in class_nodes:
        return None
    node, path = class_nodes[name]
    kinds = []
    for base in _base_names(node):
        kind = _sprite_kind(base, class_nodes, stack + (name,))
        if kind:
            kinds.append(kind)
    if not kinds:
        return None
    if len(set(kinds)) > 1:
        raise CompileError(f"{path}:{node.lineno}: a class cannot be both a sprite and the stage")
    return kinds[0]


def _fill_class(cls):
    methods = {}
    order = []
    seen = set()

    def absorb(parent):
        if parent.name in seen:
            return
        seen.add(parent.name)
        for base in parent.bases:
            absorb(base)
        for stmt in parent.node.body:
            if not isinstance(stmt, ast.FunctionDef) or stmt.name == "__init__":
                continue
            if stmt.name in methods:
                order[:] = [stmt if item.name == stmt.name else item for item in order]
            else:
                order.append(stmt)
            methods[stmt.name] = stmt

    absorb(cls)
    cls.methods = methods
    cls.method_order = order
    for stmt in cls.node.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
            cls.init = stmt


def _lineage(cls):
    order = []
    seen = set()

    def walk(item):
        if item.name in seen:
            return
        seen.add(item.name)
        for base in item.bases:
            walk(base)
        order.append(item)

    walk(cls)
    return order


def _method_owner(cls, fn):
    for item in reversed(_lineage(cls)):
        for stmt in item.node.body:
            if stmt is fn:
                return item
    return cls


def _find_super_method(cls, name):
    for base in cls.bases:
        fn = base.methods.get(name)
        if fn is not None:
            return _method_owner(base, fn), fn
    return None


def _kitty_called(func, aliases, imported):
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in aliases:
        return func.attr
    if isinstance(func, ast.Name) and func.id in imported:
        return func.id
    return None


def _is_file_declaration(stmt, aliases, imported):
    call = None
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.value, ast.Call):
        call = stmt.value
    elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        call = stmt.value
    if call is not None:
        return _kitty_called(call.func, aliases, imported) in DECLARATIONS
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
        return False
    try:
        value = _constant(stmt.value)
    except ValueError:
        return True
    return value is not _NOT_CONSTANT and not isinstance(value, bool)


def _module_imports(tree, path, warnings=None):
    aliases = {"kitty"}
    imported = set()
    math_aliases = set()
    math_names = {}
    for stmt in tree.body:
        _note_import(stmt, path, aliases, imported, math_aliases, math_names, warnings)
    if warnings is not None:
        for stmt in ast.walk(tree):
            if not isinstance(stmt, ast.FunctionDef) or not _is_ignored_function(stmt):
                continue
            for nested in ast.walk(stmt):
                if isinstance(nested, ast.Import):
                    for alias in nested.names:
                        if alias.name not in {"kitty", "math"}:
                            message = f"{path}:{nested.lineno}: {alias.name} imported and cannot be compiled"
                            if message not in warnings:
                                warnings.append(message)
                elif isinstance(nested, ast.ImportFrom):
                    if nested.module not in {"kitty", "math"}:
                        message = f"{path}:{nested.lineno}: {nested.module} imported and cannot be compiled"
                        if message not in warnings:
                            warnings.append(message)
    return aliases, imported, math_aliases, math_names


_MATH_FUNCS = {
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
    "asin": "asin",
    "acos": "acos",
    "atan": "atan",
    "sqrt": "sqrt",
    "floor": "floor",
    "ceil": "ceiling",
    "fabs": "abs",
    "log": "ln",
    "log10": "log",
    "exp": "e ^",
}


def _note_import(stmt, path, aliases, imported, math_aliases, math_names, warnings=None):
    if isinstance(stmt, ast.Import):
        for alias in stmt.names:
            if alias.name == "kitty":
                aliases.add(alias.asname or alias.name)
            elif alias.name == "math":
                math_aliases.add(alias.asname or "math")
            else:
                if warnings is not None:
                    message = f"{path}:{stmt.lineno}: {alias.name} imported and cannot be compiled"
                    if message not in warnings:
                        warnings.append(message)
        return
    if isinstance(stmt, ast.ImportFrom):
        if stmt.module == "kitty":
            for alias in stmt.names:
                imported.add(alias.asname or alias.name)
            return
        if stmt.module == "math":
            for alias in stmt.names:
                if alias.name not in _MATH_FUNCS:
                    raise CompileError(f"{path}:{stmt.lineno}: math.{alias.name} has no Scratch block")
                math_names[alias.asname or alias.name] = _MATH_FUNCS[alias.name]
            return
        if warnings is not None:
            message = f"{path}:{stmt.lineno}: {stmt.module} imported and cannot be compiled"
            if message not in warnings:
                warnings.append(message)


def _signature(label, params):
    pieces = [label]
    for param in params:
        pieces.append("%b" if param.boolean else "%s")
    return " ".join(pieces)


def _input_default(param):
    if param.boolean:
        return "true" if param.default is True else "false"
    if param.default is NO_DEFAULT or param.default is None:
        return ""
    return str(param.default)


def _default_value(compiler, default):
    if default is None:
        return NO_DEFAULT
    try:
        value = _constant(default)
    except ValueError as exc:
        compiler._error(default, str(exc))
    if value is _NOT_CONSTANT:
        compiler._error(default, "default values must be numbers, text, or True/False")
    return value


def _split_params(fn, path, as_method):
    if fn.args.posonlyargs:
        raise CompileError(f"{path}:{fn.lineno}: write parameters without /")
    args = list(fn.args.args)
    if as_method:
        if not args or args[0].arg != "self":
            raise CompileError(f"{path}:{fn.lineno}: the first parameter must be named self")
        args = args[1:]
    defaults = [None] * (len(args) - len(fn.args.defaults)) + list(fn.args.defaults)
    pairs = list(zip(args, defaults))
    kwonly = list(zip(fn.args.kwonlyargs, fn.args.kw_defaults))
    star = fn.args.vararg.arg if fn.args.vararg else None
    kw = fn.args.kwarg.arg if fn.args.kwarg else None
    return pairs, star, kw, kwonly


def _single_return_exprs(fn):
    found = []

    def walk(stmts):
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                if isinstance(stmt.value, (ast.Tuple, ast.List)):
                    return True
                found.append(stmt.value)
            for body in _flow_bodies(stmt):
                if walk(body):
                    return True
        return False

    if walk(list(fn.body)):
        return None
    return found


def _return_widths(fn):
    widths = []

    def walk(stmts):
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                if isinstance(stmt.value, (ast.Tuple, ast.List)):
                    widths.append(len(stmt.value.elts))
                else:
                    widths.append(1)
            for body in _flow_bodies(stmt):
                walk(body)

    walk(list(fn.body))
    return widths


def _nested_defs(stmts):
    found = []
    for stmt in stmts:
        if isinstance(stmt, ast.FunctionDef):
            found.append(stmt)
            continue
        for body in _flow_bodies(stmt):
            found.extend(_nested_defs(body))
    return found


def _method_params(fn, path):
    if fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs:
        raise CompileError(f"{path}:{fn.lineno}: methods use plain parameters")
    args = list(fn.args.args)
    if not args or args[0].arg != "self":
        raise CompileError(f"{path}:{fn.lineno}: the first parameter must be named self")
    defaults = [None] * (len(args) - len(fn.args.defaults)) + list(fn.args.defaults)
    return list(zip(args[1:], defaults[1:]))


def _init_binding(fn, args, node, path, class_name):
    if fn is None:
        if args:
            raise CompileError(f"{path}:{getattr(node, 'lineno', '?')}: {class_name} does not take values")
        return {}
    params = _method_params(fn, path)
    if len(args) > len(params):
        raise CompileError(f"{path}:{getattr(node, 'lineno', '?')}: {class_name} takes {len(params)} values")
    binding = {}
    for index, (arg, default) in enumerate(params):
        if index < len(args):
            binding[arg.arg] = args[index]
            continue
        if default is None:
            raise CompileError(
                f"{path}:{getattr(node, 'lineno', '?')}: {class_name} needs {arg.arg}. Write name = {class_name}(...)"
            )
        value = _constant(default)
        if value is _NOT_CONSTANT:
            raise CompileError(f"{path}:{default.lineno}: default values must be numbers, text, or True/False")
        binding[arg.arg] = value
    return binding


def _fold_binding(node, binding):
    if isinstance(node, ast.Name) and node.id in binding:
        return binding[node.id]
    if isinstance(node, ast.Constant) and isinstance(node.value, (bool, int, float, str)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _fold_binding(node.operand, binding)
        if _is_number(inner):
            return -inner
        return _NOT_CONSTANT
    if isinstance(node, ast.List):
        items = []
        for elt in node.elts:
            item = _fold_binding(elt, binding)
            if item is _NOT_CONSTANT or isinstance(item, bool):
                return _NOT_CONSTANT
            items.append(item)
        return items
    if isinstance(node, ast.Dict):
        return _dict_from(node, lambda item: _fold_binding(item, binding))
    return _NOT_CONSTANT


def _is_super_call(expr):
    if not isinstance(expr, ast.Call) or not isinstance(expr.func, ast.Attribute):
        return False
    inner = expr.func.value
    if not isinstance(inner, ast.Call) or inner.args or inner.keywords:
        return False
    return isinstance(inner.func, ast.Name) and inner.func.id == "super"


def _is_self_assign(stmt):
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        return False
    target = stmt.targets[0]
    return isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self"


def _is_target_function(stmt):
    if not isinstance(stmt, ast.FunctionDef) or not stmt.decorator_list:
        return False
    name = _decorator_name(stmt.decorator_list[0])
    return name in {"sprite", "stage"}


def _is_ignored_function(fn):
    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    for decorator in fn.decorator_list:
        name = _decorator_name(decorator)
        if name == "ignore":
            return True
    return False


def _target_decorator(fn, path):
    if len(fn.decorator_list) != 1:
        raise CompileError(f"{path}:{fn.lineno}: a sprite function takes one decorator")
    dec = fn.decorator_list[0]
    name = _decorator_name(dec)
    if name == "stage":
        return "stage", "Stage"
    label = fn.name
    if isinstance(dec, ast.Call) and dec.args:
        value = _constant(dec.args[0])
        if not isinstance(value, str):
            raise CompileError(f"{path}:{fn.lineno}: sprite name must be text")
        label = value
    return "sprite", label


def _decorator_name(dec):
    node = dec.func if isinstance(dec, ast.Call) else dec
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _has_code(stmts):
    for stmt in stmts:
        if isinstance(stmt, ast.Import) or isinstance(stmt, ast.ImportFrom):
            continue
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            continue
        return True
    return False


def _safe_sprite_name(name):
    cleaned = name.strip() or "sprite"
    return cleaned


class Target:
    def __init__(self, project, name, is_stage, path):
        self.project = project
        self.name = name
        self.is_stage = is_stage
        self.path = path
        self.blocks = {}
        self.symbols = {}
        self.ignored_names = set()
        self.scratch_vars = {}
        self.scratch_lists = {}
        self.local_vars = {}
        self.local_lists = {}
        self.procedures = {}
        self.costumes = []
        self.sounds = []
        self.y = 48
        self.scope = []
        self.aliases = {"kitty"}
        self.imported = set()
        self.math_aliases = set()
        self.math_names = {}
        self.receiver = None
        self.skip_self = False
        self.blueprint = None
        self.instance_name = None
        self.super_class = None
        self.init_runtime = []
        self.super_procs = []
        self.prepended_init = False
        self.hoist_stack = []
        self.return_proc = None
        self.needs_done = False
        self.done_name = None
        self._temps = 0
        self._flow = 0
        self._iter = 0
        self._lambda_n = 0
        self._lambda_found = []
        self._stub_n = 0
        self.frame_arg = None
        self.scope_args = []
        self.frame_lists = None
        self.span_lists = None
        self.current_proc = None
        self.frame_depth = 0
        self.heaps = {}
        self.ephemeral_stack = []

    def prepare_sprite(self, inst):
        cls = inst.blueprint
        self.receiver = "self"
        self.skip_self = True
        self.blueprint = cls
        self.instance_name = inst.sprite_name
        self.super_class = cls
        self.aliases = set(cls.aliases)
        self.imported = set(cls.imported)
        self.math_aliases = set()
        self.math_names = {}
        for item in _lineage(cls):
            self.math_aliases.update(item.math_aliases)
            self.math_names.update(item.math_names)
        self._apply_module_decls()
        binding = _init_binding(cls.init, inst.const_args, inst.node, inst.path, cls.name)
        decls = {}
        for item in _lineage(cls):
            for stmt in item.node.body:
                self._class_statement(stmt, decls)
        runtime = []
        self._walk_init(cls, binding, decls, runtime, set())
        for name, (value, node) in decls.items():
            if isinstance(value, DictLiteral):
                self._bind_dict(name, name, value.pairs, False, False, node, seed=True)
            elif isinstance(value, list):
                self._bind_list(
                    name, name, value, False, False, node,
                    frozen=isinstance(value, FrozenList),
                    unique=isinstance(value, UniqueList),
                    ref=True, seed=True,
                )
            else:
                self._bind_var(name, name, value, False, False, node)
        for fn in cls.method_order:
            if self._function_kind(fn)[0] == "block":
                self._register_proc(fn)
        self.super_procs = self._register_super_procs(cls)
        self.init_runtime = runtime
        found = []
        for item in _lineage(cls):
            self._gather_lambdas(item.node.body, found)
        self._lambda_found.extend(found)
        self._finish_lambdas()

    def compile_sprite_scripts(self):
        for parent, fn, proc in self.super_procs:
            previous = self.super_class
            self.super_class = parent
            try:
                self._compile_proc_body(fn, proc)
            finally:
                self.super_class = previous
        for fn in self.blueprint.method_order:
            if _is_ignored_function(fn):
                self.ignored_names.add(fn.name)
                continue
            previous = self.super_class
            self.super_class = _method_owner(self.blueprint, fn)
            try:
                self._compile_function(fn)
            finally:
                self.super_class = previous
        if self.init_runtime and not self.prepended_init:
            heads = self._compile_init_runtime()
            if heads:
                hat = self._new_block("event_whenflagclicked")
                self._link([hat, *heads], None)
                self._place(hat)
            self.prepended_init = True

    def _apply_module_decls(self):
        for stmt in self.blueprint.module_decls:
            key = id(stmt)
            if key in self.project.applied_decls:
                symbol = self.project.applied_decls[key]
                py_name = self._assigned_name(stmt)
                if py_name and symbol is not None and py_name not in self.symbols:
                    self.symbols[py_name] = symbol
                    if isinstance(symbol, Map):
                        self.symbols[f".keys.{py_name}"] = symbol.keys
                continue
            self._declare(stmt)
            py_name = self._assigned_name(stmt)
            self.project.applied_decls[key] = self.symbols.get(py_name) if py_name else None

    def _class_statement(self, stmt, decls):
        if isinstance(stmt, (ast.FunctionDef, ast.Pass)):
            return
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            return
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            if isinstance(stmt.value, ast.Lambda):
                return
            self._class_attribute(stmt.targets[0].id, stmt.value, stmt, decls)
            return
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value is not None:
            self._class_attribute(stmt.target.id, stmt.value, stmt, decls)
            return
        call = self._decl_call(stmt)
        if call is not None and self._kitty_name(call.func) in DECLARATIONS:
            self._declare_call(stmt, call)
            return
        self._error(stmt, "this does not belong in a sprite class")

    def _class_attribute(self, name, value_node, stmt, decls):
        try:
            value = _constant(value_node)
        except ValueError as exc:
            self._error(stmt, str(exc))
        if value is _NOT_CONSTANT or isinstance(value, bool):
            self._error(stmt, "class attributes must be numbers, text, lists, or dictionaries")
        decls[name] = (value, stmt)

    def _walk_init(self, cls, binding, decls, runtime, seen):
        fn = cls.init
        if fn is None or cls.name in seen:
            return
        seen.add(cls.name)
        for stmt in fn.body:
            if isinstance(stmt, ast.Expr) and _is_super_call(stmt.value) and stmt.value.func.attr == "__init__":
                if not cls.bases:
                    continue
                parent = cls.bases[0]
                parent_binding = self._binding_from_super(parent, stmt.value, binding)
                self._walk_init(parent, parent_binding, decls, runtime, seen)
                continue
            if _is_self_assign(stmt):
                try:
                    folded = _fold_binding(stmt.value, binding)
                except ValueError as exc:
                    self._error(stmt, str(exc))
                if folded is not _NOT_CONSTANT and not isinstance(folded, bool):
                    decls[stmt.targets[0].attr] = (folded, stmt)
                    continue
            if isinstance(stmt, ast.Pass):
                continue
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                continue
            runtime.append((stmt, dict(binding), cls))

    def _binding_from_super(self, parent, call, binding):
        if call.keywords:
            self._error(call, "super().__init__ takes plain values")
        args = []
        for arg in call.args:
            folded = _fold_binding(arg, binding)
            if folded is _NOT_CONSTANT:
                self._error(arg, "super().__init__ arguments must be numbers, text, or constructor parameters")
            args.append(folded)
        return _init_binding(parent.init, args, call, parent.path, parent.name)

    def _register_super_procs(self, cls):
        pending = []
        seen = set()

        def scan(owner, fn):
            for node in ast.walk(fn):
                if not _is_super_call(node) or node.func.attr == "__init__":
                    continue
                found = _find_super_method(owner, node.func.attr)
                if found is None:
                    self._error(node, f"no parent method {node.func.attr}")
                parent, parent_fn = found
                if self._function_kind(parent_fn)[0] != "block":
                    self._error(node, f"{node.func.attr} is an event script")
                key = f"{parent.name}.{parent_fn.name}"
                if key in seen:
                    continue
                seen.add(key)
                pending.append((key, parent, parent_fn))
                scan(parent, parent_fn)

        for fn in cls.method_order:
            scan(_method_owner(cls, fn), fn)
        if cls.init is not None:
            scan(cls, cls.init)
        compiled = []
        for key, parent, fn in pending:
            label = f"{parent.name} {fn.name.replace('_', ' ')}"
            proc = self._register_proc(fn, display=label, proc_key=key)
            compiled.append((parent, fn, proc))
        return compiled

    def _compile_init_runtime(self):
        heads = []
        for stmt, binding, cls in self.init_runtime:
            self.scope.append({name: Lit(value) for name, value in binding.items()})
            previous = self.super_class
            self.super_class = cls
            try:
                for piece in self._lower_control([stmt]):
                    heads.extend(self._compile_stmt(piece))
            finally:
                self.scope.pop()
                self.super_class = previous
        return heads

    def add_remote_receivers(self):
        if self.instance_name is None:
            return
        for sprite_name, method in sorted(self.project.remote_uses):
            if sprite_name == self.instance_name:
                self._add_receiver(method)

    def _add_receiver(self, method):
        message = f"{self.instance_name}.{method}"
        hat = self._new_block("event_whenbroadcastreceived")
        name, bid = self._broadcast(message)
        self.blocks[hat]["fields"]["BROADCAST_OPTION"] = [name, bid]
        proc = self.procedures.get(method)
        if proc is not None:
            block = self._new_block("procedures_call")
            self.blocks[block]["mutation"] = _mutation(
                proccode=proc.proccode,
                argumentids=[param.arg_id for param in proc.params],
                warp=proc.warp,
            )
            for index, param in enumerate(proc.params):
                var = self._find_var(f"{message}.{index}")
                value = Value("var", var)
                if param.boolean:
                    self._error(self.blueprint.node, "boolean inputs cannot be sent to another sprite")
                self._apply_slot(block, param.arg_id, "text", value, self.blueprint.node)
            body = [block]
        elif method in BLOCKS and BLOCKS[method].shape == "stack":
            spec = BLOCKS[method]
            block = self._new_block(spec.opcode)
            if spec.extension:
                self.project.extensions.add(spec.extension)
            for scratch_name, raw in spec.fixed_fields:
                self.blocks[block]["fields"][scratch_name] = [raw, None]
            for index, param in enumerate(spec.params):
                _py, scratch, slot, *_rest = param
                if slot in {"variable", "list", "boolean"} or slot.startswith("field:"):
                    self._error(self.blueprint.node, f"{method} cannot be called on another sprite")
                var = self._find_var(f"{message}.{index}")
                self._apply_slot(block, scratch, slot, Value("var", var), self.blueprint.node)
            body = [block]
        else:
            self._error(self.blueprint.node, f"cannot receive {method}")
        self._link([hat, *body], None)
        self._place(hat)

    def compile_body(self, stmts):
        self._read_imports(stmts)
        declarations, rest = self._split(stmts)
        for stmt in declarations:
            self._declare(stmt)
        self._collect_procedures(rest)
        self._gather_lambdas(rest, self._lambda_found)
        self._finish_lambdas()
        buffer = []
        for stmt in rest:
            if isinstance(stmt, ast.Import) or isinstance(stmt, ast.ImportFrom) or isinstance(stmt, ast.Pass):
                continue
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                continue
            if isinstance(stmt, ast.ClassDef):
                self._error(stmt, "classes must inherit kitty.Sprite or kitty.Stage")
            if isinstance(stmt, ast.FunctionDef):
                if _is_ignored_function(stmt):
                    self._flush_script(buffer)
                    buffer = []
                    self.ignored_names.add(stmt.name)
                    continue
                self._flush_script(buffer)
                buffer = []
                self._compile_function(stmt)
            else:
                buffer.append(stmt)
        self._flush_script(buffer)

    def _finish_results(self, proc):
        if proc.results or proc.result_list is not None or proc.result_dict is not None:
            return
        proc.yields = None
        if proc.returns and proc.returns != "boolean" and proc.fn is not None:
            proc.yields = self._payload_kind(proc.fn)
        saved = self.frame_arg
        self.frame_arg = None
        try:
            if proc.yields == "list":
                proc.result_list = self._bind_list(
                    None, f".result {proc.label}", [], False, False, proc.fn, keep_local=True, frame_items=False, ref=True,
                )
            elif proc.yields == "dict":
                proc.result_dict = self._bind_dict(None, f".result {proc.label}", [], False, False, proc.fn)
            else:
                proc.results = []
                count = proc.return_count or 1
                for index in range(count):
                    scratch = f".result {proc.label}" if count == 1 else f".result {proc.label} {index + 1}"
                    proc.results.append(self._bind_var(None, scratch, 0, False, False, proc.fn))
                proc.result = proc.results[0]
        finally:
            self.frame_arg = saved

    def _payload_kind(self, fn, seen=None):
        exprs = _single_return_exprs(fn)
        if not exprs:
            return None
        seen = set() if seen is None else set(seen)
        if fn in seen:
            return None
        seen.add(fn)
        kinds = []
        for expr in exprs:
            kind = self._expr_payload(expr, fn, seen)
            if kind:
                kinds.append(kind)
        if not kinds:
            return None
        if len(set(kinds)) != 1:
            self._error(fn, "return the same kind of value from every return")
        kind = kinds[0]
        return kind if kind in {"list", "dict"} else None

    def _expr_payload(self, node, fn, seen):
        if isinstance(node, ast.Name):
            assigned, _explicit, _nonlocals = _scan_bindings(list(fn.body), set(), self._call_payload(fn, seen))
            kind = assigned.get(node.id)
            if kind in {"list", "tuple", "set"}:
                return "list"
            if kind == "dict":
                return "dict"
            return "number"
        if isinstance(node, ast.Dict):
            return "dict"
        if isinstance(node, (ast.ListComp, ast.SetComp)):
            return "list"
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            return "list"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"list", "tuple", "set"} and not node.keywords:
                return "list"
            callee = self._find_fn(node.func.id, fn)
            if callee is None or callee in seen:
                return None
            return self._payload_kind(callee, seen) or "number"
        return "number"

    def _call_payload(self, fn, seen):
        def payload(value):
            if not isinstance(value, ast.AST):
                return None
            if isinstance(value, ast.Dict):
                return "dict"
            if isinstance(value, ast.ListComp):
                return "list"
            if isinstance(value, ast.SetComp):
                return "set"
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
                if value.func.id in {"list", "tuple", "set"} and not value.keywords:
                    return value.func.id
                callee = self._find_fn(value.func.id, fn)
                if callee is not None and callee in seen:
                    return "skip"
                if callee is not None:
                    found = self._payload_kind(callee, seen)
                    if found in {"list", "dict"}:
                        return found
            return None
        return payload

    def _find_fn(self, name, owner):
        proc = self.procedures.get(name)
        if not isinstance(proc, Proc):
            symbol = self.symbols.get(name)
            proc = symbol if isinstance(symbol, Proc) else None
        if isinstance(proc, Proc) and proc.fn is not None:
            return proc.fn
        if isinstance(owner, ast.FunctionDef):
            for nested in _nested_defs(owner.body):
                if nested.name == name:
                    return nested
        return None

    def finish_assets(self):
        if self.is_stage and not self.costumes:
            self._add_default_backdrop()
        if not self.is_stage and not self.costumes:
            self._add_default_costume()

    def emit(self, layer):
        data = {
            "isStage": self.is_stage,
            "name": "Stage" if self.is_stage else self.name,
            "variables": {var.vid: [var.name, var.initial] for var in self._emitted_vars()},
            "lists": {lst.lid: [lst.name, lst.initial] for lst in self._emitted_lists()},
            "broadcasts": self.project.broadcasts if self.is_stage else {},
            "blocks": self.blocks,
            "comments": {},
            "currentCostume": 0,
            "costumes": self.costumes,
            "sounds": self.sounds,
            "volume": 100,
            "layerOrder": layer,
        }
        if self.is_stage:
            data.update({
                "tempo": 60,
                "videoTransparency": 50,
                "videoState": "on",
                "textToSpeechLanguage": None,
            })
        else:
            data.update({
                "visible": True,
                "x": 0,
                "y": 0,
                "size": 100,
                "direction": 90,
                "draggable": False,
                "rotationStyle": "all around",
            })
        return data

    def _emitted_vars(self):
        if self.is_stage:
            by_id = dict(self.local_vars)
            by_id.update(self.project.shared_vars)
            return list(by_id.values())
        return list(self.local_vars.values())

    def _emitted_lists(self):
        if self.is_stage:
            by_id = dict(self.local_lists)
            by_id.update(self.project.shared_lists)
            return list(by_id.values())
        return list(self.local_lists.values())

    def _read_imports(self, stmts):
        for stmt in stmts:
            _note_import(stmt, self.path, self.aliases, self.imported, self.math_aliases, self.math_names)

    def _split(self, stmts):
        declarations = []
        rest = []
        declared = set()
        for stmt in stmts:
            if self._is_declaration(stmt, declared):
                declarations.append(stmt)
                target = self._assigned_name(stmt)
                if target:
                    declared.add(target)
            else:
                rest.append(stmt)
        return declarations, rest

    def _is_declaration(self, stmt, declared):
        call = self._decl_call(stmt)
        if call is not None and self._kitty_name(call.func) in DECLARATIONS:
            return True
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            return False
        if not isinstance(stmt.targets[0], ast.Name):
            return False
        if stmt.targets[0].id in declared or stmt.targets[0].id in self.symbols:
            return False
        if isinstance(stmt.value, ast.Dict):
            try:
                value = _constant(stmt.value)
            except ValueError as exc:
                self._error(stmt, str(exc))
            return value is not _NOT_CONSTANT
        try:
            value = _constant(stmt.value)
        except ValueError as exc:
            self._error(stmt, str(exc))
        return value is not _NOT_CONSTANT

    def _declare(self, stmt):
        call = self._decl_call(stmt)
        if call is not None and self._kitty_name(call.func) in DECLARATIONS:
            self._declare_call(stmt, call)
            return
        name = stmt.targets[0].id
        try:
            value = _constant(stmt.value)
        except ValueError as exc:
            self._error(stmt, str(exc))
        if isinstance(value, DictLiteral):
            self._bind_dict(name, name, value.pairs, False, False, stmt, seed=True)
        elif isinstance(value, list):
            self._bind_list(
                name, name, value, False, False, stmt,
                frozen=isinstance(value, FrozenList),
                unique=isinstance(value, UniqueList),
                ref=True, seed=True,
            )
        elif isinstance(value, (int, float, str)) and not isinstance(value, bool):
            self._bind_var(name, name, value, False, False, stmt)
        else:
            self._error(stmt, "start a variable with a number or text, a list with [], or a dictionary with {}")

    def _declare_call(self, stmt, call):
        kind = self._kitty_name(call.func)
        args, kwargs = self._literal_call(call)
        py_name = self._assigned_name(stmt)
        if kind == "variable":
            scratch = args[0] if args else kwargs.get("name")
            initial = args[1] if len(args) > 1 else kwargs.get("value", 0)
            if not isinstance(scratch, str):
                self._error(call, "variable name must be text")
            if isinstance(initial, bool) or not isinstance(initial, (int, float, str)):
                self._error(call, "variable value must be a number or text")
            self._bind_var(py_name or scratch, scratch, initial, bool(kwargs.get("shared", False)), bool(kwargs.get("show", False)), call)
        elif kind == "list":
            scratch = args[0] if args else kwargs.get("name")
            initial = args[1] if len(args) > 1 else kwargs.get("value", [])
            if initial is None:
                initial = []
            if not isinstance(scratch, str) or not isinstance(initial, list):
                self._error(call, "list declaration needs a name and a list of numbers or text")
            concrete = bool(kwargs.get("scratch", False))
            self._bind_list(
                py_name or scratch, scratch, initial, bool(kwargs.get("shared", False)), bool(kwargs.get("show", False)), call,
                ref=not concrete, seed=not concrete,
            )
        elif kind == "dict":
            scratch = args[0] if args else kwargs.get("name")
            initial = args[1] if len(args) > 1 else kwargs.get("value", None)
            if not isinstance(scratch, str):
                self._error(call, "dictionary name must be text")
            if initial is None:
                initial = DictLiteral([])
            if not isinstance(initial, DictLiteral):
                self._error(call, "dictionary value must look like {key: value}")
            self._bind_dict(
                py_name or scratch,
                scratch,
                initial.pairs,
                bool(kwargs.get("shared", False)),
                bool(kwargs.get("show", False)),
                call,
                seed=True,
            )
        elif kind == "sprite_name":
            scratch = args[0] if args else kwargs.get("name")
            if not isinstance(scratch, str):
                self._error(call, "sprite name must be text")
            self.name = scratch
        elif kind in {"costume", "sound", "backdrop"}:
            file_name = args[0] if args else kwargs.get("path")
            label = kwargs.get("name")
            if not isinstance(file_name, str):
                self._error(call, f"{kind} needs a file path")
            self._load_media(kind, file_name, label, call)
        else:
            self._error(call, f"unknown declaration {kind}")

    def _bind_var(self, py_name, scratch, initial, shared, show, node, keep_local=False):
        if scratch in self.scratch_vars or scratch in self.project.shared_vars_by_name():
            self._error(node, f"variable {scratch!r} is already declared")
        if self.is_stage and not keep_local:
            shared = True
        var = Var(scratch, self.project.ids.var(), _scratch_literal(initial), shared)
        if keep_local and self.frame_arg is not None:
            lst = self._bind_list(None, scratch, [], False, False, node, keep_local=True, frame_items=False)
            var.frame = (lst, self.frame_arg)
            if self.frame_lists is not None:
                self.frame_lists.append(lst)
            self.scratch_vars[scratch] = var
            return var
        self.scratch_vars[scratch] = var
        if py_name:
            if py_name in self.symbols:
                self._error(node, f"{py_name} is already defined")
            self.symbols[py_name] = var
        if shared:
            self.project.shared_vars[var.vid] = var
        else:
            self.local_vars[var.vid] = var
        if show:
            self.project.monitors.append(self._monitor("data_variable", "VARIABLE", var, False))
        return var

    def _bind_list(self, py_name, scratch, initial, shared, show, node, frozen=False, unique=False, keep_local=False, frame_items=None, ref=False, seed=False):
        try:
            shape, atoms = _flatten_list(initial)
        except ValueError as exc:
            self._error(node, str(exc))
        if ref:
            return self._bind_ref_list(
                py_name, scratch, atoms, shared, show, node,
                frozen=frozen, unique=unique, keep_local=keep_local, seed=seed, shape=shape,
            )
        items = [_scratch_literal(item) for item in atoms]
        if self.is_stage and not keep_local:
            shared = True
        lst = Lst(scratch, self.project.ids.lst(), items, shared, shape)
        lst.frozen = frozen
        lst.unique = unique
        self.scratch_lists[scratch] = lst
        if py_name:
            if py_name in self.symbols:
                self._error(node, f"{py_name} is already defined")
            self.symbols[py_name] = lst
        if shared:
            self.project.shared_lists[lst.lid] = lst
        else:
            self.local_lists[lst.lid] = lst
        if show:
            self.project.monitors.append(self._monitor("data_listcontents", "LIST", lst, True))
        if frame_items is None:
            frame_items = keep_local and self.frame_arg is not None
        if frame_items:
            self._attach_span(lst, node)
        return lst

    def _bind_dict(self, py_name, scratch, pairs, shared, show, node, local=False, seed=False):
        if f".id {scratch}" in self.scratch_vars:
            self._error(node, f"dictionary {scratch} is already declared")
        ident = self._bind_var(None, f".id {scratch}", 0, shared, False, node, keep_local=local)
        heap = self._ensure_heap("dict", node)
        key_list = self._ref_view(f"{scratch} keys", heap["columns"][0], ident, "dict")
        value_list = self._ref_view(f"{scratch} values", heap["columns"][1], ident, "dict")
        mapping = Map(scratch, key_list, value_list)
        mapping.ident = ident
        mapping.ref_kind = "dict"
        if py_name:
            if py_name in self.symbols:
                self._error(node, f"{py_name} is already defined")
            self.symbols[py_name] = mapping
            self.symbols[f".keys.{py_name}"] = key_list
        if seed:
            self._seed_columns(heap, [(heap["columns"][0], [key for key, _value in pairs]), (heap["columns"][1], [value for _key, value in pairs])], ident)
        return mapping

    def _bind_ref_list(self, py_name, scratch, atoms, shared, show, node, frozen=False, unique=False, keep_local=False, seed=False, shape=()):
        if f".id {scratch}" in self.scratch_vars:
            self._error(node, f"{scratch} is already defined")
        ident = self._bind_var(None, f".id {scratch}", 0, shared, show, node, keep_local=keep_local)
        heap = self._ensure_heap("list", node)
        lst = self._ref_view(scratch, heap["columns"][0], ident, "list", frozen=frozen, unique=unique, shape=shape)
        if py_name:
            if py_name in self.symbols:
                self._error(node, f"{py_name} is already defined")
            self.symbols[py_name] = lst
        if seed:
            pairs = [(heap["columns"][0], atoms)]
            if shape:
                pairs.append((heap["shape"], list(shape)))
            self._seed_columns(heap, pairs, ident)
        return lst

    def _ref_view(self, name, data, ident, kind, frozen=False, unique=False, shape=()):
        lst = Lst(name, ident.vid, [], False, shape)
        lst.ident = ident
        lst.heap = data
        lst.ref_kind = kind
        lst.frozen = frozen
        lst.unique = unique
        return lst

    def _ensure_heap(self, kind, node):
        if kind in self.heaps:
            return self.heaps[kind]
        saved = (self.frame_arg, self.frame_lists, self.span_lists)
        self.frame_arg = None
        self.frame_lists = None
        self.span_lists = None
        try:
            if kind == "list":
                columns = [
                    self._bind_list(None, ".objects", [], False, False, node, keep_local=True),
                    self._bind_list(None, ".lshape", [], False, False, node, keep_local=True),
                ]
            else:
                columns = [
                    self._bind_list(None, ".dkeys", [], False, False, node, keep_local=True),
                    self._bind_list(None, ".dvals", [], False, False, node, keep_local=True),
                ]
            for column in columns:
                self._attach_span(column, node)
            refs = self._bind_list(None, f".{kind} refs", [], False, False, node, keep_local=True)
            free = self._bind_list(None, f".{kind} free", [], False, False, node, keep_local=True)
            nxt = self._bind_var(None, f".{kind} next", 0, False, False, node, keep_local=True)
            slot = self._bind_var(None, f".{kind} slot", 0, False, False, node, keep_local=True)
        finally:
            self.frame_arg, self.frame_lists, self.span_lists = saved
        heap = {
            "kind": kind,
            "columns": columns,
            "refs": refs,
            "free": free,
            "next": nxt,
            "slot": slot,
            "ops": {},
            "shape": columns[1] if kind == "list" else None,
        }
        self.heaps[kind] = heap
        self._define_ref_ops(heap, node)
        return heap

    def _seed_columns(self, heap, columns, ident):
        provided = {id(data): items for data, items in columns}
        number = len(heap["refs"].initial) + 1
        for data in heap["columns"]:
            items = provided.get(id(data), [])
            starts, lengths, _owner = data.span
            literals = [_scratch_literal(item) for item in items]
            if literals:
                start = len(data.initial) + 1
                data.initial.extend(literals)
            else:
                start = 0
            starts.initial.append(start)
            lengths.initial.append(len(literals))
        heap["refs"].initial.append(1)
        heap["next"].initial = number
        ident.initial = _scratch_literal(number)

    def _define_ref_ops(self, heap, node):
        kind = heap["kind"]
        ident = Arg("id", "arg0", False)
        heap["ops"]["incref"] = self._ref_proc(f".ref {kind} incref", [ident], lambda: self._ref_incref_body(heap, ident, node), node)
        heap["ops"]["decref"] = self._ref_proc(f".ref {kind} decref", [ident], lambda: self._ref_decref_body(heap, ident, node), node)
        heap["ops"]["alloc"] = self._ref_proc(f".ref {kind} alloc", [], lambda: self._ref_alloc_body(heap, node), node)
        heap["ops"]["retain"] = self._ref_proc(f".ref {kind} retain", [ident], lambda: self._ref_retain_body(heap, ident, node), node)

    def _ref_proc(self, label, params, build, node):
        proc = Proc(label, params, True, _signature(label, params))
        saved = self.frame_arg
        self.frame_arg = None
        try:
            body = build()
        finally:
            self.frame_arg = saved
        self._define_stack(proc, body, node)
        return proc

    def _ref_incref_body(self, heap, ident, node):
        current = self._raw_item(heap["refs"], Value("arg", ident), node)
        bumped = self._binary("operator_add", "number", "NUM1", current, "NUM2", Value("lit", 1), False, node)
        positive = self._binary("operator_gt", "text", "OPERAND1", Value("arg", ident), "OPERAND2", Value("lit", 0), True, node)
        step = self._raw_replace(heap["refs"], Value("arg", ident), bumped, node)
        return [self._if_else(positive, [step], [], node)]

    def _ref_decref_body(self, heap, ident, node):
        current = self._raw_item(heap["refs"], Value("arg", ident), node)
        heads, minus = self._pin_value(self._binary("operator_subtract", "number", "NUM1", current, "NUM2", Value("lit", 1), False, node), node)
        zero = self._binary("operator_equals", "text", "OPERAND1", minus, "OPERAND2", Value("lit", 0), True, node)
        release = [self._raw_replace(heap["refs"], Value("arg", ident), minus, node)]
        clearing = []
        for column in heap["columns"]:
            clearing.append(self._span_call(column, "clear", [Value("arg", ident)], node))
        clearing.append(self._raw_add(heap["free"], Value("arg", ident), node))
        release.append(self._if_else(zero, clearing, [], node))
        positive = self._binary("operator_gt", "text", "OPERAND1", Value("arg", ident), "OPERAND2", Value("lit", 0), True, node)
        return [self._if_else(positive, heads + release, [], node)]

    def _ref_alloc_body(self, heap, node):
        length = self._raw_length(heap["free"])
        has_free = self._binary("operator_gt", "text", "OPERAND1", length, "OPERAND2", Value("lit", 0), True, node)
        yes = [
            self._store_value(heap["slot"], self._raw_item(heap["free"], Value("lit", "last"), node), node),
            self._raw_delete(heap["free"], Value("lit", "last"), node),
        ]
        for column in heap["columns"]:
            yes.append(self._span_call(column, "clear", [Value("var", heap["slot"])], node))
        no = [
            self._change_var(heap["next"], Value("lit", 1), node),
            self._store_value(heap["slot"], Value("var", heap["next"]), node),
        ]
        for column in heap["columns"]:
            starts, lengths, _owner = column.span
            no.append(self._raw_add(starts, Value("lit", 0), node))
            no.append(self._raw_add(lengths, Value("lit", 0), node))
        no.append(self._raw_add(heap["refs"], Value("lit", 0), node))
        heads = [self._if_else(has_free, yes, no, node)]
        slot = Value("var", heap["slot"])
        heads.append(self._raw_replace(heap["refs"], slot, Value("lit", 1), node))
        for column in heap["columns"]:
            starts, lengths, _owner = column.span
            heads.append(self._raw_replace(starts, slot, Value("lit", 0), node))
            heads.append(self._raw_replace(lengths, slot, Value("lit", 0), node))
        return heads

    def _ref_retain_body(self, heap, ident, node):
        count = self._raw_item(heap["refs"], Value("arg", ident), node)
        positive = self._binary("operator_gt", "text", "OPERAND1", Value("arg", ident), "OPERAND2", Value("lit", 0), True, node)
        unique = self._binary("operator_equals", "text", "OPERAND1", count, "OPERAND2", Value("lit", 1), True, node)
        reuse = self._boolean_pair("operator_and", positive, unique, node)
        yes = [self._store_value(heap["slot"], Value("arg", ident), node)]
        for column in heap["columns"]:
            yes.append(self._span_call(column, "clear", [Value("arg", ident)], node))
        no = [
            self._call_block(heap["ops"]["decref"], [Value("arg", ident)], node),
            self._call_block(heap["ops"]["alloc"], [], node),
        ]
        return [self._if_else(reuse, yes, no, node)]

    def _materialize_reuse(self, owner, node):
        heap = self.heaps[owner.ref_kind]
        heads = [self._call_block(heap["ops"]["retain"], [Value("var", owner.ident)], node)]
        heads.append(self._store_value(owner.ident, Value("var", heap["slot"]), node))
        return heads

    def _alias_ref(self, dest, src, node):
        if dest.ident is src.ident:
            return []
        return self._alias_id(dest, Value("var", src.ident), node)

    def _alias_id(self, dest, ident, node):
        heap = self.heaps[dest.ref_kind]
        return [
            self._call_block(heap["ops"]["incref"], [ident], node),
            self._call_block(heap["ops"]["decref"], [Value("var", dest.ident)], node),
            self._store_value(dest.ident, ident, node),
        ]

    def _release_ref(self, owner, node):
        heap = self.heaps[owner.ref_kind]
        return [
            self._call_block(heap["ops"]["decref"], [Value("var", owner.ident)], node),
            self._store_value(owner.ident, Value("lit", 0), node),
        ]

    def _shape_size(self, lst, dim, node):
        column = self.heaps["list"]["shape"]
        starts, _lengths, _owner = column.span
        start = self._raw_item(starts, Value("var", lst.ident), node)
        index = self._offset_index(start, Value("lit", dim + 1), node)
        heads, pinned = self._pin_value(self._raw_item(column, index, node), node)
        self._hoist(heads)
        return pinned

    def _write_shape(self, lst, shape, node):
        if lst.ident is None or not _known_shape(shape):
            return []
        column = self.heaps["list"]["shape"]
        ident = Value("var", lst.ident)
        return [self._span_call(column, "add", [ident, Value("lit", size)], node) for size in shape]

    def _adopt_shape(self, dest, src, node):
        src_shape = getattr(src, "shape", ()) or ()
        if dest.shape and not src_shape:
            self._error(node, self._dim_message(dest))
        if dest.shape and src_shape and len(dest.shape) != len(src_shape):
            self._error(node, self._dim_message(dest))
        if src_shape:
            dest.shape = src_shape

    def _attach_span(self, lst, node):
        starts = self._bind_list(None, f"{lst.name} .start", [], False, False, node, keep_local=True, frame_items=False)
        lengths = self._bind_list(None, f"{lst.name} .len", [], False, False, node, keep_local=True, frame_items=False)
        lst.span = (starts, lengths, self.frame_arg)
        lst.span_node = node
        if self.frame_lists is not None:
            self.frame_lists.append(starts)
            self.frame_lists.append(lengths)
        if self.span_lists is not None:
            self.span_lists.append(lst)
        lst.span_ops = {}
        lst.span_ops["clear"] = self._span_proc(lst, "clear", ["frame"], lambda frame: self._span_clear_body(lst, frame, node), node)
        lst.span_ops["add"] = self._span_proc(lst, "add", ["frame", "item"], lambda frame, item: self._span_add_body(lst, frame, item, node), node)
        lst.span_ops["insert"] = self._span_proc(
            lst, "insert", ["frame", "index", "item"],
            lambda frame, index, item: self._span_insert_body(lst, frame, index, item, node), node,
        )
        lst.span_ops["delete"] = self._span_proc(lst, "delete", ["frame", "index"], lambda frame, index: self._span_delete_body(lst, frame, index, node), node)

    def _span_proc(self, lst, op, names, build, node):
        params = [Arg(name, f"arg{index}", False) for index, name in enumerate(names)]
        label = f".span {op} {lst.name}"
        proc = Proc(label, params, True, _signature(label, params))
        saved = self.frame_arg
        self.frame_arg = None
        try:
            body = build(*params)
        finally:
            self.frame_arg = saved
        self._define_stack(proc, body, node)
        return proc

    def _span_call(self, lst, op, values, node):
        return self._call_block(lst.span_ops[op], values, node)

    def _span_pair(self, lst, frame, node):
        starts, lengths, _owner = lst.span
        frame_value = frame if isinstance(frame, Value) else Value("arg", frame)
        heads, start = self._pin_value(self._raw_item(starts, frame_value, node), node)
        more, length = self._pin_value(self._raw_item(lengths, frame_value, node), node)
        return heads + more, start, length

    def _backing(self, lst):
        if getattr(lst, "ident", None) is not None:
            return lst.heap, Value("var", lst.ident)
        if lst.span is not None:
            return lst, Value("arg", lst.span[2])
        return lst, None

    def _offset_index(self, start, logical, node):
        total = self._binary("operator_add", "number", "NUM1", start, "NUM2", logical, False, node)
        return self._binary("operator_subtract", "number", "NUM1", total, "NUM2", Value("lit", 1), False, node)

    def _span_physical(self, lst, index, node):
        storage, frame = self._backing(lst)
        starts, lengths, _owner = storage.span
        start = self._raw_item(starts, frame, node)
        length = self._raw_item(lengths, frame, node)
        if index.kind == "lit" and index.data == "last":
            logical = length
        elif index.kind == "lit" and index.data == "random":
            logical = self._random_between(Value("lit", 1), length, node)
        else:
            logical = index
        return self._offset_index(start, logical, node)

    def _random_between(self, low, high, node):
        block = self._new_block("operator_random")
        self._apply_slot(block, "FROM", "number", low, node)
        self._apply_slot(block, "TO", "number", high, node)
        return Value("block", block)

    def _span_shift(self, starts, pos, delta, frame, node, inclusive):
        heads, pos = self._pin_value(pos, node)
        more, delta = self._pin_value(delta, node)
        heads.extend(more)
        index = self._hidden_var(node, 1)

        def at_index():
            return self._raw_item(starts, Value("var", index), node)

        live = self._binary("operator_gt", "text", "OPERAND1", at_index(), "OPERAND2", Value("lit", 0), True, node)
        if inclusive:
            after = self._not_value(self._binary("operator_lt", "text", "OPERAND1", at_index(), "OPERAND2", pos, True, node), node)
        else:
            after = self._binary("operator_gt", "text", "OPERAND1", at_index(), "OPERAND2", pos, True, node)
        not_self = self._not_value(
            self._binary("operator_equals", "text", "OPERAND1", Value("var", index), "OPERAND2", Value("arg", frame), True, node),
            node,
        )
        cond = self._boolean_pair("operator_and", live, self._boolean_pair("operator_and", after, not_self, node), node)
        updated = self._binary("operator_add", "number", "NUM1", at_index(), "NUM2", delta, False, node)
        body = [
            self._if_else(cond, [self._raw_replace(starts, Value("var", index), updated, node)], [], node),
            self._change_var(index, Value("lit", 1), node),
        ]
        heads.extend([
            self._store_value(index, Value("lit", 1), node),
            self._repeat_block(self._raw_length(starts), body, node),
        ])
        return heads

    def _span_clear_body(self, lst, frame, node):
        starts, lengths, _owner = lst.span
        heads, start, length = self._span_pair(lst, frame, node)
        nonzero = self._binary("operator_gt", "text", "OPERAND1", length, "OPERAND2", Value("lit", 0), True, node)
        loop = self._repeat_block(length, [self._raw_delete(lst, start, node)], node)
        shift = self._span_shift(starts, start, self._negate_number(length, node), frame, node, False)
        heads.append(self._if_else(nonzero, [loop, *shift], [], node))
        heads.append(self._raw_replace(lengths, Value("arg", frame), Value("lit", 0), node))
        heads.append(self._raw_replace(starts, Value("arg", frame), Value("lit", 0), node))
        return heads

    def _span_add_body(self, lst, frame, item, node):
        starts, lengths, _owner = lst.span
        heads, start, length = self._span_pair(lst, frame, node)
        empty = self._binary("operator_equals", "text", "OPERAND1", length, "OPERAND2", Value("lit", 0), True, node)
        pinned, data_len = self._pin_value(self._raw_length(lst), node)
        heads.extend(pinned)
        new_start = self._binary("operator_add", "number", "NUM1", data_len, "NUM2", Value("lit", 1), False, node)
        yes = [
            self._raw_replace(starts, Value("arg", frame), new_start, node),
            self._raw_add(lst, Value("arg", item), node),
            self._raw_replace(lengths, Value("arg", frame), Value("lit", 1), node),
        ]
        pos = self._binary("operator_add", "number", "NUM1", start, "NUM2", length, False, node)
        placed, pos = self._pin_value(pos, node)
        at_end = self._binary("operator_gt", "text", "OPERAND1", pos, "OPERAND2", data_len, True, node)
        grown = self._binary("operator_add", "number", "NUM1", length, "NUM2", Value("lit", 1), False, node)
        middle = [
            self._raw_insert(lst, pos, Value("arg", item), node),
            *self._span_shift(starts, pos, Value("lit", 1), frame, node, True),
        ]
        no = placed + [
            self._if_else(at_end, [self._raw_add(lst, Value("arg", item), node)], middle, node),
            self._raw_replace(lengths, Value("arg", frame), grown, node),
        ]
        heads.append(self._if_else(empty, yes, no, node))
        return heads

    def _span_insert_body(self, lst, frame, index, item, node):
        starts, lengths, _owner = lst.span
        heads, start, length = self._span_pair(lst, frame, node)
        empty = self._binary("operator_equals", "text", "OPERAND1", length, "OPERAND2", Value("lit", 0), True, node)
        past = self._binary("operator_gt", "text", "OPERAND1", Value("arg", index), "OPERAND2", length, True, node)
        append_now = self._boolean_pair("operator_or", empty, past, node)
        yes = [self._span_call(lst, "add", [Value("arg", frame), Value("arg", item)], node)]
        physical = self._offset_index(start, Value("arg", index), node)
        placed, physical = self._pin_value(physical, node)
        grown = self._binary("operator_add", "number", "NUM1", length, "NUM2", Value("lit", 1), False, node)
        no = placed + [
            self._raw_insert(lst, physical, Value("arg", item), node),
            *self._span_shift(starts, physical, Value("lit", 1), frame, node, True),
            self._raw_replace(lengths, Value("arg", frame), grown, node),
        ]
        heads.append(self._if_else(append_now, yes, no, node))
        return heads

    def _span_delete_body(self, lst, frame, index, node):
        starts, lengths, _owner = lst.span
        heads, start, length = self._span_pair(lst, frame, node)
        is_all = self._binary("operator_equals", "text", "OPERAND1", Value("arg", index), "OPERAND2", Value("lit", "all"), True, node)
        yes = [self._span_call(lst, "clear", [Value("arg", frame)], node)]
        is_last = self._binary("operator_equals", "text", "OPERAND1", Value("arg", index), "OPERAND2", Value("lit", "last"), True, node)
        logical = self._hidden_var(node, 0)
        choose = self._if_else(
            is_last,
            [self._store_value(logical, length, node)],
            [self._store_value(logical, Value("arg", index), node)],
            node,
        )
        placed, physical = self._pin_value(self._offset_index(start, Value("var", logical), node), node)
        new_len = self._binary("operator_subtract", "number", "NUM1", length, "NUM2", Value("lit", 1), False, node)
        counted, new_len = self._pin_value(new_len, node)
        zero = self._binary("operator_equals", "text", "OPERAND1", new_len, "OPERAND2", Value("lit", 0), True, node)
        no = [choose, *placed, self._raw_delete(lst, physical, node), *counted]
        no.append(self._raw_replace(lengths, Value("arg", frame), new_len, node))
        no.append(self._if_else(zero, [self._raw_replace(starts, Value("arg", frame), Value("lit", 0), node)], [], node))
        no.extend(self._span_shift(starts, physical, Value("lit", -1), frame, node, False))
        heads.append(self._if_else(is_all, yes, no, node))
        return heads

    def _span_contains(self, lst, item, node):
        storage, frame = self._backing(lst)
        starts, _lengths, _owner = storage.span
        heads, item = self._pin_value(item, node)
        pinned, start, length = self._span_pair(storage, frame, node)
        heads.extend(pinned)
        flag = self._hidden_var(node, 0)
        index = self._hidden_var(node, 1)
        current = self._raw_item(storage, self._offset_index(start, Value("var", index), node), node)
        same = self._binary("operator_equals", "text", "OPERAND1", current, "OPERAND2", item, True, node)
        body = [
            self._if_else(same, [self._store_value(flag, Value("lit", 1), node)], [], node),
            self._change_var(index, Value("lit", 1), node),
        ]
        heads.extend([
            self._store_value(flag, Value("lit", 0), node),
            self._store_value(index, Value("lit", 1), node),
            self._repeat_block(length, body, node),
        ])
        return heads, Value("var", flag, True)

    def _span_index_of(self, lst, item, node):
        storage, frame = self._backing(lst)
        starts, _lengths, _owner = storage.span
        heads, item = self._pin_value(item, node)
        pinned, start, length = self._span_pair(storage, frame, node)
        heads.extend(pinned)
        found = self._hidden_var(node, 0)
        index = self._hidden_var(node, 1)
        current = self._raw_item(storage, self._offset_index(start, Value("var", index), node), node)
        same = self._binary("operator_equals", "text", "OPERAND1", current, "OPERAND2", item, True, node)
        fresh = self._binary("operator_equals", "text", "OPERAND1", Value("var", found), "OPERAND2", Value("lit", 0), True, node)
        match = self._boolean_pair("operator_and", same, fresh, node)
        body = [
            self._if_else(match, [self._store_value(found, Value("var", index), node)], [], node),
            self._change_var(index, Value("lit", 1), node),
        ]
        heads.extend([
            self._store_value(found, Value("lit", 0), node),
            self._store_value(index, Value("lit", 1), node),
            self._repeat_block(length, body, node),
        ])
        return heads, Value("var", found)

    def _monitor(self, opcode, param, item, is_list):
        monitor = {
            "id": item.vid if isinstance(item, Var) else item.lid,
            "mode": "list" if is_list else "default",
            "opcode": opcode,
            "params": {param: item.name},
            "spriteName": None if item.shared or self.is_stage else self.name,
            "value": item.initial,
            "width": 0,
            "height": 0,
            "x": 5,
            "y": 5,
            "visible": True,
        }
        if not is_list:
            monitor["sliderMin"] = 0
            monitor["sliderMax"] = 100
            monitor["isDiscrete"] = True
        return monitor

    def _load_media(self, kind, file_name, label, node):
        if kind == "backdrop" and not self.is_stage:
            self._error(node, "backdrops belong on the stage (stage.py or @kitty.stage)")
        source = Path(file_name)
        if not source.is_absolute():
            source = self.path.parent / source
        if not source.is_file():
            self._error(node, f"file not found: {source}")
        ext = source.suffix.lower().lstrip(".")
        if ext == "jpeg":
            ext = "jpg"
        data = source.read_bytes()
        asset_id, md5ext = self.project.add_asset(data, ext)
        media_name = label or source.stem
        if kind == "sound":
            rate, count = _wav_info(data) if ext == "wav" else (48000, 1)
            self.sounds.append({
                "name": media_name,
                "assetId": asset_id,
                "dataFormat": ext,
                "format": "",
                "rate": rate,
                "sampleCount": count,
                "md5ext": md5ext,
            })
            return
        costume = {
            "name": media_name,
            "bitmapResolution": 1 if ext == "svg" else 2,
            "dataFormat": ext,
            "assetId": asset_id,
            "md5ext": md5ext,
            "rotationCenterX": 0,
            "rotationCenterY": 0,
        }
        self.costumes.append(costume)

    def _add_default_costume(self):
        asset_id, md5ext = self.project.add_asset(_COSTUME_SVG, "svg")
        self.costumes.append({
            "name": "costume1",
            "bitmapResolution": 1,
            "dataFormat": "svg",
            "assetId": asset_id,
            "md5ext": md5ext,
            "rotationCenterX": 32,
            "rotationCenterY": 32,
        })

    def _add_default_backdrop(self):
        asset_id, md5ext = self.project.add_asset(_BACKDROP_SVG, "svg")
        self.costumes.append({
            "name": "backdrop1",
            "bitmapResolution": 1,
            "dataFormat": "svg",
            "assetId": asset_id,
            "md5ext": md5ext,
            "rotationCenterX": 240,
            "rotationCenterY": 180,
        })

    def _collect_procedures(self, rest):
        procs = []
        for stmt in rest:
            if isinstance(stmt, ast.FunctionDef) and _is_ignored_function(stmt):
                self.ignored_names.add(stmt.name)
            elif isinstance(stmt, ast.FunctionDef) and self._function_kind(stmt)[0] == "block":
                procs.append(self._register_proc(stmt, defer_results=True))
        for proc in procs:
            if proc.returns:
                self._finish_results(proc)

    def _flush_script(self, stmts):
        if not stmts:
            return
        stmts = self._lower_control(list(stmts))
        heads = self._compile_stmts(stmts)
        if not heads:
            return
        hat = self._new_block("event_whenflagclicked")
        self._link([hat, *heads], None)
        self._place(hat)

    def _compile_function(self, fn):
        if _is_ignored_function(fn):
            self.ignored_names.add(fn.name)
            return
        kind, info = self._function_kind(fn)
        if kind == "block":
            self._compile_proc_body(fn)
            return
        if self.skip_self:
            if _method_params(fn, self.path):
                self._error(fn, "event scripts cannot take parameters")
        elif fn.args.args or fn.args.kwonlyargs or fn.args.vararg or fn.args.kwarg:
            self._error(fn, "event scripts cannot take parameters")
        hat = self._make_hat(kind, info, fn)
        heads = []
        if kind == "green_flag" and self.init_runtime and not self.prepended_init:
            heads.extend(self._compile_init_runtime())
            self.prepended_init = True
        lowered = self._lower_control(list(fn.body))
        frame, inits = self._prepare_locals(lowered, fn.name, [], fn)
        self.scope.append(frame)
        try:
            self._compile_nested(lowered, fn.name)
            heads.extend(inits)
            heads.extend(self._compile_stmts(lowered))
        finally:
            self.scope.pop()
        self._link(heads, hat)
        if heads:
            self.blocks[hat]["next"] = heads[0]
        self._place(hat)

    def _function_kind(self, fn):
        if _is_ignored_function(fn):
            return "ignored", {}
        if not fn.decorator_list:
            if _contains_return(fn.body):
                kind = "boolean" if _returns_boolean(fn) else "number"
                return "block", {"returns": kind}
            return "block", {}
        if len(fn.decorator_list) != 1:
            self._error(fn, "use one kitty decorator")
        dec = fn.decorator_list[0]
        name = _decorator_name(dec)
        if name in {"sprite", "stage"}:
            self._error(fn, "sprite and stage decorators belong on a top-level function")
        args, kwargs = ([], {})
        if isinstance(dec, ast.Call):
            args, kwargs = self._literal_call(dec)
        hats = {
            "green_flag": "green_flag",
            "when_clicked": "clicked",
            "when_stage_clicked": "stage_clicked",
            "when_cloned": "cloned",
        }
        if name in hats:
            return hats[name], {}
        if name == "when_key":
            if not args or not isinstance(args[0], str):
                self._error(dec, 'when_key needs a key, for example "space"')
            return "key", {"key": args[0]}
        if name == "when_backdrop":
            if not args or not isinstance(args[0], str):
                self._error(dec, "when_backdrop needs a backdrop name")
            return "backdrop", {"name": args[0]}
        if name == "when_receive":
            if not args or not isinstance(args[0], str):
                self._error(dec, "when_receive needs a message name")
            return "receive", {"message": args[0]}
        if name == "when_loudness":
            if not args or isinstance(args[0], bool) or not isinstance(args[0], (int, float)):
                self._error(dec, "when_loudness needs a number")
            return "loudness", {"value": args[0]}
        if name == "when_timer":
            if not args or isinstance(args[0], bool) or not isinstance(args[0], (int, float)):
                self._error(dec, "when_timer needs a number")
            return "timer", {"value": args[0]}
        if name == "block":
            return "block", {"warp": bool(kwargs.get("warp", False))}
        if name in {"number", "boolean"}:
            return "block", {"warp": bool(kwargs.get("warp", False)), "returns": name}
        self._error(fn, f"unknown decorator {name}")

    def _make_hat(self, kind, info, node):
        if kind == "green_flag":
            return self._new_block("event_whenflagclicked")
        if kind == "clicked":
            opcode = "event_whenstageclicked" if self.is_stage else "event_whenthisspriteclicked"
            return self._new_block(opcode)
        if kind == "stage_clicked":
            return self._new_block("event_whenstageclicked")
        if kind == "cloned":
            return self._new_block("control_start_as_clone")
        if kind == "key":
            block = self._new_block("event_whenkeypressed")
            self.blocks[block]["fields"]["KEY_OPTION"] = [_normalize_key(info["key"]), None]
            return block
        if kind == "backdrop":
            block = self._new_block("event_whenbackdropswitchesto")
            self.blocks[block]["fields"]["BACKDROP"] = [info["name"], None]
            return block
        if kind == "receive":
            block = self._new_block("event_whenbroadcastreceived")
            name, bid = self._broadcast(info["message"])
            self.blocks[block]["fields"]["BROADCAST_OPTION"] = [name, bid]
            return block
        if kind in {"loudness", "timer"}:
            block = self._new_block("event_whengreaterthan")
            menu = "LOUDNESS" if kind == "loudness" else "TIMER"
            self.blocks[block]["fields"]["WHENGREATERTHANMENU"] = [menu, None]
            self._literal_input(block, "VALUE", "positive", info["value"])
            return block
        self._error(node, f"unknown hat {kind}")

    def _register_proc(self, fn, display=None, proc_key=None, as_method=None, defer_results=False):
        key = proc_key or fn.name
        if key in self.procedures:
            self._error(fn, f"{key} is already defined")
        if proc_key is None and fn.name in self.symbols:
            self._error(fn, f"{fn.name} is already defined")
        _kind, info = self._function_kind(fn)
        method = self.skip_self if as_method is None else as_method
        pairs, star_name, kw_name, kwonly = _split_params(fn, self.path, method)
        label = display or fn.name.replace("_", " ")
        user_params = []
        params = []

        def add_param(name, boolean, default, keyword_only=False):
            param = Arg(name, f"arg{len(params)}", boolean)
            param.default = False if boolean and default is NO_DEFAULT else default
            param.keyword_only = keyword_only
            params.append(param)
            return param

        for arg, default in pairs:
            user_params.append(add_param(arg.arg, _is_bool_arg(arg, default), _default_value(self, default)))
        for arg, default in kwonly:
            user_params.append(add_param(arg.arg, _is_bool_arg(arg, default), _default_value(self, default), True))
        star = None
        if star_name:
            count = add_param("arg count", False, NO_DEFAULT)
            slots = [add_param(f"arg {index + 1}", False, NO_DEFAULT) for index in range(_STAR_LIMIT)]
            star = StarArgs(star_name, count, slots)
        kw = None
        if kw_name:
            count = add_param("keyword count", False, NO_DEFAULT)
            pairs = []
            for index in range(_KW_LIMIT):
                key_arg = add_param(f"key {index + 1}", False, NO_DEFAULT)
                value_arg = add_param(f"value {index + 1}", False, NO_DEFAULT)
                pairs.append((key_arg, value_arg))
            kw = KwArgs(kw_name, count, pairs)
        for scope in self.scope_args:
            add_param(scope.name, False, NO_DEFAULT)
        proc = Proc(key, params, True, _signature(label, params))
        proc.user_params = user_params
        proc.scope_args = [param for param in params if param.name.startswith(".frame")]
        proc.star = star
        proc.kw = kw
        proc.label = label
        proc.returns = info.get("returns")
        proc.fn = fn
        if proc.returns:
            widths = _return_widths(fn)
            if widths and len(set(widths)) != 1:
                self._error(fn, "return the same number of values from every return")
            count = widths[0] if widths else 1
            if proc.returns == "boolean" and count != 1:
                self._error(fn, "a boolean function returns one condition")
            proc.return_count = count
        self.procedures[key] = proc
        if proc_key is None:
            self.symbols[fn.name] = proc
        if proc.returns and not defer_results:
            self._finish_results(proc)
        for param in user_params:
            param.carries = _carried_kind(fn, param.name)
        return proc

    def _gather_lambdas(self, stmts, found):
        for stmt in stmts:
            if isinstance(stmt, ast.FunctionDef):
                continue
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.value, ast.Lambda):
                target = stmt.targets[0]
                if isinstance(target, ast.Name):
                    found.append((target.id, stmt.value))
                elif (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    found.append((target.attr, stmt.value))
            self._gather_lambdas(_nested_statements(stmt), found)

    def _finish_lambdas(self):
        found = self._lambda_found
        if not found:
            return
        self._lambda_found = []
        procs = []
        seen = set()
        for name, node in found:
            if name in seen:
                self._error(node, f"{name} is already defined")
            seen.add(name)
            if name in self.symbols or name in self.procedures:
                self._error(node, f"{name} is already defined")
            proc = self._register_lambda(name, node)
            procs.append(proc)
        self._refine_lambda_kinds(procs)
        for proc in procs:
            self._compile_proc_body(proc.fn, proc)

    def _register_lambda(self, name, node):
        anonymous = name is None
        if anonymous:
            self._lambda_n += 1
            name = f"lambda_{self._lambda_n}"
            display = f"lambda {self._lambda_n}"
        else:
            display = name.replace("_", " ")
        fn = self._function_from_lambda(name, node)
        scopes = list(self.scope_args)
        if self.frame_arg is not None:
            scopes = scopes + [self.frame_arg]
        saved = self.scope_args
        self.scope_args = scopes
        try:
            proc = self._register_proc(fn, display=display, proc_key=name if anonymous else None, as_method=False)
        finally:
            self.scope_args = saved
        proc.source = node
        return proc

    def _function_from_lambda(self, name, node):
        decorator = ast.Name(id="number", ctx=ast.Load())
        ret = ast.Return(value=node.body)
        fn = ast.FunctionDef(
            name=name,
            args=node.args,
            body=[ret],
            decorator_list=[decorator],
            returns=None,
            type_params=[],
        )
        return self._mark(fn, node)

    def _refine_lambda_kinds(self, procs):
        changed = True
        while changed:
            changed = False
            for proc in procs:
                kind = self._value_kind(proc.source.body)
                if kind != proc.returns:
                    proc.returns = kind
                    changed = True

    def _value_kind(self, node):
        if isinstance(node, (ast.Compare, ast.BoolOp)):
            return "boolean"
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return "boolean"
        if isinstance(node, ast.Constant) and isinstance(node.value, bool):
            return "boolean"
        if isinstance(node, ast.IfExp):
            if self._value_kind(node.body) == "boolean" and self._value_kind(node.orelse) == "boolean":
                return "boolean"
            return "number"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Lambda):
                return self._value_kind(node.func.body)
            proc = self._proc_from_call(node)
            if proc is not None and proc.returns == "boolean":
                return "boolean"
            if proc is not None and proc.source is not None and proc.returns != "boolean":
                return proc.returns or "number"
            name = self._block_name(node.func)
            if name == "contains":
                return "boolean"
            spec = BLOCKS.get(name) if name else None
            if spec is not None and spec.shape == "boolean":
                return "boolean"
        return "number"

    def _compile_proc_body(self, fn, proc=None):
        proc = proc or self.procedures[fn.name]
        saved = (self.frame_arg, self.scope_args, self.frame_lists, self.span_lists, self.current_proc, self.frame_depth)
        depth = len(proc.scope_args)
        frame_arg = Arg(f".frame{depth}", f"frame{depth}", False)
        self.frame_arg = frame_arg
        self.scope_args = list(proc.scope_args)
        self.frame_lists = []
        self.span_lists = []
        self.current_proc = proc
        self.frame_depth = depth
        proc.owned = []
        proc.frame_arg = frame_arg
        proc.frame_lists = self.frame_lists
        proc.span_lists = self.span_lists
        try:
            self._compile_framed_proc(fn, proc)
        finally:
            self.frame_arg, self.scope_args, self.frame_lists, self.span_lists, self.current_proc, self.frame_depth = saved

    def _compile_framed_proc(self, fn, proc):
        held = self.frame_arg
        self.frame_arg = None
        proc.free_list = self._bind_list(None, f".free {proc.label}", [], False, False, fn, keep_local=True)
        proc.next_var = self._bind_var(None, f".next {proc.label}", 0, False, False, fn, keep_local=True)
        proc.ticket = self._bind_var(None, f".ticket {proc.label}", 0, False, False, fn, keep_local=True)
        proc.frame_result_vars = []
        for index, result in enumerate(proc.results):
            lst = self._bind_list(None, f".cells {result.name}", [], False, False, fn, keep_local=True)
            holder = Var(f"{result.name} cell", f"cell{index}", "0", False)
            holder.frame = (lst, held)
            proc.frame_result_vars.append(holder)
        self.frame_arg = held
        for holder in proc.frame_result_vars:
            self.frame_lists.append(holder.frame[0])
        lowered = self._rewrite_arg_loops(list(fn.body), proc)
        lowered = self._lower_control(lowered)
        previous = self.return_proc
        previous_done = self.needs_done
        self.return_proc = proc if proc.returns else None
        self.needs_done = False
        previous_done_name = self.done_name
        self.done_name = f"done {proc.name}" if proc.returns else None
        try:
            if proc.returns:
                if not _contains_return(lowered):
                    label = "boolean" if proc.returns == "boolean" else "number"
                    self._error(fn, f"a {label} function must return a value")
                lowered = self._lower_returns(lowered)
            elif _contains_return(lowered):
                self._error(fn, "return belongs in a @kitty.number or @kitty.boolean function")
            frame, inits = self._prepare_locals(lowered, proc.name, proc.user_params, fn)
            if proc.star:
                frame[proc.star.name] = proc.star
                frame[proc.star.count.name] = proc.star.count
            if proc.kw:
                frame[proc.kw.name] = proc.kw
                frame[proc.kw.count.name] = proc.kw.count
            self.scope.append(frame)
            try:
                self._compile_nested(lowered, proc.name)
                body = inits + self._compile_stmts(lowered) + self._epilogue(proc, fn)
            finally:
                self.scope.pop()
        finally:
            self.return_proc = previous
            self.needs_done = previous_done
            self.done_name = previous_done_name
        impl_params = list(proc.params) + [proc.frame_arg]
        impl = Proc(f"{proc.name} .run", impl_params, True, _signature(f"{proc.label} run", impl_params))
        proc.impl = impl
        self._define_stack(impl, body, fn)
        self._define_entry(proc, fn)

    def _define_stack(self, proc, heads, node):
        define = self._new_block("procedures_definition")
        proto = self._new_block("procedures_prototype", shadow=True, parent=define)
        self.blocks[define]["inputs"]["custom_block"] = [1, proto]
        self.blocks[proto]["mutation"] = _mutation(
            proccode=proc.proccode,
            argumentids=[param.arg_id for param in proc.params],
            argumentnames=[param.name for param in proc.params],
            argumentdefaults=[_input_default(param) for param in proc.params],
            warp=proc.warp,
        )
        for param in proc.params:
            opcode = "argument_reporter_boolean" if param.boolean else "argument_reporter_string_number"
            reporter = self._new_block(opcode, shadow=True, parent=proto)
            self.blocks[reporter]["fields"]["VALUE"] = [param.name, None]
            self.blocks[proto]["inputs"][param.arg_id] = [1, reporter]
        self._link(heads, define)
        if heads:
            self.blocks[define]["next"] = heads[0]
        self._place(define)

    def _define_entry(self, proc, node):
        define = self._new_block("procedures_definition")
        proto = self._new_block("procedures_prototype", shadow=True, parent=define)
        self.blocks[define]["inputs"]["custom_block"] = [1, proto]
        self.blocks[proto]["mutation"] = _mutation(
            proccode=proc.proccode,
            argumentids=[param.arg_id for param in proc.params],
            argumentnames=[param.name for param in proc.params],
            argumentdefaults=[_input_default(param) for param in proc.params],
            warp=True,
        )
        for param in proc.params:
            opcode = "argument_reporter_boolean" if param.boolean else "argument_reporter_string_number"
            reporter = self._new_block(opcode, shadow=True, parent=proto)
            self.blocks[reporter]["fields"]["VALUE"] = [param.name, None]
            self.blocks[proto]["inputs"][param.arg_id] = [1, reporter]
        length = self._length_of(proc.free_list)
        has_free = self._binary("operator_gt", "text", "OPERAND1", length, "OPERAND2", Value("lit", 0), True, node)
        yes = [
            self._store_value(proc.ticket, self._item_value(proc.free_list, Value("lit", "last"), node), node),
            self._delete_at(proc.free_list, Value("lit", "last"), node),
        ]
        for lst in proc.span_lists:
            yes.append(self._span_call(lst, "clear", [Value("var", proc.ticket)], node))
        no = [
            self._change_var(proc.next_var, Value("lit", 1), node),
            self._store_value(proc.ticket, Value("var", proc.next_var), node),
        ]
        for lst in proc.frame_lists:
            no.append(self._add_item(lst, Value("lit", 0), node))
        values = [Value("arg", param) for param in proc.params]
        values.append(Value("var", proc.ticket))
        call = self._call_block(proc.impl, values, node)
        heads = [self._if_else(has_free, yes, no, node), call]
        self._link(heads, define)
        self.blocks[define]["next"] = heads[0]
        self._place(define)

    def _epilogue(self, proc, node):
        heads = []
        for owner in proc.owned:
            heads.extend(self._release_ref(owner, node))
        for holder, published in zip(proc.frame_result_vars, proc.results):
            heads.append(self._store_value(published, Value("var", holder), node))
        heads.append(self._add_item(proc.free_list, Value("arg", proc.frame_arg), node))
        return heads

    def _compile_nested(self, stmts, owner_name):
        found = _nested_defs(stmts)
        procs = []
        for fn in found:
            if fn.decorator_list and self._function_kind(fn)[0] != "block":
                self._error(fn, "a nested function is a custom block. Leave off the hat")
            proc = self._open_nested(fn, owner_name)
            self.scope[-1][fn.name] = proc
            procs.append((fn, proc))
        for fn, proc in procs:
            self._compile_proc_body(fn, proc)

    def _open_nested(self, fn, owner_name):
        scopes = list(self.scope_args)
        if self.frame_arg is not None:
            scopes = scopes + [self.frame_arg]
        saved = self.scope_args
        self.scope_args = scopes
        try:
            display = f"{owner_name} {fn.name}".replace("_", " ").replace(".", " ")
            return self._register_proc(fn, display=display, proc_key=f"{owner_name}.{fn.name}", as_method=False)
        finally:
            self.scope_args = saved

    def _rewrite_arg_loops(self, stmts, proc):
        if proc.star is None and proc.kw is None:
            return stmts
        return [self._rewrite_arg_stmt(stmt, proc) for stmt in stmts]

    def _rewrite_arg_stmt(self, stmt, proc):
        if isinstance(stmt, ast.For):
            rewritten = self._rewrite_arg_for(stmt, proc)
            if rewritten is not None:
                return rewritten
        if isinstance(stmt, ast.If):
            return self._mark(ast.If(
                test=stmt.test,
                body=self._rewrite_arg_loops(stmt.body, proc),
                orelse=self._rewrite_arg_loops(stmt.orelse, proc),
            ), stmt)
        if isinstance(stmt, ast.While):
            return self._mark(ast.While(test=stmt.test, body=self._rewrite_arg_loops(stmt.body, proc), orelse=[]), stmt)
        if isinstance(stmt, ast.With):
            return self._mark(ast.With(items=stmt.items, body=self._rewrite_arg_loops(stmt.body, proc)), stmt)
        if isinstance(stmt, ast.Try):
            handlers = []
            for handler in stmt.handlers:
                copied = ast.ExceptHandler(type=handler.type, name=handler.name, body=self._rewrite_arg_loops(handler.body, proc))
                handlers.append(self._mark(copied, handler))
            return self._mark(ast.Try(
                body=self._rewrite_arg_loops(stmt.body, proc),
                handlers=handlers,
                orelse=self._rewrite_arg_loops(stmt.orelse, proc),
                finalbody=self._rewrite_arg_loops(stmt.finalbody, proc),
            ), stmt)
        return stmt

    def _rewrite_arg_for(self, stmt, proc):
        if not isinstance(stmt.iter, ast.Name):
            return None
        star = proc.star is not None and stmt.iter.id == proc.star.name
        kw = proc.kw is not None and stmt.iter.id == proc.kw.name
        if not star and not kw:
            return None
        if not isinstance(stmt.target, ast.Name):
            self._error(stmt, "write for item in args")
        self._flow += 1
        index = f".ia{self._flow}"
        count = proc.star.count.name if star else proc.kw.count.name
        if star:
            value = self._mark(ast.Subscript(
                value=self._name(proc.star.name, stmt),
                slice=self._name(index, stmt),
                ctx=ast.Load(),
            ), stmt)
        else:
            value = self._mark(ast.Call(
                func=self._name(".kwkey", stmt),
                args=[self._name(index, stmt)],
                keywords=[],
            ), stmt)
        body = [self._assign_name(stmt.target.id, value, stmt), *self._rewrite_arg_loops(stmt.body, proc)]
        loop = ast.For(
            target=self._mark(ast.Name(id=index, ctx=ast.Store()), stmt),
            iter=self._mark(ast.Call(
                func=self._name("range", stmt),
                args=[self._name(count, stmt)],
                keywords=[],
            ), stmt),
            body=body,
            orelse=[],
        )
        return self._mark(loop, stmt)

    def _compile_stmts(self, stmts):
        heads = []
        for stmt in stmts:
            heads.extend(self._compile_stmt(stmt))
        return heads

    def _compile_stmt(self, stmt):
        self.hoist_stack.append([])
        self.ephemeral_stack.append([])
        try:
            heads = self._compile_stmt_inner(stmt)
            extra = self._release_owners(self.ephemeral_stack[-1], stmt)
        finally:
            hoisted = self.hoist_stack.pop()
            self.ephemeral_stack.pop()
        return hoisted + heads + extra

    def _compile_stmt_inner(self, stmt):
        if isinstance(stmt, ast.Pass):
            return []
        if isinstance(stmt, ast.Return):
            return self._compile_return(stmt)
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            return []
        if isinstance(stmt, ast.Expr):
            return self._compile_stack(stmt.value)
        if isinstance(stmt, ast.If):
            return [self._compile_if(stmt)]
        if isinstance(stmt, ast.For):
            return self._compile_for(stmt)
        if isinstance(stmt, ast.While):
            return self._compile_while(stmt)
        if isinstance(stmt, ast.With):
            return self._compile_with(stmt)
        if isinstance(stmt, ast.Assign):
            compiled = self._compile_assign(stmt)
            if compiled is None:
                return []
            return compiled if isinstance(compiled, list) else [compiled]
        if isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            return [self._compile_assign(stmt)]
        if isinstance(stmt, ast.AugAssign):
            changed = self._compile_aug(stmt)
            return changed if isinstance(changed, list) else [changed]
        if isinstance(stmt, ast.FunctionDef):
            symbol = self._lookup(stmt.name)
            if isinstance(symbol, Proc):
                return []
            self._error(stmt, "define scripts and custom blocks outside of other scripts")
        if isinstance(stmt, (ast.Global, ast.Nonlocal)):
            if isinstance(stmt, ast.Nonlocal):
                if self.current_proc is None:
                    self._error(stmt, "nonlocal belongs inside a nested function")
            return []
        if isinstance(stmt, ast.Break):
            self._error(stmt, "break is outside a loop")
        if isinstance(stmt, ast.Continue):
            self._error(stmt, "continue is outside a loop")
        if isinstance(stmt, ast.Raise):
            self._error(stmt, "raise belongs inside try")
        if isinstance(stmt, ast.Try):
            self._error(stmt, "try could not be compiled")
        self._error(stmt, "this Python statement has no Scratch block")

    def _compile_return(self, stmt):
        proc = self.return_proc
        if proc is None or not proc.returns:
            self._error(stmt, "return belongs in a @kitty.number or @kitty.boolean function")
        if stmt.value is None:
            self._error(stmt, "return a value")
        values = self._return_values(stmt)
        if proc.yields in {"list", "dict"}:
            if proc.yields == "list":
                if len(values) != 1 or values[0].kind != "list":
                    self._error(stmt, "return a list")
                source = values[0].data
                if source.ident is not None:
                    self._adopt_shape(proc.result_list, source, stmt)
                    heads = self._alias_ref(proc.result_list, source, stmt)
                else:
                    self._adopt_shape(proc.result_list, source, stmt)
                    heads = [
                        *self._materialize_reuse(proc.result_list, stmt),
                        *self._write_shape(proc.result_list, source.shape, stmt),
                        *self._copy_list(source, proc.result_list, stmt),
                    ]
            else:
                if len(values) != 1 or values[0].kind != "dict":
                    self._error(stmt, "return a dictionary")
                mapping = values[0].data
                if mapping.ident is not None:
                    heads = self._alias_ref(proc.result_dict, mapping, stmt)
                else:
                    heads = [
                        *self._materialize_reuse(proc.result_dict, stmt),
                        *self._copy_list(mapping.keys, proc.result_dict.keys, stmt),
                        *self._copy_list(mapping.values, proc.result_dict.values, stmt),
                    ]
            if self.needs_done:
                done = self._lookup(self.done_name)
                if not isinstance(done, Var):
                    self._error(stmt, "return could not leave its loop")
                heads.append(self._store_value(done, Value("lit", 1), stmt))
            return heads
        holders = proc.frame_result_vars or [proc.result]
        if len(values) != len(holders):
            self._error(stmt, f"return {len(holders)} values")
        heads = []
        for holder, value in zip(holders, values):
            if proc.returns == "boolean":
                heads.extend(self._store_boolean(holder, value, stmt))
            else:
                heads.append(self._store_value(holder, value, stmt))
        if self.needs_done:
            done = self._lookup(self.done_name)
            if not isinstance(done, Var):
                self._error(stmt, "return could not leave its loop")
            heads.append(self._store_value(done, Value("lit", 1), stmt))
        return heads

    def _return_values(self, stmt):
        if isinstance(stmt.value, (ast.Tuple, ast.List)):
            values = []
            for elt in stmt.value.elts:
                if isinstance(elt, ast.Starred):
                    self._error(elt, "return each value by name")
                values.append(self._compile_expr(elt))
            return values
        return [self._compile_expr(stmt.value)]

    def _store_value(self, var, value, node):
        frame = getattr(var, "frame", None)
        if frame:
            lst, arg = frame
            return self._replace_item(lst, Value("arg", arg), value, node)
        block = self._new_block("data_setvariableto")
        self.blocks[block]["fields"]["VARIABLE"] = [var.name, var.vid]
        self._apply_slot(block, "VALUE", "text", value, node)
        return block

    def _store_boolean(self, var, value, node):
        if value.kind == "lit" and isinstance(value.data, bool):
            number = 1 if value.data else 0
            return [self._store_value(var, Value("lit", number), node)]
        block = self._new_block("control_if_else")
        self._apply_boolean(block, "CONDITION", value, node)
        yes = self._store_value(var, Value("lit", 1), node)
        no = self._store_value(var, Value("lit", 0), node)
        self._link([yes], block)
        self.blocks[block]["inputs"]["SUBSTACK"] = [2, yes]
        self._link([no], block)
        self.blocks[block]["inputs"]["SUBSTACK2"] = [2, no]
        return [block]

    def _hoist_proc_value(self, proc, call):
        if not self.hoist_stack:
            self._error(call, f"use {proc.name} inside a script")
        if proc.yields == "list":
            return Value("list", self._emit_list_result(proc, call))
        if proc.yields == "dict":
            return Value("dict", self._emit_dict_result(proc, call))
        outputs = self._emit_returning_call(proc, call)
        if len(outputs) == 1:
            return Value("var", outputs[0], proc.returns == "boolean")
        lst = self._hidden_list(call, frozen=True)
        heads = [self._delete_all_items(lst)]
        for var in outputs:
            heads.append(self._add_item(lst, Value("var", var), call))
        self.hoist_stack[-1].extend(heads)
        return Value("list", lst)

    def _emit_returning_call(self, proc, call):
        values = self._bind_proc_args(proc, call)
        held = self.frame_arg
        self.frame_arg = None
        plains = []
        try:
            for _result in proc.results:
                self._stub_n += 1
                plains.append(self._bind_var(None, f".r{self._stub_n}", 0, False, False, call, keep_local=True))
        finally:
            self.frame_arg = held
        stub = self._make_stub(proc, plains, call)
        self.hoist_stack[-1].append(self._call_block(stub, values, call))
        outputs = []
        for plain in plains:
            if held is not None:
                framed = self._hidden_var(call)
                self.hoist_stack[-1].append(self._store_value(framed, Value("var", plain), call))
                outputs.append(framed)
            else:
                outputs.append(plain)
        return outputs

    def _make_stub(self, proc, plains, node):
        self._stub_n += 1
        number = self._stub_n
        params = []
        for index, param in enumerate(proc.params):
            copied = Arg(param.name, f"s{number}_{index}", param.boolean)
            copied.default = param.default
            params.append(copied)
        label = f".use {number}"
        stub = Proc(label, params, True, _signature(label, params))
        call = self._call_block(proc, [Value("arg", param) for param in params], node)
        copies = [
            self._store_value(plain, Value("var", result), node)
            for plain, result in zip(plains, proc.results)
        ]
        self._define_stack(stub, [call, *copies], node)
        return stub

    def _call_block(self, proc, values, node):
        if len(values) != len(proc.params):
            self._error(node, f"{proc.name} takes {len(proc.params)} values")
        block = self._new_block("procedures_call")
        self.blocks[block]["mutation"] = _mutation(
            proccode=proc.proccode,
            argumentids=[param.arg_id for param in proc.params],
            warp=proc.warp,
        )
        for param, value in zip(proc.params, values):
            if param.boolean:
                self._apply_boolean(block, param.arg_id, value, node)
            else:
                self._apply_slot(block, param.arg_id, "text", value, node)
        return block

    def _compile_super_value(self, call):
        name = call.func.attr
        owner = self.super_class or self.blueprint
        if owner is None:
            self._error(call, "super() belongs in a sprite class")
        found = _find_super_method(owner, name)
        if found is None:
            self._error(call, f"no parent method {name}")
        parent, _fn = found
        proc = self.procedures.get(f"{parent.name}.{name}")
        if proc is None or not proc.returns:
            self._error(call, f"{name} does not return a value")
        return self._hoist_proc_value(proc, call)

    def _lower_returns(self, stmts):
        self._temps = 0
        self.arm_returns = False
        lowered = self._lower_stmt_list(list(stmts))
        self.needs_done = self.arm_returns
        if self.needs_done and lowered:
            lowered.insert(0, self._assign_name(self.done_name, ast.Constant(value=0), lowered[0]))
        return lowered

    def _lower_stmt_list(self, stmts):
        out = []
        guard = False
        for stmt in stmts:
            pieces, arming = self._lower_one(stmt)
            if guard and pieces:
                self.arm_returns = True
                out.append(self._guard_done(pieces, stmt))
            else:
                out.extend(pieces)
            guard = guard or arming
        return out

    def _lower_one(self, stmt):
        if _cblock_kind(stmt) == "if_":
            stmt = self._with_as_if(stmt)
        if isinstance(stmt, ast.If):
            body = self._lower_stmt_list(stmt.body) or [self._pass(stmt)]
            orelse = self._lower_stmt_list(stmt.orelse)
            node = self._make_if(stmt.test, body, orelse, stmt)
            return [node], _contains_return(stmt.body) or _contains_return(stmt.orelse)
        if isinstance(stmt, ast.Return):
            return [stmt], True
        if _loop_can_return(stmt):
            self.arm_returns = True
            return self._rewrite_loop(stmt), True
        return [stmt], False

    def _rewrite_loop(self, stmt):
        kind = _cblock_kind(stmt)
        if isinstance(stmt, ast.For):
            return self._rewrite_for(stmt)
        if kind == "repeat":
            call = stmt.items[0].context_expr
            if not call.args:
                self._error(stmt, "repeat needs a number")
            return self._rewrite_counted(call.args[0], stmt.body, stmt)
        if isinstance(stmt, ast.While):
            test = stmt.test
            if isinstance(test, ast.Constant) and test.value is True:
                test = self._done_clear(stmt)
            else:
                test = self._and_done(test, stmt)
            body = self._lower_stmt_list(stmt.body) or [self._pass(stmt)]
            return [self._make_while(test, body, stmt)]
        if kind == "forever":
            body = self._lower_stmt_list(stmt.body) or [self._pass(stmt)]
            return [self._make_while(self._done_clear(stmt), body, stmt)]
        if kind == "repeat_until":
            call = stmt.items[0].context_expr
            if not call.args:
                self._error(stmt, "repeat_until needs a condition")
            test = self._and_done(self._negate(call.args[0], stmt), stmt)
            body = self._lower_stmt_list(stmt.body) or [self._pass(stmt)]
            return [self._make_while(test, body, stmt)]
        self._error(stmt, "return inside this loop works with while, forever, repeat, and for i in range(n)")

    def _rewrite_for(self, stmt):
        if not isinstance(stmt.target, ast.Name):
            self._error(stmt, "for loops assign one name, as in for i in range(n)")
        if self._is_range_call(stmt.iter):
            return self._rewrite_range(stmt)
        return self._rewrite_each(stmt)

    def _rewrite_range(self, stmt):
        name = stmt.target.id
        start, stop, step = self._range_nodes(stmt.iter)
        if name == "_":
            count = self._range_count_node(start, stop, step, stmt)
            return self._rewrite_counted(count, stmt.body, stmt)
        cursor = self._fresh_ident("cursor")
        stop_name = self._fresh_ident("stop")
        step_name = self._fresh_ident("step")
        body = self._lower_stmt_list(stmt.body)
        assign = self._assign_name(name, self._name(cursor, stmt), stmt)
        bump = self._aug_by(cursor, self._name(step_name, stmt), stmt)
        if _contains_return(stmt.body):
            bump = self._guard_done([bump], stmt)
        test = self._and_done(self._range_test(cursor, stop_name, step, step_name, stmt), stmt)
        loop = self._make_while(test, [assign, *(body or [self._pass(stmt)]), bump], stmt)
        return [
            self._assign_name(cursor, start, stmt),
            self._assign_name(stop_name, stop, stmt),
            self._assign_name(step_name, step, stmt),
            loop,
        ]

    def _range_count_node(self, start, stop, step, source):
        if isinstance(step, ast.Constant) and step.value == 1 and _constant(start) == 0:
            return stop
        self._error(source, "return inside for _ in range works with range(n) or range(0, n)")

    def _range_test(self, name, stop_name, step, step_name, source):
        step_value = _constant(step)
        if _is_number(step_value) and step_value < 0:
            return self._compare_name(name, ast.Gt(), self._name(stop_name, source), source)
        if _is_number(step_value) and step_value > 0:
            return self._compare_name(name, ast.Lt(), self._name(stop_name, source), source)
        positive = self._compare_name(step_name, ast.Gt(), self._mark(ast.Constant(value=0), source), source)
        negative = self._compare_name(step_name, ast.Lt(), self._mark(ast.Constant(value=0), source), source)
        going_up = self._mark(ast.BoolOp(op=ast.And(), values=[positive, self._compare_name(name, ast.Lt(), self._name(stop_name, source), source)]), source)
        going_down = self._mark(ast.BoolOp(op=ast.And(), values=[negative, self._compare_name(name, ast.Gt(), self._name(stop_name, source), source)]), source)
        return self._mark(ast.BoolOp(op=ast.Or(), values=[going_up, going_down]), source)

    def _rewrite_each(self, stmt):
        symbol = self._iter_symbol(stmt.iter)
        if isinstance(symbol, Map):
            container = f".keys.{self._iter_name(stmt.iter)}"
        elif isinstance(symbol, Lst):
            container = self._iter_name(stmt.iter)
        else:
            self._error(stmt, "for walks range(...), a list, or a dictionary")
        if container is None:
            self._error(stmt, "for walks range(...), a list, or a dictionary")
        index = self._fresh_ident("index")
        limit = self._fresh_ident("limit")
        name = stmt.target.id
        body = self._lower_stmt_list(stmt.body)
        if name != "_":
            item = self._assign_name(
                name,
                self._mark(ast.Subscript(value=self._name(container, stmt), slice=self._name(index, stmt), ctx=ast.Load()), stmt),
                stmt,
            )
            body = [item] + body
        bump = self._aug_by(index, self._mark(ast.Constant(value=1), stmt), stmt)
        if _contains_return(stmt.body):
            bump = self._guard_done([bump], stmt)
        test = self._and_done(self._compare_name(index, ast.Lt(), self._name(limit, stmt), stmt), stmt)
        length = self._mark(
            ast.Call(func=self._mark(ast.Name(id="len", ctx=ast.Load()), stmt), args=[self._name(container, stmt)], keywords=[]),
            stmt,
        )
        loop = self._make_while(test, (body or [self._pass(stmt)]) + [bump], stmt)
        return [
            self._assign_name(index, self._mark(ast.Constant(value=0), stmt), stmt),
            self._assign_name(limit, length, stmt),
            loop,
        ]

    def _rewrite_counted(self, count_expr, body, source):
        self._temps += 1
        stem = self.return_proc.name if self.return_proc else "script"
        limit = f"limit {stem} {self._temps}"
        count = f"count {stem} {self._temps}"
        zero = self._mark(ast.Constant(value=0), source)
        test = self._and_done(self._compare_name(count, ast.Lt(), self._name(limit, source), source), source)
        step = self._aug_name(count, source)
        lowered = self._lower_stmt_list(body)
        loop = self._make_while(test, [step] + (lowered or [self._pass(source)]), source)
        return [
            self._assign_name(limit, count_expr, source),
            self._assign_name(count, zero, source),
            loop,
        ]

    def _with_as_if(self, stmt):
        call = stmt.items[0].context_expr
        if not call.args:
            self._error(stmt, "if_ needs a condition")
        return self._make_if(call.args[0], stmt.body, [], stmt)

    def _guard_done(self, body, source):
        node = self._make_if(self._done_clear(source), body, [], source)
        return node

    def _and_done(self, test, source):
        node = ast.BoolOp(op=ast.And(), values=[self._done_clear(source), test])
        return self._mark(node, source)

    def _done_clear(self, source):
        zero = self._mark(ast.Constant(value=0), source)
        return self._compare_name(self.done_name, ast.Eq(), zero, source)

    def _negate(self, expr, source):
        return self._mark(ast.UnaryOp(op=ast.Not(), operand=expr), source)

    def _compare_name(self, left, op, right, source):
        node = ast.Compare(left=self._name(left, source), ops=[op], comparators=[right])
        return self._mark(node, source)

    def _name(self, ident, source):
        return self._mark(ast.Name(id=ident, ctx=ast.Load()), source)

    def _sum_names(self, left, right, source):
        node = ast.BinOp(left=self._name(left, source), op=ast.Add(), right=self._name(right, source))
        return self._mark(node, source)

    def _assign_name(self, ident, value, source):
        if isinstance(value, ast.Constant):
            value = self._mark(value, source)
        target = self._mark(ast.Name(id=ident, ctx=ast.Store()), source)
        return self._mark(ast.Assign(targets=[target], value=value), source)

    def _aug_name(self, ident, source):
        return self._aug_by(ident, self._mark(ast.Constant(value=1), source), source)

    def _aug_by(self, ident, value, source):
        target = self._mark(ast.Name(id=ident, ctx=ast.Store()), source)
        return self._mark(ast.AugAssign(target=target, op=ast.Add(), value=value), source)

    def _fresh_ident(self, label):
        self._temps += 1
        stem = self.return_proc.name if self.return_proc else "script"
        return f"{label} {stem} {self._temps}"

    def _make_while(self, test, body, source):
        return self._mark(ast.While(test=test, body=body, orelse=[]), source)

    def _make_if(self, test, body, orelse, source):
        return self._mark(ast.If(test=test, body=body, orelse=orelse), source)

    def _pass(self, source):
        return self._mark(ast.Pass(), source)

    def _mark(self, node, source):
        node.lineno = getattr(source, "lineno", 1) or 1
        node.col_offset = getattr(source, "col_offset", 0) or 0
        return node

    def _compile_stack(self, expr):
        if not isinstance(expr, ast.Call):
            self._error(expr, "a script statement must be a kitty block or a custom block")
        if isinstance(expr.func, ast.Name) and expr.func.id in self.ignored_names:
            self._error(expr, f"ignored function {expr.func.id} cannot be called from compiled Scratch code")
        if (
            isinstance(expr.func, ast.Attribute)
            and expr.func.attr in self.ignored_names
            and isinstance(expr.func.value, ast.Name)
            and expr.func.value.id == "self"
        ):
            self._error(expr, f"ignored function {expr.func.attr} cannot be called from compiled Scratch code")
        if self._math_operator(expr.func) is not None:
            self._error(expr, "a math function is a value. Use it in say, set, or other blocks")
        collected = self._collection_statement(expr)
        if collected is not None:
            return collected
        if _is_super_call(expr):
            if expr.func.attr == "__init__":
                self._error(expr, "super().__init__ belongs in __init__")
            return [self._emit_super(expr)]
        remote = self._remote_instance(expr)
        if remote is not None and remote != self.instance_name:
            return self._emit_remote(remote, expr)
        proc = self._proc_from_call(expr)
        if proc is not None:
            return [self._emit_proc_call(proc, expr)]
        name = self._block_name(expr.func)
        if name == "clone":
            if expr.args or expr.keywords:
                self._error(expr, "clone takes no values")
            return [self._emit_spec(BLOCKS["create_clone"], expr)]
        if name in MATH or name == "math":
            self._error(expr, f"{name} is a value, not a command")
        if name in {"length", "contains"}:
            self._error(expr, f"{name} is a value, not a command")
        spec = BLOCKS.get(name) if name else None
        if spec is None:
            if self._text_method_value(expr) is not None:
                self._error(expr, "a string method is a value. Use it in say, set, or other blocks")
            self._error(expr, "unknown Scratch block")
        if spec.shape == "c":
            self._error(expr, f"use with kitty.{name}(...): or self.{name}(...):")
        if spec.shape != "stack":
            self._error(expr, f"{name} is a value, not a command")
        if name == "wait_until":
            until = self._condition_arg(expr)
            if until is not None:
                return self._wait_until(until, expr)
        return [self._emit_spec(spec, expr)]

    def _compile_if(self, stmt):
        if stmt.orelse:
            block = self._new_block("control_if_else")
        else:
            block = self._new_block("control_if")
        self._apply_boolean(block, "CONDITION", self._compile_expr(stmt.test), stmt.test)
        then_heads = self._compile_stmts(stmt.body)
        self._link(then_heads, block)
        if then_heads:
            self.blocks[block]["inputs"]["SUBSTACK"] = [2, then_heads[0]]
        if stmt.orelse:
            else_heads = self._compile_stmts(stmt.orelse)
            self._link(else_heads, block)
            if else_heads:
                self.blocks[block]["inputs"]["SUBSTACK2"] = [2, else_heads[0]]
        return block

    def _compile_for(self, stmt):
        if stmt.orelse:
            self._error(stmt, "Scratch loops have no else")
        if self._constant_empty_range(stmt.iter):
            return []
        if not isinstance(stmt.target, ast.Name):
            self._error(stmt, "for loops assign one name, as in for i in range(n)")
        if self._is_range_call(stmt.iter):
            return self._compile_range_for(stmt)
        return self._compile_each(stmt)

    def _compile_range_for(self, stmt):
        start, stop, step, times, heads = self._range_parts(stmt.iter)
        name = stmt.target.id
        body = self._compile_stmts(stmt.body)
        if name != "_":
            var = self._loop_var(name, stmt)
            cursor = self._hidden_var(stmt)
            heads.append(self._store_value(cursor, start, stmt))
            body = [self._store_value(var, Value("var", cursor), stmt), *body]
            body.append(self._change_var(cursor, step, stmt))
        heads.append(self._repeat_block(times, body, stmt.iter))
        return heads

    def _compile_each(self, stmt):
        symbol = self._iter_symbol(stmt.iter)
        if isinstance(symbol, Map):
            sequence = symbol.keys
        elif isinstance(symbol, Lst):
            sequence = symbol
        else:
            self._error(stmt.iter, "for walks range(...), a list, or a dictionary")
        index = self._hidden_var(stmt, 1)
        times = self._length_of(sequence, stmt)
        body = []
        if stmt.target.id != "_":
            var = self._loop_var(stmt.target.id, stmt)
            item = self._item_value(sequence, Value("var", index), stmt)
            body.append(self._store_value(var, item, stmt))
        body.extend(self._compile_stmts(stmt.body))
        body.append(self._change_var(index, Value("lit", 1), stmt))
        return [
            self._store_value(index, Value("lit", 1), stmt),
            self._repeat_block(times, body, stmt),
        ]

    def _loop_var(self, name, node):
        symbol = self._lookup(name)
        if symbol is None:
            return self._bind_var(name, name, 0, False, False, node)
        if isinstance(symbol, Var):
            return symbol
        self._error(node, f"{name} is not a variable. A for loop assigns a variable")

    def _repeat_block(self, times, body, node):
        block = self._new_block("control_repeat")
        self._apply_slot(block, "TIMES", "whole", times, node)
        self._link(body, block)
        if body:
            self.blocks[block]["inputs"]["SUBSTACK"] = [2, body[0]]
        return block

    def _change_var(self, var, value, node):
        if getattr(var, "frame", None):
            total = self._binary("operator_add", "number", "NUM1", Value("var", var), "NUM2", value, False, node)
            return self._store_value(var, total, node)
        block = self._new_block("data_changevariableby")
        self.blocks[block]["fields"]["VARIABLE"] = [var.name, var.vid]
        self._apply_slot(block, "VALUE", "number", value, node)
        return block

    def _range_parts(self, node):
        start, stop, step = self._range_nodes(node)
        start_value = self._compile_expr(start)
        stop_value = self._compile_expr(stop)
        step_value = self._compile_expr(step)
        if step_value.kind == "lit" and _is_number(step_value.data) and step_value.data == 0:
            self._error(node, "range step cannot be 0")
        heads = []
        heads_start, start_value = self._pin_value(start_value, node)
        heads_step, step_value = self._pin_value(step_value, node)
        heads.extend(heads_start)
        heads.extend(heads_step)
        folded = self._folded_range_count(start_value, stop_value, step_value)
        if folded is not None:
            return start_value, stop_value, step_value, Value("lit", folded), heads
        if start_value.kind == "lit" and start_value.data == 0 and step_value.kind == "lit" and step_value.data == 1:
            return start_value, stop_value, step_value, stop_value, heads
        span = self._binary("operator_subtract", "number", "NUM1", stop_value, "NUM2", start_value, False, node)
        if step_value.kind == "lit" and step_value.data == 1:
            return start_value, stop_value, step_value, span, heads
        quotient = self._binary("operator_divide", "number", "NUM1", span, "NUM2", step_value, False, node)
        times = self._compile_math("ceiling", quotient, node)
        return start_value, stop_value, step_value, times, heads

    def _folded_range_count(self, start, stop, step):
        if not (start.kind == "lit" and stop.kind == "lit" and step.kind == "lit"):
            return None
        if not all(isinstance(item.data, int) and not isinstance(item.data, bool) for item in (start, stop, step)):
            return None
        if step.data == 0:
            return None
        return len(range(start.data, stop.data, step.data))

    def _compile_while(self, stmt):
        if stmt.orelse:
            self._error(stmt, "Scratch loops have no else")
        test = stmt.test
        if isinstance(test, ast.Constant) and test.value is True:
            block = self._new_block("control_forever")
            body = self._compile_stmts(stmt.body)
            self._link(body, block)
            if body:
                self.blocks[block]["inputs"]["SUBSTACK"] = [2, body[0]]
            return [block]
        if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
            until = test.operand
        else:
            until = self._negate(test, test)
        return self._repeat_until_loop(until, stmt.body, test)

    def _repeat_until_loop(self, until, body, node):
        block = self._new_block("control_repeat_until")
        condition, setup, owners = self._isolated_value(until)
        if setup or owners:
            return self._poll_until(block, until, condition, setup, owners, body, node)
        self._apply_boolean(block, "CONDITION", condition, until)
        heads = self._compile_stmts(body)
        self._link(heads, block)
        if heads:
            self.blocks[block]["inputs"]["SUBSTACK"] = [2, heads[0]]
        return [block]

    def _wait_until(self, until, node):
        condition, setup, owners = self._isolated_value(until)
        if setup or owners:
            block = self._new_block("control_repeat_until")
            return self._poll_until(block, until, condition, setup, owners, [], node)
        block = self._new_block("control_wait_until")
        self._apply_boolean(block, "CONDITION", condition, until)
        return [block]

    def _poll_until(self, block, until, condition, setup, owners, body, node):
        """Loop until a condition that needs blocks of its own before it can be read.

        A custom block call, `in` on a list, or a conditional value in the
        condition runs blocks first. The loop block only rereads its input, so
        those blocks would run once. Keep the answer in a hidden variable and
        work it out again at the end of every pass.
        """
        stop = self._hidden_var(node)
        heads = setup + self._store_boolean(stop, condition, until) + self._release_owners(owners, node)
        self._apply_boolean(block, "CONDITION", Value("var", stop, True), node)
        inner = self._compile_stmts(body) + self._truth_heads(stop, until)
        self._link(inner, block)
        self.blocks[block]["inputs"]["SUBSTACK"] = [2, inner[0]]
        return heads + [block]

    def _truth_heads(self, flag, node):
        """Blocks that set flag to 1 when node is true and to 0 when it is false.

        and/or stop at the first operand that settles the answer, as in Python,
        so a later operand's blocks do not run. After break, the loop test
        starts with the break flag, and the rest of the test is skipped.
        """
        if isinstance(node, ast.BoolOp):
            heads = self._truth_heads(flag, node.values[0])
            for operand in node.values[1:]:
                open_question = Value("var", flag, True)
                if isinstance(node.op, ast.Or):
                    open_question = self._not_value(open_question, node)
                heads.append(self._if_else(open_question, self._truth_heads(flag, operand), [], node))
            return heads
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            heads = self._truth_heads(flag, node.operand)
            flipped = self._not_value(Value("var", flag, True), node)
            return heads + self._store_boolean(flag, flipped, node)
        value, setup, owners = self._isolated_value(node)
        return setup + self._store_boolean(flag, value, node) + self._release_owners(owners, node)

    def _isolated_value(self, node):
        """Compile node on its own.

        Returns the value, the blocks that must run before the value is read,
        and the hidden lists to release once it has been read.
        """
        setup = []
        owners = []
        self.hoist_stack.append(setup)
        self.ephemeral_stack.append(owners)
        try:
            value = self._compile_expr(node)
        finally:
            self.hoist_stack.pop()
            self.ephemeral_stack.pop()
        return value, setup, owners

    def _release_owners(self, owners, node):
        heads = []
        for owner in owners:
            heads.extend(self._release_ref(owner, node))
        return heads

    def _condition_arg(self, call):
        """The one condition of repeat_until or wait_until, or None to let the block report the mistake."""
        if len(call.args) + len(call.keywords) != 1:
            return None
        if call.args:
            return call.args[0]
        keyword = call.keywords[0]
        return keyword.value if keyword.arg == "condition" else None

    def _compile_with(self, stmt):
        if len(stmt.items) != 1:
            self._error(stmt, "use one with block at a time")
        item = stmt.items[0]
        if item.optional_vars is not None:
            self._error(stmt, "this with block does not assign a name")
        if not isinstance(item.context_expr, ast.Call):
            self._error(item.context_expr, "with expects kitty.repeat, kitty.forever, kitty.if_, or kitty.repeat_until")
        name = self._block_name(item.context_expr.func)
        spec = BLOCKS.get(name) if name else None
        if spec is None or spec.shape != "c":
            self._error(item.context_expr, "with expects kitty.repeat, kitty.forever, kitty.if_, or kitty.repeat_until")
        if name == "repeat_until":
            until = self._condition_arg(item.context_expr)
            if until is not None:
                return self._repeat_until_loop(until, stmt.body, item.context_expr)
        block = self._emit_spec(spec, item.context_expr)
        body = self._compile_stmts(stmt.body)
        self._link(body, block)
        if body:
            self.blocks[block]["inputs"]["SUBSTACK"] = [2, body[0]]
        return [block]

    def _compile_assign(self, stmt):
        target = stmt.targets[0] if isinstance(stmt, ast.Assign) else stmt.target
        if isinstance(stmt, ast.Assign) and len(stmt.targets) != 1:
            self._error(stmt, "assign one name at a time")
        if isinstance(target, (ast.Tuple, ast.List)):
            return self._compile_unpack(target, stmt.value, stmt)
        if isinstance(target, ast.Subscript):
            if isinstance(target.slice, ast.Slice):
                self._error(stmt, "slice assignment is not supported. Build a new list")
            return self._compile_setitem(target, stmt.value)
        py_name = self._assigned_python_name(target, stmt)
        if isinstance(stmt.value, ast.Lambda):
            symbol = self._lookup(py_name)
            if not isinstance(symbol, Proc):
                proc = self._register_lambda(py_name, stmt.value)
                self._refine_lambda_kinds([proc])
                self._compile_proc_body(proc.fn, proc)
            return None
        if isinstance(stmt.value, ast.Dict):
            return self._compile_dict_assign(py_name, stmt.value, stmt)
        if isinstance(stmt.value, ast.Call):
            proc = self._proc_from_call(stmt.value)
            if isinstance(proc, Proc) and proc.yields == "list":
                return self._store_list(py_name, self._hoist_proc_value(proc, stmt.value), stmt)
            if isinstance(proc, Proc) and proc.yields == "dict":
                return self._store_dict(py_name, self._hoist_proc_value(proc, stmt.value), stmt)
        if isinstance(stmt.value, ast.Name):
            source = self._lookup(stmt.value.id)
            if isinstance(source, Lst):
                return self._store_list(py_name, Value("list", source), stmt)
            if isinstance(source, Map):
                return self._store_dict(py_name, Value("dict", source), stmt)
        sequence_kind = _expr_sequence_kind(stmt.value)
        if sequence_kind == "slice":
            base_name = _root_name(stmt.value.value)
            base_symbol = self._lookup(base_name) if base_name else None
            if isinstance(base_symbol, Lst) or isinstance(self._lookup(py_name), Lst):
                return self._assign_sequence(py_name, stmt.value, stmt)
        elif sequence_kind is not None or isinstance(self._lookup(py_name), Lst):
            return self._assign_sequence(py_name, stmt.value, stmt)
        symbol = self._lookup(py_name)
        if symbol is None:
            symbol = self._bind_var(py_name, py_name, 0, False, False, stmt)
        if not isinstance(symbol, Var):
            self._error(stmt, f"{py_name} is not a variable")
        value = self._compile_expr(stmt.value)
        return self._store_value(symbol, value, stmt.value)

    def _compile_aug(self, stmt):
        if isinstance(stmt.target, ast.Subscript):
            return self._compile_augitem(stmt)
        py_name = self._assigned_python_name(stmt.target, stmt)
        symbol = self._lookup(py_name)
        if isinstance(symbol, Lst):
            if symbol.frozen:
                self._error(stmt, "a tuple cannot be changed")
            if symbol.unique:
                self._error(stmt, "a set uses add, as in seen.add(1)")
            if symbol.shape:
                self._error(stmt, self._dim_message(symbol))
            if not isinstance(stmt.op, ast.Add):
                self._error(stmt, "a list uses += to add items, as in items += [3]")
            return self._extend_list(symbol, stmt.value, stmt)
        if isinstance(symbol, Map):
            self._error(stmt, "set a dictionary key with scores[key] = value, or call scores.update(...)")
        if not isinstance(symbol, Var):
            self._error(stmt, f"{py_name} is not a variable")
        value = self._compile_expr(stmt.value)
        if isinstance(stmt.op, (ast.Add, ast.Sub)) and not getattr(symbol, "frame", None):
            if isinstance(stmt.op, ast.Sub):
                value = self._negate_number(value, stmt)
            return self._change_var(symbol, value, stmt.value)
        if isinstance(stmt.op, ast.Sub):
            value = self._negate_number(value, stmt)
            result = self._combine_numbers(ast.Add(), Value("var", symbol), value, stmt)
        else:
            result = self._combine_numbers(stmt.op, Value("var", symbol), value, stmt)
        return self._store_value(symbol, result, stmt)

    def _compile_expr(self, node):
        if isinstance(node, ast.Constant):
            if node.value is None or isinstance(node.value, (bytes, type(...))):
                self._error(node, "this value has no Scratch block")
            return Value("lit", node.value, isinstance(node.value, bool))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            inner = self._compile_expr(node.operand)
            if inner.kind == "lit" and isinstance(inner.data, (int, float)) and not isinstance(inner.data, bool):
                return Value("lit", -inner.data)
            return self._binary("operator_subtract", "number", "NUM1", Value("lit", 0), "NUM2", inner, False, node)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
            return self._compile_expr(node.operand)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return self._not_value(self._compile_expr(node.operand), node)
        if isinstance(node, ast.Name):
            symbol = self._lookup(node.id)
            if isinstance(symbol, Lit):
                return Value("lit", symbol.value, isinstance(symbol.value, bool))
            if isinstance(symbol, StarArgs):
                return Value("star", symbol)
            if isinstance(symbol, KwArgs):
                return Value("kw", symbol)
            if isinstance(symbol, (Var, Lst, Arg, Map)):
                boolean = (isinstance(symbol, Arg) and symbol.boolean) or (isinstance(symbol, Var) and getattr(symbol, "boolean", False))
                if isinstance(symbol, Var):
                    kind = "var"
                elif isinstance(symbol, Lst):
                    kind = "list"
                elif isinstance(symbol, Map):
                    kind = "dict"
                else:
                    kind = "arg"
                return Value(kind, symbol, boolean)
            if isinstance(symbol, Proc):
                self._error(node, f"call {node.id}(...); a custom block is not a value")
            self._error(node, f"unknown name {node.id}. Declare it with {node.id} = 0, {node.id} = [], or {node.id} = {{}}")
        if isinstance(node, ast.Attribute):
            return self._compile_attribute(node)
        if isinstance(node, ast.Call):
            return self._compile_call_expr(node)
        if isinstance(node, ast.BinOp):
            return self._compile_binop(node)
        if isinstance(node, ast.BoolOp):
            return self._compile_boolop(node)
        if isinstance(node, ast.Compare):
            return self._compile_compare(node)
        if isinstance(node, ast.Subscript):
            return self._compile_subscript(node)
        if isinstance(node, ast.JoinedStr):
            return self._compile_joined(node)
        if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.ListComp, ast.SetComp)):
            return self._sequence_value(node)
        if isinstance(node, ast.Lambda):
            self._error(node, "call a lambda, as in (lambda n: n * 2)(3)")
        if isinstance(node, ast.IfExp):
            return self._compile_ifexp(node)
        if isinstance(node, ast.Dict):
            self._error(node, "assign a dictionary, or read it with data[key]")
        self._error(node, "this expression has no Scratch block")

    def _compile_ifexp(self, node):
        if not self.hoist_stack:
            self._error(node, "use this conditional inside a script")
        boolean = self._value_kind(node.body) == "boolean" and self._value_kind(node.orelse) == "boolean"
        number = 1
        while f".v{number}" in self.scratch_vars:
            number += 1
        temp = self._bind_var(None, f".v{number}", 0, False, False, node)
        test = self._compile_expr(node.test)
        yes = self._branch_store(temp, node.body, boolean, node)
        no = self._branch_store(temp, node.orelse, boolean, node)
        block = self._new_block("control_if_else")
        self._apply_boolean(block, "CONDITION", test, node.test)
        self._link(yes, block)
        self.blocks[block]["inputs"]["SUBSTACK"] = [2, yes[0]]
        self._link(no, block)
        self.blocks[block]["inputs"]["SUBSTACK2"] = [2, no[0]]
        self.hoist_stack[-1].append(block)
        return Value("var", temp, boolean)

    def _branch_store(self, var, node, boolean, owner):
        self.hoist_stack.append([])
        try:
            value = self._compile_expr(node)
            hoisted = self.hoist_stack[-1]
        finally:
            self.hoist_stack.pop()
        if boolean:
            stored = self._store_boolean(var, value, owner)
        else:
            stored = [self._store_value(var, value, owner)]
        return hoisted + stored

    def _compile_call_expr(self, call):
        if isinstance(call.func, ast.Name) and call.func.id in self.ignored_names:
            self._error(call, f"ignored function {call.func.id} cannot be called from compiled Scratch code")
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr in self.ignored_names
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "self"
        ):
            self._error(call, f"ignored function {call.func.attr} cannot be called from compiled Scratch code")
        if isinstance(call.func, ast.Name) and call.func.id == ".kwkey":
            return self._kw_key_at(self.current_proc.kw if self.current_proc else None, call)
        if isinstance(call.func, ast.Lambda):
            proc = self._register_lambda(None, call.func)
            self._refine_lambda_kinds([proc])
            self._compile_proc_body(proc.fn, proc)
            return self._hoist_proc_value(proc, call)
        math_op = self._math_operator(call.func)
        if math_op is not None:
            if len(call.args) != 1 or call.keywords:
                self._error(call, "a math function takes one number")
            return self._compile_math(math_op, self._compile_expr(call.args[0]), call, radians=True)
        collected = self._collection_value(call)
        if collected is not None:
            return collected
        builtin = self._builtin_name(call.func)
        if builtin == "len":
            if len(call.args) != 1:
                self._error(call, "len takes one value")
            return self._compile_length(call.args[0], call)
        if builtin == "abs":
            if len(call.args) != 1:
                self._error(call, "abs takes one number")
            return self._compile_math("abs", self._compile_expr(call.args[0]), call)
        if builtin == "round":
            spec = BLOCKS["round"]
            return self._value_from_spec(spec, call)
        if _is_super_call(call) and call.func.attr != "__init__":
            return self._compile_super_value(call)
        proc = self._proc_from_call(call)
        if proc is not None:
            if not proc.returns:
                self._error(call, f"{proc.name} is a command. Define it with @kitty.number or @kitty.boolean to use the result")
            return self._hoist_proc_value(proc, call)
        remote = self._remote_instance(call)
        if remote is not None and remote != self.instance_name:
            return self._compile_remote_reporter(remote, call)
        name = self._block_name(call.func)
        if name in MATH:
            if len(call.args) != 1 or call.keywords:
                self._error(call, f"{name} takes one number")
            return self._compile_math(MATH[name], self._compile_expr(call.args[0]), call)
        if name == "math":
            if len(call.args) != 2:
                self._error(call, 'kitty.math("sqrt", n) takes an operation and a number')
            op = _constant(call.args[0])
            if op not in _MATH_OPS:
                self._error(call.args[0], "unknown math operation")
            return self._compile_math(op, self._compile_expr(call.args[1]), call)
        if name == "length":
            if len(call.args) != 1:
                self._error(call, "length takes one list or text")
            return self._compile_length(call.args[0], call)
        if name == "contains":
            if len(call.args) != 2:
                self._error(call, "contains takes a list or text, then an item")
            return self._compile_contains(call.args[0], call.args[1], call)
        spec = BLOCKS.get(name) if name else None
        if spec is not None:
            if spec.shape == "stack" or spec.shape == "c":
                self._error(call, f"kitty.{name} is a command, not a value")
            return self._value_from_spec(spec, call)
        text = self._text_method_value(call)
        if text is not None:
            return text
        self._error(call, "unknown Scratch value")

    def _compile_length(self, node, owner):
        if isinstance(node, ast.Name):
            symbol = self._lookup(node.id)
            if isinstance(symbol, (StarArgs, KwArgs)):
                return Value("arg", symbol.count)
        dimension = self._partial_dimension(node)
        if dimension is not None:
            return dimension
        value = self._compile_expr(node)
        if value.kind == "list":
            return self._length_of(value.data, owner)
        if value.kind == "dict":
            return self._length_of(value.data.keys, owner)
        block = self._new_block("operator_length")
        self._apply_slot(block, "STRING", "text", value, node)
        return Value("block", block)

    def _compile_contains(self, container_node, item_node, owner):
        container = self._compile_expr(container_node)
        item = self._compile_expr(item_node)
        if container.kind == "list":
            return self._list_contains(container.data, item, item_node)
        if container.kind == "dict":
            return self._list_contains(container.data.keys, item, item_node)
        block = self._new_block("operator_contains")
        self._apply_slot(block, "STRING1", "text", container, container_node)
        self._apply_slot(block, "STRING2", "text", item, item_node)
        return Value("block", block, True)

    def _compile_math(self, op, value, node, radians=False):
        if radians and op in _RADIANS:
            value = self._combine_numbers(ast.Mult(), value, Value("lit", _RAD_TO_DEG), node)
        block = self._new_block("operator_mathop")
        self.blocks[block]["fields"]["OPERATOR"] = [op, None]
        self._apply_slot(block, "NUM", "number", value, node)
        result = Value("block", block)
        if radians and op in _INVERSE:
            result = self._combine_numbers(ast.Mult(), result, Value("lit", _DEG_TO_RAD), node)
        return result

    def _math_operator(self, func):
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in self.math_aliases:
            op = _MATH_FUNCS.get(func.attr)
            if op is None:
                self._error(func, f"math.{func.attr} has no Scratch block")
            return op
        if isinstance(func, ast.Name) and func.id in self.math_names:
            return self.math_names[func.id]
        return None

    def _combine_numbers(self, op, left, right, node):
        if left.kind == "lit" and right.kind == "lit" and _is_number(left.data) and _is_number(right.data):
            if isinstance(op, (ast.Div, ast.FloorDiv, ast.Mod)) and right.data == 0:
                self._error(node, "division by zero")
            if isinstance(op, ast.FloorDiv):
                return Value("lit", left.data // right.data)
            if type(op) in (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod):
                return Value("lit", _fold_numbers(op, left.data, right.data))
        ops = {
            ast.Add: ("operator_add", "NUM1", "NUM2"),
            ast.Sub: ("operator_subtract", "NUM1", "NUM2"),
            ast.Mult: ("operator_multiply", "NUM1", "NUM2"),
            ast.Div: ("operator_divide", "NUM1", "NUM2"),
            ast.Mod: ("operator_mod", "NUM1", "NUM2"),
        }
        for op_type, (opcode, left_name, right_name) in ops.items():
            if isinstance(op, op_type):
                return self._binary(opcode, "number", left_name, left, right_name, right, False, node)
        if isinstance(op, ast.FloorDiv):
            divided = self._binary("operator_divide", "number", "NUM1", left, "NUM2", right, False, node)
            return self._compile_math("floor", divided, node)
        self._error(node, "this operator has no Scratch block")

    def _negate_number(self, value, node):
        if value.kind == "lit" and _is_number(value.data):
            return Value("lit", -value.data)
        return self._binary("operator_subtract", "number", "NUM1", Value("lit", 0), "NUM2", value, False, node)

    def _collection_of(self, call):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
            return None
        symbol = self._receiver_symbol(call.func.value)
        if isinstance(symbol, (Lst, Map)):
            return symbol, call.func.attr
        return None

    def _receiver_symbol(self, node):
        if isinstance(node, ast.Name):
            return self._lookup(node.id)
        if isinstance(node, ast.Attribute) and self._attr_owner(node.value) == "self":
            return self._lookup(node.attr)
        return None

    def _collection_statement(self, call):
        found = self._collection_of(call)
        if found is None:
            return None
        symbol, name = found
        if isinstance(symbol, Lst):
            return self._list_statement(symbol, name, call)
        return self._dict_statement(symbol, name, call)

    def _collection_value(self, call):
        found = self._collection_of(call)
        if found is None:
            return None
        symbol, name = found
        if isinstance(symbol, Lst):
            return self._list_value(symbol, name, call)
        return self._dict_value(symbol, name, call)

    def _list_statement(self, lst, name, call):
        self._flat_list(lst, call)
        self._no_keywords(call)
        if lst.frozen:
            self._error(call, "a tuple cannot be changed")
        if lst.unique:
            return self._set_statement(lst, name, call)
        if name == "append":
            self._take_args(call, 1, "append takes one item")
            return [self._add_item(lst, self._compile_expr(call.args[0]), call)]
        if name == "extend":
            self._take_args(call, 1, "extend takes a list")
            return self._extend_list(lst, call.args[0], call)
        if name == "insert":
            self._take_args(call, 2, "insert takes an index and an item")
            index = self._python_to_scratch_index(self._compile_expr(call.args[0]), self._length_of(lst), call)
            return [self._insert_item(lst, index, self._compile_expr(call.args[1]), call)]
        if name == "remove":
            self._take_args(call, 1, "remove takes one item")
            return self._remove_item(lst, self._compile_expr(call.args[0]), call)
        if name == "clear":
            self._take_args(call, 0, "clear takes no values")
            return [self._delete_all_items(lst)]
        if name == "pop":
            if len(call.args) > 1:
                self._error(call, "pop takes no index, or one index")
            index = Value("lit", "last") if not call.args else self._python_to_scratch_index(self._compile_expr(call.args[0]), self._length_of(lst), call)
            return [self._delete_at(lst, index, call)]
        self._error(call, "a list has append, extend, insert, remove, pop, clear, and index")

    def _list_value(self, lst, name, call):
        self._flat_list(lst, call)
        self._no_keywords(call)
        if lst.frozen and name in {"append", "extend", "insert", "remove", "clear", "pop"}:
            self._error(call, "a tuple cannot be changed")
        if lst.unique and name not in {"pop"}:
            self._error(call, "a set has add, discard, remove, and clear")
        if name == "index":
            self._take_args(call, 1, "index takes one item")
            found = self._item_number(lst, self._compile_expr(call.args[0]), call)
            return self._binary("operator_subtract", "number", "NUM1", found, "NUM2", Value("lit", 1), False, call)
        if name == "pop":
            if len(call.args) > 1:
                self._error(call, "pop takes no index, or one index")
            if call.args:
                index = self._python_to_scratch_index(self._compile_expr(call.args[0]), self._length_of(lst), call)
            else:
                index = Value("lit", "last")
            return self._pop_value(lst, index, call)
        if name in {"append", "extend", "insert", "remove", "clear"}:
            self._error(call, f"{name} changes the list. Call it on its own line")
        self._error(call, "a list has append, extend, insert, remove, pop, clear, and index")

    def _dict_statement(self, mapping, name, call):
        self._no_keywords(call)
        if name == "clear":
            self._take_args(call, 0, "clear takes no values")
            return [self._delete_all_items(mapping.keys), self._delete_all_items(mapping.values)]
        if name == "update":
            self._take_args(call, 1, "update takes a dictionary")
            return self._dict_update(mapping, call.args[0], call)
        if name == "pop":
            self._take_args(call, 1, "pop takes a key")
            return self._dict_delete_key(mapping, self._compile_expr(call.args[0]), call)
        if name == "get":
            self._error(call, "get returns a value. Use it in say, set, or other blocks")
        self._error(call, "a dictionary has get, pop, update, and clear")

    def _dict_value(self, mapping, name, call):
        self._no_keywords(call)
        if name == "get":
            if len(call.args) == 1:
                return self._dict_get(mapping, call.args[0], call)
            if len(call.args) == 2:
                return self._dict_get_default(mapping, call.args[0], call.args[1], call)
            self._error(call, "get takes a key, or a key and a default")
        if name == "pop":
            self._take_args(call, 1, "pop takes a key")
            _blocks, value = self._dict_pop_blocks(mapping, self._compile_expr(call.args[0]), call)
            return value
        if name in {"clear", "update"}:
            self._error(call, f"{name} changes the dictionary. Call it on its own line")
        self._error(call, "a dictionary has get, pop, update, and clear")

    def _flat_list(self, lst, node):
        if lst.shape:
            self._error(node, self._dim_message(lst))

    def _no_keywords(self, call):
        if call.keywords:
            self._error(call, "write the values in order")

    def _take_args(self, call, count, message):
        if len(call.args) != count:
            self._error(call, message)

    def _extend_list(self, lst, node, owner):
        if isinstance(node, ast.List):
            heads = []
            for elt in node.elts:
                if isinstance(elt, ast.Starred):
                    self._error(elt, "extend a list with another list")
                heads.append(self._add_item(lst, self._compile_expr(elt), owner))
            return heads
        other = self._receiver_symbol(node)
        if not isinstance(other, Lst):
            self._error(node, "extend takes a list")
        self._flat_list(other, node)
        return self._walk_list(other, lambda index: [self._add_item(lst, self._item_value(other, Value("var", index), owner), owner)], owner)

    def _remove_item(self, lst, item, node):
        heads, item = self._pin_value(item, node)
        index = self._item_number(lst, item, node)
        heads2, index = self._pin_value(index, node)
        heads.extend(heads2)
        heads.append(self._delete_at(lst, index, node))
        return heads

    def _pop_value(self, lst, index, node):
        if not self.hoist_stack:
            self._error(node, "use pop inside a script")
        heads, index = self._pin_value(index, node)
        number = 1
        while f".v{number}" in self.scratch_vars:
            number += 1
        temp = self._bind_var(None, f".v{number}", 0, False, False, node)
        heads.append(self._store_value(temp, self._item_value(lst, index, node), node))
        heads.append(self._delete_at(lst, index, node))
        self.hoist_stack[-1].extend(heads)
        return Value("var", temp)

    def _dict_delete_key(self, mapping, key, node):
        heads, key = self._pin_value(key, node)
        index = self._item_number(mapping.keys, key, node)
        more, index = self._pin_value(index, node)
        heads.extend(more)
        heads.append(self._delete_at(mapping.keys, index, node))
        heads.append(self._delete_at(mapping.values, index, node))
        return heads

    def _dict_pop_blocks(self, mapping, key, node):
        heads, key = self._pin_value(key, node)
        index = self._item_number(mapping.keys, key, node)
        more, index = self._pin_value(index, node)
        heads.extend(more)
        number = 1
        while f".v{number}" in self.scratch_vars:
            number += 1
        temp = self._bind_var(None, f".v{number}", 0, False, False, node)
        heads.append(self._store_value(temp, self._item_value(mapping.values, index, node), node))
        heads.append(self._delete_at(mapping.keys, index, node))
        heads.append(self._delete_at(mapping.values, index, node))
        if self.hoist_stack:
            self.hoist_stack[-1].extend(heads)
            return [], Value("var", temp)
        return heads, Value("var", temp)

    def _dict_get_default(self, mapping, key_node, default_node, node):
        if not self.hoist_stack:
            self._error(node, "use get inside a script")
        key = self._compile_expr(key_node)
        heads, key = self._pin_value(key, node)
        number = 1
        while f".v{number}" in self.scratch_vars:
            number += 1
        temp = self._bind_var(None, f".v{number}", 0, False, False, node)
        yes = [self._store_value(temp, self._item_value(mapping.values, self._item_number(mapping.keys, key, node), node), node)]
        self.hoist_stack.append([])
        try:
            default_value = self._compile_expr(default_node)
            default_heads = list(self.hoist_stack[-1])
        finally:
            self.hoist_stack.pop()
        no = default_heads + [self._store_value(temp, default_value, node)]
        block = self._new_block("control_if_else")
        self._apply_boolean(block, "CONDITION", self._list_contains(mapping.keys, key, node), node)
        self._link(yes, block)
        self.blocks[block]["inputs"]["SUBSTACK"] = [2, yes[0]]
        self._link(no, block)
        self.blocks[block]["inputs"]["SUBSTACK2"] = [2, no[0]]
        heads.append(block)
        self.hoist_stack[-1].extend(heads)
        return Value("var", temp)

    def _dict_update(self, mapping, node, owner):
        if isinstance(node, ast.Dict):
            if any(key is None for key in node.keys):
                self._error(node, "a dictionary is written as {key: value}")
            heads = []
            for key_node, value_node in zip(node.keys, node.values):
                heads.extend(self._dict_upsert(mapping, key_node, value_node, owner))
            return heads
        other = self._receiver_symbol(node)
        if not isinstance(other, Map):
            self._error(node, "update takes a dictionary")
        return self._walk_list(
            other.keys,
            lambda index: self._dict_upsert_values(
                mapping,
                self._item_value(other.keys, Value("var", index), owner),
                self._item_value(other.values, Value("var", index), owner),
                owner,
            ),
            owner,
        )

    def _walk_list(self, lst, step, node):
        index = self._hidden_var(node, 1)
        body = step(index)
        body.append(self._change_var(index, Value("lit", 1), node))
        return [
            self._store_value(index, Value("lit", 1), node),
            self._repeat_block(self._length_of(lst, node), body, node),
        ]

    def _insert_item(self, lst, index, item, node):
        storage, frame = self._backing(lst)
        if frame is not None:
            return self._span_call(storage, "insert", [frame, index, item], node)
        return self._raw_insert(lst, index, item, node)

    def _delete_at(self, lst, index, node):
        storage, frame = self._backing(lst)
        if frame is not None:
            return self._span_call(storage, "delete", [frame, index], node)
        return self._raw_delete(lst, index, node)

    def _raw_insert(self, lst, index, item, node):
        block = self._new_block("data_insertatlist")
        self.blocks[block]["fields"]["LIST"] = [lst.name, lst.lid]
        self._apply_slot(block, "INDEX", "index", index, node)
        self._apply_slot(block, "ITEM", "text", item, node)
        return block

    def _raw_delete(self, lst, index, node):
        block = self._new_block("data_deleteoflist")
        self.blocks[block]["fields"]["LIST"] = [lst.name, lst.lid]
        self._apply_slot(block, "INDEX", "index", index, node)
        return block

    def _compile_binop(self, node):
        left = self._compile_expr(node.left)
        right = self._compile_expr(node.right)
        if isinstance(node.op, ast.Add) and _either_text(left, right):
            if left.kind == "lit" and right.kind == "lit":
                return Value("lit", f"{_as_text(left.data)}{_as_text(right.data)}")
            joined = self._binary("operator_join", "text", "STRING1", left, "STRING2", right, False, node)
            joined.text = True
            return joined
        return self._combine_numbers(node.op, left, right, node)

    def _compile_boolop(self, node):
        opcode = "operator_and" if isinstance(node.op, ast.And) else "operator_or"
        values = [self._compile_expr(item) for item in node.values]
        current = values[0]
        for value in values[1:]:
            current = self._boolean_pair(opcode, current, value, node)
        return current

    def _compile_compare(self, node):
        if len(node.ops) != 1 and not node.ops:
            self._error(node, "empty comparison")
        left = self._compile_expr(node.left)
        current = None
        for op, comparator in zip(node.ops, node.comparators):
            right = self._compile_expr(comparator)
            piece = self._one_compare(op, left, right, node)
            current = piece if current is None else self._boolean_pair("operator_and", current, piece, node)
            left = right
        return current

    def _one_compare(self, op, left, right, node):
        if isinstance(op, (ast.In, ast.NotIn)):
            contained = self._contains_values(right, left, node)
            if isinstance(op, ast.NotIn):
                return self._not_value(contained, node)
            return contained
        table = {
            ast.Eq: "operator_equals",
            ast.Gt: "operator_gt",
            ast.Lt: "operator_lt",
        }
        for op_type, opcode in table.items():
            if isinstance(op, op_type):
                return self._binary(opcode, "text", "OPERAND1", left, "OPERAND2", right, True, node)
        if isinstance(op, ast.NotEq):
            return self._not_value(self._binary("operator_equals", "text", "OPERAND1", left, "OPERAND2", right, True, node), node)
        if isinstance(op, ast.GtE):
            return self._not_value(self._binary("operator_lt", "text", "OPERAND1", left, "OPERAND2", right, True, node), node)
        if isinstance(op, ast.LtE):
            return self._not_value(self._binary("operator_gt", "text", "OPERAND1", left, "OPERAND2", right, True, node), node)
        self._error(node, "this comparison has no Scratch block")

    def _contains_values(self, container, item, node):
        if container.kind == "star":
            return self._slots_contain(container.data.slots, container.data.count, item, node)
        if container.kind == "kw":
            return self._slots_contain([key for key, _value in container.data.pairs], container.data.count, item, node)
        if container.kind == "list":
            return self._list_contains(container.data, item, node)
        if container.kind == "dict":
            return self._list_contains(container.data.keys, item, node)
        block = self._new_block("operator_contains")
        self._apply_slot(block, "STRING1", "text", container, node)
        self._apply_slot(block, "STRING2", "text", item, node)
        return Value("block", block, True)

    def _compile_subscript(self, node):
        if isinstance(node.slice, ast.Slice):
            return self._compile_get_slice(node)
        base, exprs = self._peel_subscripts(node)
        if isinstance(base, ast.Name):
            symbol = self._lookup(base.id)
            if isinstance(symbol, StarArgs):
                if len(exprs) != 1:
                    self._error(node, "args takes one index")
                return self._star_item(symbol, exprs[0], node)
            if isinstance(symbol, KwArgs):
                if len(exprs) != 1:
                    self._error(node, "kwargs takes one key")
                return self._kw_item(symbol, exprs[0], node)
        container = self._compile_expr(base)
        if container.kind == "dict":
            if len(exprs) != 1:
                self._error(node, "a dictionary takes one key")
            return self._dict_get(container.data, exprs[0], node)
        if container.kind == "list":
            index = self._flat_index(container.data, exprs, node)
            return self._item_value(container.data, index, node)
        if len(exprs) != 1:
            return self._compile_text_chain(node)
        return self._text_index(container, exprs[0], node)

    def _compile_setitem(self, target, value_node):
        base, exprs = self._peel_subscripts(target)
        container = self._compile_expr(base)
        if container.kind == "dict":
            if len(exprs) != 1:
                self._error(target, "a dictionary takes one key")
            return self._dict_upsert(container.data, exprs[0], value_node, target)
        if container.kind != "list":
            self._error(target, "text cannot be changed. Build a new string")
        if container.data.frozen:
            self._error(target, "a tuple cannot be changed")
        if container.data.unique:
            self._error(target, "a set has no positions. Use add or discard")
        index = self._flat_index(container.data, exprs, target)
        value = self._compile_expr(value_node)
        return self._replace_item(container.data, index, value, target)

    def _compile_augitem(self, stmt):
        base, exprs = self._peel_subscripts(stmt.target)
        container = self._compile_expr(base)
        if container.kind == "dict":
            if len(exprs) != 1:
                self._error(stmt.target, "a dictionary takes one key")
            return self._dict_aug(container.data, exprs[0], stmt)
        if container.kind != "list":
            self._error(stmt.target, "text cannot be changed. Build a new string")
        if container.data.frozen:
            self._error(stmt.target, "a tuple cannot be changed")
        if container.data.unique:
            self._error(stmt.target, "a set has no positions. Use add or discard")
        index = self._flat_index(container.data, exprs, stmt.target)
        heads, index = self._reusable_number(index, stmt)
        current = self._item_value(container.data, index, stmt)
        value = self._compile_expr(stmt.value)
        total = self._combine_numbers(stmt.op, current, value, stmt)
        heads.append(self._replace_item(container.data, index, total, stmt))
        return heads

    def _peel_subscripts(self, node):
        groups = []
        current = node
        while isinstance(current, ast.Subscript):
            groups.append(current)
            current = current.value
        groups.reverse()
        exprs = []
        for sub in groups:
            exprs.extend(self._slice_exprs(sub))
        if not exprs:
            self._error(node, "a list index is a number")
        return current, exprs

    def _slice_exprs(self, sub):
        sl = sub.slice
        if isinstance(sl, ast.Slice):
            self._error(sub, "list indexes are numbers, not slices")
        if isinstance(sl, ast.Tuple):
            if not sl.elts or any(isinstance(elt, ast.Starred) for elt in sl.elts):
                self._error(sub, "a list index is a number")
            return list(sl.elts)
        return [sl]

    def _partial_dimension(self, node):
        if isinstance(node, ast.Subscript):
            base, exprs = self._peel_subscripts(node)
        elif isinstance(node, (ast.Name, ast.Attribute)):
            base, exprs = node, []
        else:
            return None
        if not isinstance(base, (ast.Name, ast.Attribute)):
            return None
        value = self._compile_expr(base)
        if value.kind != "list" or not value.data.shape:
            return None
        rank = len(value.data.shape)
        if len(exprs) > rank:
            self._error(node, self._dim_message(value.data))
        if len(exprs) == rank:
            return None
        if value.data.ident is not None:
            return self._shape_size(value.data, len(exprs), node)
        return Value("lit", value.data.shape[len(exprs)])

    def _flat_index(self, lst, exprs, node):
        rank = len(lst.shape)
        if not rank and len(exprs) > 1 and lst.ident is not None:
            lst.shape = tuple(0 for _ in range(len(exprs)))
            rank = len(exprs)
        if rank and len(exprs) != rank:
            self._error(node, self._dim_message(lst))
        if not rank and len(exprs) != 1:
            self._error(node, f"{lst.name} has one dimension")
        values = [self._compile_expr(expr) for expr in exprs]
        if not rank:
            length = self._length_of(lst) if _index_needs_length(values[0]) else 0
            return self._python_to_scratch_index(values[0], length, node, allow_menu=True)
        if any(value.kind == "lit" and isinstance(value.data, str) for value in values):
            self._error(node, f"indexes of {lst.name} are numbers starting at 0")
        numbers = []
        converted = []
        all_lit = True
        runtime = lst.ident is not None
        for dim, value in enumerate(values):
            if value.kind == "lit" and _is_number(value.data):
                numbers.append(value.data)
            else:
                all_lit = False
            size = self._shape_size(lst, dim, node) if runtime else lst.shape[dim]
            converted.append(self._python_to_scratch_index(value, size, node))
        if all_lit and _known_shape(lst.shape):
            self._check_axis_bounds(lst, numbers, node)
            if not runtime:
                return Value("lit", _fold_flat_index(lst.shape, [item.data for item in converted]))
        return self._flat_index_blocks(lst.shape, converted, node, lst if runtime else None)

    def _flat_index_blocks(self, shape, values, node, lst=None):
        acc = values[0]
        for dim in range(1, len(values)):
            size = self._shape_size(lst, dim, node) if lst is not None else Value("lit", shape[dim])
            shifted = self._binary("operator_subtract", "number", "NUM1", acc, "NUM2", Value("lit", 1), False, node)
            scaled = self._binary("operator_multiply", "number", "NUM1", shifted, "NUM2", size, False, node)
            acc = self._binary("operator_add", "number", "NUM1", scaled, "NUM2", values[dim], False, node)
        return acc

    def _check_axis_bounds(self, lst, numbers, node):
        for axis, (size, number) in enumerate(zip(lst.shape, numbers), start=1):
            if number != int(number) or number < -size or number >= size:
                self._error(node, f"dimension {axis} of {lst.name} has {size} items. Indexes run from 0 to {size - 1}")

    def _dim_message(self, lst):
        letters = ["i", "j", "k", "a", "b", "c"]
        names = [letters[i] if i < len(letters) else f"i{i + 1}" for i in range(len(lst.shape))]
        return f"{lst.name} has {len(lst.shape)} dimensions. Use {lst.name}[" + "][".join(names) + "]"

    def _item_value(self, lst, index, node):
        storage, frame = self._backing(lst)
        if frame is not None and not (index.kind == "lit" and index.data == "all"):
            index = self._span_physical(lst, index, node)
        return self._raw_item(storage, index, node)

    def _replace_item(self, lst, index, value, node):
        storage, frame = self._backing(lst)
        if frame is not None and not (index.kind == "lit" and index.data == "all"):
            index = self._span_physical(lst, index, node)
        return self._raw_replace(storage, index, value, node)

    def _raw_item(self, lst, index, node):
        block = self._new_block("data_itemoflist")
        self.blocks[block]["fields"]["LIST"] = [lst.name, lst.lid]
        self._apply_slot(block, "INDEX", "index", index, node)
        return Value("block", block)

    def _raw_replace(self, lst, index, value, node):
        block = self._new_block("data_replaceitemoflist")
        self.blocks[block]["fields"]["LIST"] = [lst.name, lst.lid]
        self._apply_slot(block, "INDEX", "index", index, node)
        self._apply_slot(block, "ITEM", "text", value, node)
        return block

    def _reusable_number(self, value, node):
        if value.kind in {"lit", "var", "arg"}:
            return [], value
        number = 1
        while f".idx{number}" in self.scratch_vars:
            number += 1
        var = self._bind_var(None, f".idx{number}", 0, False, False, node)
        return [self._store_value(var, value, node)], Value("var", var)

    def _value_from_spec(self, spec, call):
        block = self._emit_spec(spec, call)
        return Value("block", block, spec.shape == "boolean")

    def _emit_spec(self, spec, call):
        values = self._bind_params(spec, call)
        values = self._shift_index_args(spec, values, call)
        block = self._new_block(spec.opcode)
        if spec.extension:
            self.project.extensions.add(spec.extension)
        for scratch_name, raw in spec.fixed_fields:
            self.blocks[block]["fields"][scratch_name] = [raw, None]
        for param, value in zip(spec.params, values):
            _py, scratch, slot, *_rest = param
            self._apply_slot(block, scratch, slot, value, call)
        return block

    def _bind_params(self, spec, call):
        params = spec.params
        if call.keywords and any(item.arg is None for item in call.keywords):
            self._error(call, "Scratch blocks do not take **kwargs")
        names = [param[0] for param in params]
        bound = {}
        if len(call.args) > len(params):
            label = self._block_name(call.func) or spec.opcode
            self._error(call, f"{label} takes {len(params)} values")
        for param, arg in zip(params, call.args):
            bound[param[0]] = self._compile_expr(arg)
        for keyword in call.keywords:
            if keyword.arg not in names:
                self._error(keyword, f"unknown input {keyword.arg}")
            if keyword.arg in bound:
                self._error(keyword, f"{keyword.arg} was given twice")
            bound[keyword.arg] = self._compile_expr(keyword.value)
        values = []
        for param in params:
            name = param[0]
            default = param[3] if len(param) == 4 else REQUIRED
            if name in bound:
                values.append(bound[name])
            elif default is not REQUIRED:
                values.append(Value("lit", default))
            else:
                self._error(call, f"missing {name}")
        return values

    def _emit_proc_call(self, proc, call):
        return self._call_block(proc, self._bind_proc_args(proc, call), call)

    def _passed_ref(self, param, value, node):
        carries = getattr(param, "carries", None)
        if carries == "list":
            if value.kind != "list" or value.data.ident is None:
                self._error(node, f"pass a list to {param.name}")
            rank = getattr(param, "grid_rank", 0)
            if rank and len(value.data.shape) != rank:
                self._error(node, f"{param.name} has {rank} dimensions")
            return Value("var", value.data.ident)
        if carries == "dict":
            if value.kind != "dict" or value.data.ident is None:
                self._error(node, f"pass a dictionary to {param.name}")
            return Value("var", value.data.ident)
        return value

    def _bind_proc_args(self, proc, call):
        if any(keyword.arg is None for keyword in call.keywords):
            self._error(call, "pass each keyword by name")
        if any(isinstance(arg, ast.Starred) for arg in call.args):
            self._error(call, "pass extra values directly, as in f(1, 2, 3)")
        if proc.user_params or proc.star is not None or proc.kw is not None or proc.scope_args:
            user_params = proc.user_params
        else:
            user_params = list(proc.params)
        positional = [param for param in user_params if not param.keyword_only]
        if proc.star is None and len(call.args) > len(positional):
            self._error(call, f"{proc.name} takes {len(positional)} values")
        extras = call.args[len(positional):]
        if len(extras) > _STAR_LIMIT:
            self._error(call, f"pass at most {_STAR_LIMIT} extra values")
        bound = {}
        for param, arg in zip(positional, call.args):
            bound[param.name] = self._compile_expr(arg)
        extra_kw = []
        names = {param.name for param in user_params}
        for keyword in call.keywords:
            if keyword.arg in bound:
                self._error(keyword, f"{keyword.arg} was given twice")
            if keyword.arg in names:
                bound[keyword.arg] = self._compile_expr(keyword.value)
            elif proc.kw is not None:
                extra_kw.append(keyword)
            else:
                self._error(keyword, "unknown custom block input")
        if len(extra_kw) > _KW_LIMIT:
            self._error(call, f"pass at most {_KW_LIMIT} extra keywords")
        values = []
        for param in user_params:
            if param.name in bound:
                values.append(self._passed_ref(param, bound[param.name], call))
            elif param.default is not NO_DEFAULT:
                values.append(Value("lit", param.default, isinstance(param.default, bool)))
            elif param.boolean:
                values.append(Value("lit", False, True))
            else:
                self._error(call, f"missing {param.name}")
        if proc.star is not None:
            values.append(Value("lit", len(extras)))
            for index in range(_STAR_LIMIT):
                if index < len(extras):
                    values.append(self._compile_expr(extras[index]))
                else:
                    values.append(Value("lit", ""))
        if proc.kw is not None:
            values.append(Value("lit", len(extra_kw)))
            for index in range(_KW_LIMIT):
                if index < len(extra_kw):
                    values.append(Value("lit", extra_kw[index].arg))
                    values.append(self._compile_expr(extra_kw[index].value))
                else:
                    values.append(Value("lit", ""))
                    values.append(Value("lit", ""))
        for scope in proc.scope_args:
            values.append(Value("arg", scope))
        return values

    def _star_item(self, star, expr, node):
        index = self._compile_expr(expr)
        if index.kind == "lit" and _is_number(index.data) and float(index.data).is_integer():
            number = int(index.data)
            if number < 0 or number >= len(star.slots):
                self._error(node, f"extra values are numbered 0 to {_STAR_LIMIT - 1}")
            return Value("arg", star.slots[number])
        heads, index = self._pin_value(index, node)
        temp = self._hidden_var(node)
        heads.append(self._store_value(temp, Value("lit", ""), node))
        count = Value("arg", star.count)
        for number, slot in enumerate(star.slots):
            same = self._binary("operator_equals", "text", "OPERAND1", index, "OPERAND2", Value("lit", number), True, node)
            live = self._binary("operator_lt", "text", "OPERAND1", Value("lit", number), "OPERAND2", count, True, node)
            cond = self._boolean_pair("operator_and", same, live, node)
            heads.append(self._if_else(cond, [self._store_value(temp, Value("arg", slot), node)], [], node))
        self._hoist(heads)
        return Value("var", temp)

    def _kw_item(self, kw, expr, node):
        key = self._compile_expr(expr)
        heads, key = self._pin_value(key, node)
        temp = self._hidden_var(node)
        heads.append(self._store_value(temp, Value("lit", ""), node))
        count = Value("arg", kw.count)
        for number, (key_arg, value_arg) in enumerate(kw.pairs):
            same = self._binary("operator_equals", "text", "OPERAND1", key, "OPERAND2", Value("arg", key_arg), True, node)
            live = self._binary("operator_lt", "text", "OPERAND1", Value("lit", number), "OPERAND2", count, True, node)
            cond = self._boolean_pair("operator_and", same, live, node)
            heads.append(self._if_else(cond, [self._store_value(temp, Value("arg", value_arg), node)], [], node))
        self._hoist(heads)
        return Value("var", temp)

    def _kw_key_at(self, kw, call):
        if kw is None or len(call.args) != 1:
            self._error(call, "kwargs has no keys here")
        index = self._compile_expr(call.args[0])
        heads, index = self._pin_value(index, call)
        temp = self._hidden_var(call)
        heads.append(self._store_value(temp, Value("lit", ""), call))
        count = Value("arg", kw.count)
        for number, (key_arg, _value_arg) in enumerate(kw.pairs):
            same = self._binary("operator_equals", "text", "OPERAND1", index, "OPERAND2", Value("lit", number), True, call)
            live = self._binary("operator_lt", "text", "OPERAND1", Value("lit", number), "OPERAND2", count, True, call)
            cond = self._boolean_pair("operator_and", same, live, call)
            heads.append(self._if_else(cond, [self._store_value(temp, Value("arg", key_arg), call)], [], call))
        self._hoist(heads)
        return Value("var", temp)

    def _slots_contain(self, slots, count, item, node):
        current = None
        for number, slot in enumerate(slots):
            same = self._binary("operator_equals", "text", "OPERAND1", item, "OPERAND2", Value("arg", slot), True, node)
            live = self._binary("operator_lt", "text", "OPERAND1", Value("lit", number), "OPERAND2", Value("arg", count), True, node)
            piece = self._boolean_pair("operator_and", same, live, node)
            current = piece if current is None else self._boolean_pair("operator_or", current, piece, node)
        return current

    def _binary(self, opcode, slot, left_name, left, right_name, right, boolean, node):
        block = self._new_block(opcode)
        self._apply_slot(block, left_name, slot, left, node)
        self._apply_slot(block, right_name, slot, right, node)
        return Value("block", block, boolean)

    def _boolean_pair(self, opcode, left, right, node):
        block = self._new_block(opcode)
        self._apply_boolean(block, "OPERAND1", left, node)
        self._apply_boolean(block, "OPERAND2", right, node)
        return Value("block", block, True)

    def _not_value(self, value, node):
        if value.kind == "lit" and isinstance(value.data, bool):
            return Value("lit", not value.data, True)
        block = self._new_block("operator_not")
        self._apply_boolean(block, "OPERAND", value, node)
        return Value("block", block, True)

    def _apply_boolean(self, block, scratch_name, value, node):
        if value.kind == "lit" and isinstance(value.data, bool):
            value = self._bool_constant(value.data)
        if value.kind == "var" and value.boolean:
            value = self._binary("operator_equals", "text", "OPERAND1", value, "OPERAND2", Value("lit", 1), True, node)
        if not value.boolean and value.kind != "arg":
            self._error(node, "Scratch needs a boolean block here, such as a comparison or touching")
        if value.kind == "arg" and not value.data.boolean and not value.boolean:
            self._error(node, "this parameter is not a boolean")
        reporter = self._as_reporter(value, block, node)
        self.blocks[block]["inputs"][scratch_name] = [2, reporter]

    def _bool_constant(self, value):
        block = self._new_block("operator_equals")
        self._literal_input(block, "OPERAND1", "text", "1")
        self._literal_input(block, "OPERAND2", "text", "1" if value else "0")
        return Value("block", block, True)

    def _apply_slot(self, block, scratch_name, slot, value, node):
        if slot == "variable":
            var = self._as_var(value, node)
            self.blocks[block]["fields"][scratch_name] = [var.name, var.vid]
            return
        if slot == "list":
            lst = self._as_list(value, node)
            if lst.shape and self.blocks[block]["opcode"] in _ND_LIST_BLOCKED:
                self._error(node, self._dim_message(lst))
            self.blocks[block]["fields"][scratch_name] = [lst.name, lst.lid]
            return
        if slot == "broadcast_input":
            if value.kind != "lit" or not isinstance(value.data, str):
                self._error(node, "broadcast message must be text")
            name, bid = self._broadcast(value.data)
            self.blocks[block]["inputs"][scratch_name] = [1, [11, name, bid]]
            return
        if slot.startswith("field:"):
            if value.kind != "lit" or not isinstance(value.data, str):
                self._error(node, "this menu needs a name, not a block")
            self.blocks[block]["fields"][scratch_name] = [_normalize_field(slot, value.data, node), None]
            return
        if slot.startswith("menu:"):
            self._apply_menu(block, scratch_name, slot.split(":", 1)[1], value, node)
            return
        if slot == "boolean":
            self._apply_boolean(block, scratch_name, value, node)
            return
        if slot == "color":
            self._apply_color(block, scratch_name, value, node)
            return
        if slot in _NUMBER_TYPES or slot == "index":
            self._apply_number(block, scratch_name, slot, value, node)
            return
        if slot in _TEXT_TYPES or slot == "text":
            self._apply_text(block, scratch_name, value, node)
            return
        self._error(node, f"unsupported input {slot}")

    def _apply_menu(self, block, scratch_name, menu, value, node):
        opcode, field = MENUS[menu]
        if value.kind == "lit":
            if not isinstance(value.data, str):
                self._error(node, "this menu needs text")
            choice = _normalize_menu(menu, value.data)
            shadow = self._new_block(opcode, shadow=True, parent=block)
            self.blocks[shadow]["fields"][field] = [choice, None]
            self.blocks[block]["inputs"][scratch_name] = [1, shadow]
            return
        shadow = self._new_block(opcode, shadow=True, parent=block)
        self.blocks[shadow]["fields"][field] = ["_mouse_" if menu in {"goto", "point", "touching", "distance"} else "", None]
        reporter = self._as_reporter(value, block, node)
        self.blocks[block]["inputs"][scratch_name] = [3, reporter, shadow]

    def _apply_color(self, block, scratch_name, value, node):
        if value.kind == "lit":
            self._literal_input(block, scratch_name, "color", _normalize_color(value.data, node))
            return
        reporter = self._as_reporter(value, block, node)
        self.blocks[block]["inputs"][scratch_name] = [3, reporter, [9, "#ff0000"]]

    def _apply_number(self, block, scratch_name, slot, value, node):
        kind = "index" if slot == "index" else slot
        primitive, default = _NUMBER_TYPES[kind]
        if value.kind == "lit":
            if slot == "index" and isinstance(value.data, str) and value.data in {"last", "all", "random"}:
                self.blocks[block]["inputs"][scratch_name] = [1, [primitive, value.data]]
                return
            if not _is_number(value.data):
                self._error(node, "this input needs a number")
            self.blocks[block]["inputs"][scratch_name] = [1, [primitive, _format_number(value.data)]]
            return
        reporter = self._as_reporter(value, block, node)
        self.blocks[block]["inputs"][scratch_name] = [3, reporter, [primitive, default]]

    def _apply_text(self, block, scratch_name, value, node):
        if value.kind == "lit":
            if isinstance(value.data, bool):
                text = "true" if value.data else "false"
            else:
                text = _as_text(value.data)
            self.blocks[block]["inputs"][scratch_name] = [1, [10, text]]
            return
        reporter = self._as_reporter(value, block, node)
        self.blocks[block]["inputs"][scratch_name] = [3, reporter, [10, ""]]

    def _literal_input(self, block, scratch_name, slot, raw):
        if slot == "color":
            self.blocks[block]["inputs"][scratch_name] = [1, [9, raw]]
            return
        if slot in _NUMBER_TYPES:
            primitive, _default = _NUMBER_TYPES[slot]
            self.blocks[block]["inputs"][scratch_name] = [1, [primitive, _format_number(raw)]]
            return
        self.blocks[block]["inputs"][scratch_name] = [1, [10, str(raw)]]

    def _as_reporter(self, value, owner, node):
        if value.kind == "block":
            self.blocks[value.data]["parent"] = owner
            return value.data
        if value.kind == "var":
            frame = getattr(value.data, "frame", None)
            if frame:
                lst, arg = frame
                return self._as_reporter(self._item_value(lst, Value("arg", arg), node), owner, node)
            block = self._new_block("data_variable", parent=owner)
            self.blocks[block]["fields"]["VARIABLE"] = [value.data.name, value.data.vid]
            return block
        if value.kind == "list":
            if value.data.ident is not None or value.data.span is not None:
                joined = self._join_list(Value("lit", " "), value.data, node)
                return self._as_reporter(joined, owner, node)
            block = self._new_block("data_listcontents", parent=owner)
            self.blocks[block]["fields"]["LIST"] = [value.data.name, value.data.lid]
            return block
        if value.kind == "arg":
            opcode = "argument_reporter_boolean" if value.data.boolean else "argument_reporter_string_number"
            block = self._new_block(opcode, parent=owner)
            self.blocks[block]["fields"]["VALUE"] = [value.data.name, None]
            return block
        self._error(node, "this value cannot be used here")

    def _as_var(self, value, node):
        if value.kind == "var":
            return value.data
        if value.kind == "lit" and isinstance(value.data, str):
            found = self._find_var(value.data)
            if found is None:
                return self._bind_var(None, value.data, 0, self.is_stage, False, node)
            return found
        self._error(node, "expected a variable")

    def _as_list(self, value, node):
        if value.kind == "list":
            return value.data
        if value.kind == "lit" and isinstance(value.data, str):
            found = self._find_list(value.data)
            if found is None:
                self._error(node, f"unknown list {value.data}")
            return found
        self._error(node, "expected a list")

    def _find_var(self, name):
        if name in self.scratch_vars:
            return self.scratch_vars[name]
        for var in self.project.shared_vars.values():
            if var.name == name:
                return var
        return None

    def _find_list(self, name):
        if name in self.scratch_lists:
            return self.scratch_lists[name]
        for lst in self.project.shared_lists.values():
            if lst.name == name:
                return lst
        return None

    def _broadcast(self, name):
        for bid, existing in self.project.broadcasts.items():
            if existing == name:
                return name, bid
        bid = self.project.ids.broadcast()
        self.project.broadcasts[bid] = name
        return name, bid

    def _proc_from_call(self, call):
        if isinstance(call.func, ast.Name):
            symbol = self._lookup(call.func.id)
            if isinstance(symbol, Proc):
                return symbol
        if isinstance(call.func, ast.Attribute) and self._attr_owner(call.func.value) == "self":
            symbol = self._lookup(call.func.attr)
            if isinstance(symbol, Proc):
                return symbol
        return None

    def _emit_super(self, expr):
        name = expr.func.attr
        owner = self.super_class or self.blueprint
        if owner is None:
            self._error(expr, "super() belongs in a sprite class")
        found = _find_super_method(owner, name)
        if found is None:
            self._error(expr, f"no parent method {name}")
        parent, _fn = found
        proc = self.procedures.get(f"{parent.name}.{name}")
        if proc is None:
            self._error(expr, f"no parent method {name}")
        return self._emit_proc_call(proc, expr)

    def _emit_remote(self, sprite_name, expr):
        method = expr.func.attr
        inst = self.project.instances[sprite_name]
        fn = inst.blueprint.methods.get(method)
        if fn is not None:
            if self._function_kind(fn)[0] != "block":
                self._error(expr, f"{method} is an event script on {sprite_name}")
            params = []
            for index, (arg, default) in enumerate(_method_params(fn, inst.blueprint.path)):
                if _is_bool_arg(arg, default):
                    self._error(expr, "boolean inputs cannot be sent to another sprite")
                default_value = "" if default is None else _constant(default)
                if default is not None and default_value is _NOT_CONSTANT:
                    self._error(default, "default values must be numbers, text, or True/False")
                params.append(Arg(arg.arg, f"arg{index}", False))
                params[-1].default = NO_DEFAULT if default is None else default_value
            remote = Proc(method, params, False, method)
            remote.user_params = params
            values = self._bind_proc_args(remote, expr)
            self.project.remote_uses.add((sprite_name, method))
            return self._remote_sequence(sprite_name, method, values, expr)
        spec = BLOCKS.get(method)
        if spec is not None and spec.shape == "stack":
            for param in spec.params:
                slot = param[2]
                if slot in {"variable", "list", "boolean"} or slot.startswith("field:"):
                    self._error(expr, f"{method} cannot be called on another sprite. Call it from that sprite's own script")
            values = self._bind_params(spec, expr)
            self.project.remote_uses.add((sprite_name, method))
            return self._remote_sequence(sprite_name, method, values, expr)
        if method in _OF_PROPERTIES:
            self._error(expr, f"{method} is a value, not a command")
        self._error(expr, f"{sprite_name} has no block {method}")

    def _remote_sequence(self, sprite_name, method, values, expr):
        message = f"{sprite_name}.{method}"
        heads = []
        for index, value in enumerate(values):
            var = self._shared_arg_var(f"{message}.{index}", expr)
            block = self._new_block("data_setvariableto")
            self.blocks[block]["fields"]["VARIABLE"] = [var.name, var.vid]
            self._apply_slot(block, "VALUE", "text", value, expr)
            heads.append(block)
        broadcast = self._new_block("event_broadcastandwait")
        name, bid = self._broadcast(message)
        self.blocks[broadcast]["inputs"]["BROADCAST_INPUT"] = [1, [11, name, bid]]
        heads.append(broadcast)
        return heads

    def _shared_arg_var(self, name, node):
        found = self._find_var(name)
        if found is not None:
            return found
        return self._bind_var(None, name, "", True, False, node)

    def _compile_remote_reporter(self, sprite_name, call):
        method = call.func.attr
        inst = self.project.instances[sprite_name]
        fn = inst.blueprint.methods.get(method)
        if fn is not None and self._function_kind(fn)[1].get("returns"):
            self._error(call, f"{method} returns a value. Call it on this sprite, not on {sprite_name}")
        if method not in _OF_PROPERTIES or call.args or call.keywords:
            self._error(call, f"{method} cannot be read from {sprite_name}")
        inst = self.project.instances[sprite_name]
        label = "stage" if inst.blueprint.kind == "stage" else self._scratch_sprite_name(sprite_name)
        block = self._new_block("sensing_of")
        self.blocks[block]["fields"]["PROPERTY"] = [_OF_PROPERTIES[method], None]
        self._apply_menu(block, "OBJECT", "object", Value("lit", label), call)
        return Value("block", block)

    def _scratch_sprite_name(self, instance_name):
        target = self.project.targets_by_name.get(instance_name)
        if target is not None:
            return target.name
        return instance_name

    def _remote_instance(self, call):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
            return None
        node = call.func.value
        if not isinstance(node, ast.Name):
            return None
        if self.receiver and node.id == self.receiver:
            return None
        if node.id in self.project.instances:
            return node.id
        return None

    def _block_name(self, func):
        kitty = self._kitty_name(func)
        if kitty:
            return kitty
        if isinstance(func, ast.Attribute) and self._attr_owner(func.value) == "self":
            return func.attr
        return None

    def _attr_owner(self, node):
        if not isinstance(node, ast.Name):
            return None
        if self.receiver and node.id == self.receiver:
            return "self"
        if self.instance_name and node.id == self.instance_name and node.id in self.project.instances:
            return "self"
        if node.id in self.aliases:
            return "kitty"
        if node.id in self.project.instances:
            return node.id
        return None

    def _compile_attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in self.math_aliases:
            if node.attr == "pi":
                return Value("lit", _math.pi)
            if node.attr == "e":
                return Value("lit", _math.e)
            self._error(node, f"math.{node.attr} has no Scratch block")
        owner = self._attr_owner(node.value)
        if owner == "self":
            symbol = self._lookup(node.attr)
            if isinstance(symbol, Lit):
                return Value("lit", symbol.value, isinstance(symbol.value, bool))
            if isinstance(symbol, (Var, Lst, Map)):
                if isinstance(symbol, Var):
                    kind = "var"
                elif isinstance(symbol, Lst):
                    kind = "list"
                else:
                    kind = "dict"
                return Value(kind, symbol)
            if isinstance(symbol, Proc):
                self._error(node, f"call self.{node.attr}(...); a custom block is not a value")
            self._error(node, f"unknown attribute {node.attr}. Set it with self.{node.attr} = 0")
        if isinstance(owner, str) and owner in self.project.instances:
            self._error(node, f"{node.attr} belongs to {owner}. Use a shared variable to read another sprite's variable")
        self._error(node, "this expression has no Scratch block")

    def _assigned_python_name(self, target, stmt):
        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target, ast.Attribute) and self._attr_owner(target.value) == "self":
            return target.attr
        self._error(stmt, "assign a variable name, or self.name on a sprite")

    def _constant_empty_range(self, node):
        if not self._is_range_call(node) or node.keywords:
            return False
        start, stop, step = self._range_nodes(node)
        values = []
        for item in (start, stop, step):
            if not isinstance(item, ast.Constant) or isinstance(item.value, bool) or not isinstance(item.value, int):
                return False
            values.append(item.value)
        if values[2] == 0:
            return False
        return len(range(*values)) == 0

    def _is_range_call(self, node):
        if not isinstance(node, ast.Call):
            return False
        func = node.func
        if not isinstance(func, ast.Name) or func.id != "range":
            return False
        return self._lookup("range") is None

    def _range_nodes(self, node):
        if node.keywords:
            self._error(node, "range takes numbers")
        zero = self._mark(ast.Constant(value=0), node)
        one = self._mark(ast.Constant(value=1), node)
        if len(node.args) == 1:
            return zero, node.args[0], one
        if len(node.args) == 2:
            return node.args[0], node.args[1], one
        if len(node.args) == 3:
            step = node.args[2]
            step_value = _constant(step)
            if _is_number(step_value) and step_value == 0:
                self._error(node, "range step cannot be 0")
            return node.args[0], node.args[1], step
        self._error(node, "range takes 1, 2, or 3 numbers")

    def _iter_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute) and self._attr_owner(node.value) == "self":
            return node.attr
        return None

    def _iter_symbol(self, node):
        name = self._iter_name(node)
        if name is None:
            return None
        return self._lookup(name)

    def _pin_value(self, value, node):
        if value.kind in {"lit", "var", "arg"}:
            return [], value
        number = 1
        while f".k{number}" in self.scratch_vars:
            number += 1
        var = self._bind_var(None, f".k{number}", 0, False, False, node)
        return [self._store_value(var, value, node)], Value("var", var)

    def _compile_dict_assign(self, name, node, stmt):
        if any(key is None for key in node.keys):
            self._error(node, "a dictionary is written as {key: value}")
        symbol = self._lookup(name)
        if symbol is None:
            symbol = self._bind_dict(name, name, [], False, False, stmt, local=self.frame_arg is not None)
            if self.current_proc is not None:
                self.current_proc.owned.append(symbol)
        if not isinstance(symbol, Map):
            self._error(stmt, f"{name} is not a dictionary")
        if symbol.ident is not None:
            heads = self._materialize_reuse(symbol, stmt)
        else:
            heads = [self._delete_all_items(symbol.keys), self._delete_all_items(symbol.values)]
        for key_node, value_node in zip(node.keys, node.values):
            key = self._compile_expr(key_node)
            value = self._compile_expr(value_node)
            heads.extend(self._dict_upsert_values(symbol, key, value, stmt))
        return heads

    def _dict_get(self, mapping, key_node, node):
        key = self._compile_expr(key_node)
        return self._item_value(mapping.values, self._item_number(mapping.keys, key, node), node)

    def _dict_upsert(self, mapping, key_node, value_node, node):
        key = self._compile_expr(key_node)
        value = self._compile_expr(value_node)
        return self._dict_upsert_values(mapping, key, value, node)

    def _dict_upsert_values(self, mapping, key, value, node):
        heads, key = self._pin_value(key, node)
        more, value = self._pin_value(value, node)
        heads.extend(more)
        setup, cond = self._query_contains(mapping.keys, key, node)
        heads.extend(setup)
        found, index = self._query_index(mapping.keys, key, node)
        heads.extend(found)
        yes = self._replace_item(mapping.values, index, value, node)
        add_key = self._add_item(mapping.keys, key, node)
        add_value = self._add_item(mapping.values, value, node)
        block = self._new_block("control_if_else")
        self._apply_boolean(block, "CONDITION", cond, node)
        self._link([yes], block)
        self.blocks[block]["inputs"]["SUBSTACK"] = [2, yes]
        self._link([add_key, add_value], block)
        self.blocks[block]["inputs"]["SUBSTACK2"] = [2, add_key]
        heads.append(block)
        return heads

    def _dict_aug(self, mapping, key_node, stmt):
        key = self._compile_expr(key_node)
        heads, key = self._pin_value(key, stmt)
        current = self._item_value(mapping.values, self._item_number(mapping.keys, key, stmt), stmt)
        value = self._compile_expr(stmt.value)
        total = self._combine_numbers(stmt.op, current, value, stmt)
        heads.extend(self._dict_upsert_values(mapping, key, total, stmt))
        return heads

    def _list_contains(self, lst, item, node):
        _storage, frame = self._backing(lst)
        if frame is not None:
            setup, value = self._span_contains(lst, item, node)
            self._hoist(setup)
            return value
        return self._raw_contains(lst, item, node)

    def _item_number(self, lst, item, node):
        _storage, frame = self._backing(lst)
        if frame is not None:
            setup, value = self._span_index_of(lst, item, node)
            self._hoist(setup)
            return value
        return self._raw_item_number(lst, item, node)

    def _raw_contains(self, lst, item, node):
        block = self._new_block("data_listcontainsitem")
        self.blocks[block]["fields"]["LIST"] = [lst.name, lst.lid]
        self._apply_slot(block, "ITEM", "text", item, node)
        return Value("block", block, True)

    def _raw_item_number(self, lst, item, node):
        block = self._new_block("data_itemnumoflist")
        self.blocks[block]["fields"]["LIST"] = [lst.name, lst.lid]
        self._apply_slot(block, "ITEM", "text", item, node)
        return Value("block", block)

    def _add_item(self, lst, item, node):
        storage, frame = self._backing(lst)
        if frame is not None:
            return self._span_call(storage, "add", [frame, item], node)
        return self._raw_add(lst, item, node)

    def _raw_add(self, lst, item, node):
        block = self._new_block("data_addtolist")
        self.blocks[block]["fields"]["LIST"] = [lst.name, lst.lid]
        self._apply_slot(block, "ITEM", "text", item, node)
        return block

    def _delete_all_items(self, lst, node=None):
        storage, frame = self._backing(lst)
        if frame is not None:
            return self._span_call(storage, "clear", [frame], node or storage.span_node)
        return self._raw_clear(lst)

    def _raw_clear(self, lst):
        block = self._new_block("data_deletealloflist")
        self.blocks[block]["fields"]["LIST"] = [lst.name, lst.lid]
        return block

    def _raw_length(self, lst):
        block = self._new_block("data_lengthoflist")
        self.blocks[block]["fields"]["LIST"] = [lst.name, lst.lid]
        return Value("block", block)

    def _lookup(self, name):
        for scope in reversed(self.scope):
            if name in scope:
                return scope[name]
        return self.symbols.get(name)

    def _kitty_name(self, func):
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id in self.aliases:
            return func.attr
        if isinstance(func, ast.Name) and func.id in self.imported:
            return func.id
        return None

    def _builtin_name(self, func):
        if isinstance(func, ast.Name) and func.id in {"len", "abs", "round"} and func.id not in self.symbols:
            return func.id
        return None

    def _decl_call(self, stmt):
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.value, ast.Call):
            return stmt.value
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            return stmt.value
        return None

    def _assigned_name(self, stmt):
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            return stmt.targets[0].id
        return None

    def _literal_call(self, call):
        args = []
        for arg in call.args:
            try:
                value = _constant(arg)
            except ValueError as exc:
                self._error(arg, str(exc))
            if value is _NOT_CONSTANT:
                self._error(arg, "this value must be a number, text, list, dictionary, or True/False")
            args.append(value)
        kwargs = {}
        for keyword in call.keywords:
            if keyword.arg is None:
                self._error(keyword, "Scratch blocks do not take **kwargs")
            try:
                value = _constant(keyword.value)
            except ValueError as exc:
                self._error(keyword, str(exc))
            if value is _NOT_CONSTANT:
                self._error(keyword, "this value must be a number, text, list, dictionary, or True/False")
            kwargs[keyword.arg] = value
        return args, kwargs

    def _new_block(self, opcode, shadow=False, parent=None):
        block_id = self.project.ids.block()
        self.blocks[block_id] = {
            "opcode": opcode,
            "next": None,
            "parent": parent,
            "inputs": {},
            "fields": {},
            "shadow": shadow,
            "topLevel": False,
        }
        return block_id

    def _link(self, heads, parent):
        for index, block_id in enumerate(heads):
            block = self.blocks[block_id]
            block["parent"] = parent if index == 0 else heads[index - 1]
            block["next"] = heads[index + 1] if index + 1 < len(heads) else None
            block["topLevel"] = False

    def _place(self, block_id):
        block = self.blocks[block_id]
        block["topLevel"] = True
        block["parent"] = None
        block["x"] = 48
        block["y"] = self.y
        self.y += 120

    def _prepare_locals(self, stmts, qual, params, owner):
        list_names = {}
        for existing_name, existing in self.symbols.items():
            if isinstance(existing, Map):
                list_names[existing_name] = "dict"
            elif isinstance(existing, Lst):
                list_names[existing_name] = "list"
        payload = self._call_payload(owner, set()) if isinstance(owner, ast.FunctionDef) else None
        assigned, explicit, nonlocals = _scan_bindings(stmts, list_names, payload)
        frame = {param.name: param for param in params}
        inits = []
        for name in nonlocals:
            if name in explicit:
                self._error(owner, f"{name} is global. Remove nonlocal")
            if not any(isinstance(scope.get(name), Var) for scope in self.scope):
                self._error(owner, f"nonlocal {name} is not a variable in the outer function")
        for name in explicit:
            if name in frame:
                self._error(owner, f"{name} is a parameter")
            if name not in self.symbols:
                self._error(owner, f"global {name} needs a sprite variable. Declare {name} above the function")
        for param in params:
            carries = getattr(param, "carries", None)
            if carries == "list":
                rank = _grid_rank(owner, param.name) if isinstance(owner, (ast.FunctionDef, ast.Lambda)) else 0
                param.grid_rank = rank
                frame[param.name] = self._bind_ref_list(
                    None, f"{qual} {param.name}", [], False, False, owner, keep_local=True,
                    shape=tuple(0 for _ in range(rank)),
                )
                inits.extend(self._alias_id(frame[param.name], Value("arg", param), owner))
                if self.current_proc is not None:
                    self.current_proc.owned.append(frame[param.name])
            elif carries == "dict":
                frame[param.name] = self._bind_dict(None, f"{qual} {param.name}", [], False, False, owner, local=True)
                inits.extend(self._alias_id(frame[param.name], Value("arg", param), owner))
                if self.current_proc is not None:
                    self.current_proc.owned.append(frame[param.name])
        for name, kind in assigned.items():
            if name in nonlocals or name in explicit:
                continue
            if kind == "mixed":
                self._error(owner, f"{name} is used as both a variable and a list")
            if name in frame:
                if isinstance(frame[name], (Lst, Map)):
                    continue
                if kind != "var":
                    self._error(owner, f"{name} is a parameter")
                var = self._bind_var(None, f"{qual} {name}", 0, False, False, owner, keep_local=True)
                inits.append(self._store_value(var, Value("arg", frame[name]), owner))
                frame[name] = var
                continue
            if name.startswith("."):
                frame[name] = self._bind_var(None, name, 0, False, False, owner, keep_local=True)
                continue
            existing = self.symbols.get(name)
            if existing is not None and not isinstance(existing, Proc):
                self._error(owner, f"{name} is a sprite variable. Write global {name} inside the function before changing it")
            scratch = f"{qual} {name}"
            if kind == "var":
                frame[name] = self._bind_var(None, scratch, 0, False, False, owner, keep_local=True)
            elif kind == "dict":
                frame[name] = self._bind_dict(None, scratch, [], False, False, owner, local=True)
                if self.current_proc is not None:
                    self.current_proc.owned.append(frame[name])
            else:
                frame[name] = self._bind_list(
                    None, scratch, [], False, False, owner,
                    frozen=kind == "tuple", unique=kind == "set", keep_local=True, ref=True,
                )
                if self.current_proc is not None and frame[name].ident is not None:
                    self.current_proc.owned.append(frame[name])
        if self.frame_arg is not None:
            for param in params:
                if isinstance(frame.get(param.name), Arg):
                    var = self._bind_var(None, f"{qual} {param.name}", 0, False, False, owner, keep_local=True)
                    if param.boolean:
                        var.boolean = True
                        inits.extend(self._store_boolean(var, Value("arg", param, True), owner))
                    else:
                        inits.append(self._store_value(var, Value("arg", param), owner))
                    frame[param.name] = var
        return frame, inits

    def _lower_control(self, stmts):
        lowered, _flags = self._lower_flow(list(stmts), [], [])
        return lowered

    def _lower_flow(self, stmts, loops, tries):
        out = []
        guards = []
        for stmt in stmts:
            pieces, flags = self._lower_flow_stmt(stmt, loops, tries)
            if guards and pieces:
                pieces = [self._guard_flags(guards, pieces, stmt)]
            out.extend(pieces)
            for flag in flags:
                if flag not in guards:
                    guards.append(flag)
        return out, guards

    def _lower_flow_stmt(self, stmt, loops, tries):
        if isinstance(stmt, ast.For) and self._constant_empty_range(stmt.iter):
            return [], []
        if isinstance(stmt, ast.Break):
            if not loops:
                self._error(stmt, "break is outside a loop")
            br, co = loops[-1]
            one = self._const(1, stmt)
            return [self._assign_name(br, one, stmt), self._assign_name(co, self._const(1, stmt), stmt)], [co]
        if isinstance(stmt, ast.Continue):
            if not loops:
                self._error(stmt, "continue is outside a loop")
            _br, co = loops[-1]
            return [self._assign_name(co, self._const(1, stmt), stmt)], [co]
        if isinstance(stmt, ast.Raise):
            return self._lower_raise(stmt, loops, tries)
        if isinstance(stmt, ast.Try):
            return self._lower_try(stmt, loops, tries)
        if self._must_expand(stmt):
            return self._expand_loop(stmt, loops, tries)
        if isinstance(stmt, ast.If):
            body, bflags = self._lower_flow(stmt.body, loops, tries)
            orelse, oflags = self._lower_flow(stmt.orelse, loops, tries)
            flags = list(bflags)
            for flag in oflags:
                if flag not in flags:
                    flags.append(flag)
            return [self._make_if(stmt.test, body or [self._pass(stmt)], orelse, stmt)], flags
        if isinstance(stmt, (ast.For, ast.While)):
            body, flags = self._lower_flow(stmt.body, loops, tries)
            if isinstance(stmt, ast.While):
                node = self._mark(ast.While(test=stmt.test, body=body, orelse=[]), stmt)
            else:
                node = self._mark(ast.For(target=stmt.target, iter=stmt.iter, body=body, orelse=[]), stmt)
            return [node], flags
        if isinstance(stmt, ast.With):
            body, flags = self._lower_flow(stmt.body, loops, tries)
            return [self._mark(ast.With(items=stmt.items, body=body), stmt)], flags
        return [stmt], []

    def _must_expand(self, stmt):
        if not _loop_stmt(stmt):
            return False
        if _direct_break(stmt.body) or _direct_raise(stmt.body):
            return True
        return (
            isinstance(stmt, ast.For)
            and (self._is_enum_call(stmt.iter) or self._is_zip_call(stmt.iter) or not isinstance(stmt.target, ast.Name))
        )

    def _expand_loop(self, stmt, loops, tries):
        self._flow += 1
        number = self._flow
        br = f".br{number}"
        co = f".co{number}"
        setup, test, body, bumps = self._loop_parts(stmt, number)
        inner, _flags = self._lower_flow(body, loops + [(br, co)], tries)
        wrapped = [self._assign_name(co, self._const(0, stmt), stmt)] + inner
        for bump in bumps:
            wrapped.append(self._guard_flags([br], [bump], stmt))
        loop = self._make_while(self._and_flag_clear(br, test, stmt), wrapped or [self._pass(stmt)], stmt)
        flags = [tries[-1][0]] if tries and _direct_raise(stmt.body) else []
        pieces = [
            self._assign_name(br, self._const(0, stmt), stmt),
            self._assign_name(co, self._const(0, stmt), stmt),
            *setup,
            loop,
        ]
        return pieces, flags

    def _loop_parts(self, stmt, number):
        if isinstance(stmt, ast.For):
            return self._for_parts(stmt, number)
        if isinstance(stmt, ast.While):
            return [], stmt.test, list(stmt.body), []
        kind = _cblock_kind(stmt)
        call = stmt.items[0].context_expr
        if kind == "forever":
            return [], self._const(True, stmt), list(stmt.body), []
        if kind == "repeat_until":
            if not call.args:
                self._error(stmt, "repeat_until needs a condition")
            return [], self._negate(call.args[0], stmt), list(stmt.body), []
        if kind == "repeat":
            if not call.args:
                self._error(stmt, "repeat needs a number")
            limit = f".lim{number}"
            count = f".n{number}"
            setup = [
                self._assign_name(limit, call.args[0], stmt),
                self._assign_name(count, self._const(0, stmt), stmt),
            ]
            test = self._compare_name(count, ast.Lt(), self._name(limit, stmt), stmt)
            return setup, test, list(stmt.body), [self._aug_by(count, self._const(1, stmt), stmt)]
        self._error(stmt, "this loop cannot use break or continue")

    def _for_parts(self, stmt, number):
        if self._is_enum_call(stmt.iter):
            return self._enum_parts(stmt, number)
        if self._is_zip_call(stmt.iter):
            return self._zip_parts(stmt, number)
        if self._is_range_call(stmt.iter):
            return self._range_for_parts(stmt, number)
        return self._each_parts(stmt, number)

    def _range_for_parts(self, stmt, number):
        start, stop, step = self._range_nodes(stmt.iter)
        hold_start = f".a{number}"
        hold_stop = f".b{number}"
        hold_step = f".c{number}"
        cursor = f".n{number}"
        setup = [
            self._assign_name(hold_start, start, stmt),
            self._assign_name(hold_stop, stop, stmt),
            self._assign_name(hold_step, step, stmt),
            self._assign_name(cursor, self._name(hold_start, stmt), stmt),
        ]
        test = self._range_test(cursor, hold_stop, step, hold_step, stmt)
        body = list(stmt.body)
        if isinstance(stmt.target, ast.Name) and stmt.target.id != "_":
            body = [self._assign_name(stmt.target.id, self._name(cursor, stmt), stmt), *body]
        bump = self._aug_by(cursor, self._name(hold_step, stmt), stmt)
        return setup, test, body, [bump]

    def _each_parts(self, stmt, number):
        if not isinstance(stmt.target, ast.Name):
            self._error(stmt, "write for i, item in enumerate(items) or for a, b in zip(xs, ys)")
        index = f".ix{number}"
        limit = f".lim{number}"
        setup = [
            self._assign_name(index, self._const(0, stmt), stmt),
            self._assign_name(limit, self._len_of(stmt.iter, stmt), stmt),
        ]
        test = self._compare_name(index, ast.Lt(), self._name(limit, stmt), stmt)
        body = list(stmt.body)
        if stmt.target.id != "_":
            item = self._assign_name(stmt.target.id, self._at(stmt.iter, index, stmt), stmt)
            body = [item] + body
        return setup, test, body, [self._aug_by(index, self._const(1, stmt), stmt)]

    def _enum_parts(self, stmt, number):
        call = stmt.iter
        if call.keywords or len(call.args) not in {1, 2}:
            self._error(call, "enumerate takes a list, or a list and a start")
        names = _target_names(stmt.target)
        if len(names) != 2:
            self._error(stmt, "write for i, item in enumerate(items)")
        start = call.args[1] if len(call.args) == 2 else self._const(0, stmt)
        index = f".ix{number}"
        limit = f".lim{number}"
        origin = f".a{number}"
        setup = [
            self._assign_name(origin, start, stmt),
            self._assign_name(index, self._const(0, stmt), stmt),
            self._assign_name(limit, self._len_of(call.args[0], stmt), stmt),
        ]
        test = self._compare_name(index, ast.Lt(), self._name(limit, stmt), stmt)
        body = []
        if names[0] != "_":
            body.append(self._assign_name(names[0], self._sum_names(origin, index, stmt), stmt))
        if names[1] != "_":
            body.append(self._assign_name(names[1], self._at(call.args[0], index, stmt), stmt))
        return setup, test, body + list(stmt.body), [self._aug_by(index, self._const(1, stmt), stmt)]

    def _zip_parts(self, stmt, number):
        call = stmt.iter
        if call.keywords or len(call.args) < 2:
            self._error(call, "zip takes two or more lists")
        names = _target_names(stmt.target)
        if len(names) != len(call.args):
            self._error(stmt, "write for a, b in zip(xs, ys)")
        index = f".ix{number}"
        limit = f".lim{number}"
        setup = [
            self._assign_name(index, self._const(0, stmt), stmt),
            self._assign_name(limit, self._len_of(call.args[0], stmt), stmt),
        ]
        for other in call.args[1:]:
            shorter = self._mark(
                ast.Compare(left=self._len_of(other, stmt), ops=[ast.Lt()], comparators=[self._name(limit, stmt)]),
                stmt,
            )
            setup.append(self._make_if(shorter, [self._assign_name(limit, self._len_of(other, stmt), stmt)], [], stmt))
        test = self._compare_name(index, ast.Lt(), self._name(limit, stmt), stmt)
        body = [self._assign_name(name, self._at(seq, index, stmt), stmt) for name, seq in zip(names, call.args)]
        return setup, test, body + list(stmt.body), [self._aug_by(index, self._const(1, stmt), stmt)]

    def _lower_try(self, stmt, loops, tries):
        if len(stmt.handlers) > 1:
            self._error(stmt, "use one except")
        handler = stmt.handlers[0] if stmt.handlers else None
        if handler is not None:
            self._check_handler(handler)
        self._flow += 1
        err = f".err{self._flow}"
        msg = f".msg{self._flow}"
        body, _flags = self._lower_flow(stmt.body, loops, tries + [(err, msg)])
        handler_body = []
        if handler is not None:
            handler_body, _flags = self._lower_flow(handler.body, loops, tries)
            if handler.name:
                handler_body = [self._assign_name(handler.name, self._name(msg, handler), handler)] + handler_body
        else_body, _flags = self._lower_flow(stmt.orelse, loops, tries)
        final_body, _flags = self._lower_flow(stmt.finalbody, loops, tries)
        pieces = [
            self._assign_name(err, self._const(0, stmt), stmt),
            self._assign_name(msg, self._const("", stmt), stmt),
            *body,
        ]
        if handler is not None or else_body:
            pieces.append(self._make_if(
                self._compare_name(err, ast.Eq(), self._const(1, stmt), stmt),
                handler_body or [self._pass(stmt)],
                else_body,
                stmt,
            ))
        pieces.extend(final_body)
        flags = []
        if tries and (
            _direct_raise(stmt.finalbody)
            or _direct_raise(stmt.orelse)
            or (handler is not None and _direct_raise(handler.body))
        ):
            flags.append(tries[-1][0])
        return pieces, flags

    def _check_handler(self, handler):
        if handler.type is None:
            return
        if isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
            return
        self._error(handler, "except catches Exception. Scratch does not raise its own errors")

    def _lower_raise(self, stmt, loops, tries):
        if not tries:
            self._error(stmt, "raise belongs inside try")
        err, msg = tries[-1]
        pieces = [
            self._assign_name(err, self._const(1, stmt), stmt),
            self._assign_name(msg, self._raise_message(stmt), stmt),
        ]
        flags = [err]
        for br, co in loops:
            pieces.append(self._assign_name(br, self._const(1, stmt), stmt))
            pieces.append(self._assign_name(co, self._const(1, stmt), stmt))
            if co not in flags:
                flags.append(co)
        return pieces, flags

    def _raise_message(self, stmt):
        exc = stmt.exc
        if exc is None:
            return self._const("", stmt)
        if isinstance(exc, ast.Call):
            if exc.args:
                return exc.args[0]
            return self._const("", stmt)
        return exc

    def _guard_flags(self, flags, body, source):
        zero = self._const(0, source)
        tests = [self._compare_name(flag, ast.Eq(), zero, source) for flag in flags]
        test = tests[0] if len(tests) == 1 else self._mark(ast.BoolOp(op=ast.And(), values=tests), source)
        return self._make_if(test, body, [], source)

    def _and_flag_clear(self, flag, test, source):
        clear = self._compare_name(flag, ast.Eq(), self._const(0, source), source)
        if isinstance(test, ast.Constant) and test.value is True:
            return clear
        return self._mark(ast.BoolOp(op=ast.And(), values=[clear, test]), source)

    def _const(self, value, source):
        return self._mark(ast.Constant(value=value), source)

    def _len_of(self, value, source):
        call = ast.Call(func=self._mark(ast.Name(id="len", ctx=ast.Load()), source), args=[value], keywords=[])
        return self._mark(call, source)

    def _at(self, value, index, source):
        node = ast.Subscript(value=value, slice=self._name(index, source), ctx=ast.Load())
        return self._mark(node, source)

    def _is_enum_call(self, node):
        return _plain_call(node, "enumerate") and self._lookup("enumerate") is None

    def _is_zip_call(self, node):
        return _plain_call(node, "zip") and self._lookup("zip") is None

    def _hidden_var(self, node, initial=0):
        number = 1
        while f".v{number}" in self.scratch_vars:
            number += 1
        return self._bind_var(None, f".v{number}", initial, False, False, node, keep_local=True)

    def _hidden_list(self, node, frozen=False, unique=False):
        number = 1
        while f".id .c{number}" in self.scratch_vars:
            number += 1
        lst = self._bind_ref_list(None, f".c{number}", [], False, False, node, frozen=frozen, unique=unique, keep_local=True)
        lst.ephemeral = True
        if self.ephemeral_stack:
            self.ephemeral_stack[-1].append(lst)
        self._hoist(self._materialize_reuse(lst, node))
        return lst

    def _hoist(self, heads):
        if heads:
            if not self.hoist_stack:
                raise CompileError("use this inside a script")
            self.hoist_stack[-1].extend(heads)

    def _if_else(self, cond, yes, no, node):
        block = self._new_block("control_if_else" if no else "control_if")
        self._apply_boolean(block, "CONDITION", cond, node)
        self._link(yes, block)
        if yes:
            self.blocks[block]["inputs"]["SUBSTACK"] = [2, yes[0]]
        if no:
            self._link(no, block)
            if no:
                self.blocks[block]["inputs"]["SUBSTACK2"] = [2, no[0]]
        return block

    def _repeat_until_block(self, condition, body, node):
        block = self._new_block("control_repeat_until")
        self._apply_boolean(block, "CONDITION", condition, node)
        self._link(body, block)
        if body:
            self.blocks[block]["inputs"]["SUBSTACK"] = [2, body[0]]
        return block

    def _length_of(self, lst, node=None):
        storage, frame = self._backing(lst)
        if frame is not None:
            _starts, lengths, _owner = storage.span
            return self._raw_item(lengths, frame, node or storage.span_node)
        return self._raw_length(lst)

    def _text_length(self, value, node):
        block = self._new_block("operator_length")
        self._apply_slot(block, "STRING", "text", value, node)
        return Value("block", block)

    def _join_values(self, left, right, node):
        joined = self._binary("operator_join", "text", "STRING1", left, "STRING2", right, False, node)
        joined.text = True
        return joined

    def _letter_at(self, text, index, node):
        block = self._new_block("operator_letter_of")
        self._apply_slot(block, "LETTER", "whole", index, node)
        self._apply_slot(block, "STRING", "text", text, node)
        return Value("block", block)

    def _python_to_scratch_index(self, value, length, node, allow_menu=False):
        if value.kind == "lit" and isinstance(value.data, bool):
            self._error(node, "a list index is a whole number")
        if value.kind == "lit" and isinstance(value.data, str):
            if allow_menu and value.data in {"last", "all", "random"}:
                return value
            self._error(node, "a list index is a whole number")
        if value.kind == "lit" and _is_number(value.data):
            if value.data != int(value.data):
                self._error(node, "a list index is a whole number")
            number = int(value.data)
            if number >= 0:
                return Value("lit", number + 1)
            if isinstance(length, int):
                return Value("lit", length + number + 1)
            if number == -1:
                return length
            return self._binary("operator_add", "number", "NUM1", length, "NUM2", Value("lit", number + 1), False, node)
        return self._dynamic_index(value, length, node)

    def _dynamic_index(self, value, length, node):
        if not self.hoist_stack:
            self._error(node, "use this index inside a script")
        heads, pinned = self._pin_value(value, node)
        length_value = Value("lit", length) if isinstance(length, int) else length
        temp = self._hidden_var(node)
        negative = self._binary("operator_lt", "text", "OPERAND1", pinned, "OPERAND2", Value("lit", 0), True, node)
        plus = self._binary("operator_add", "number", "NUM1", pinned, "NUM2", Value("lit", 1), False, node)
        shifted = self._binary("operator_add", "number", "NUM1", length_value, "NUM2", pinned, False, node)
        wrapped = self._binary("operator_add", "number", "NUM1", shifted, "NUM2", Value("lit", 1), False, node)
        block = self._if_else(negative, [self._store_value(temp, wrapped, node)], [self._store_value(temp, plus, node)], node)
        self._hoist(heads + [block])
        return Value("var", temp)

    def _shift_index_args(self, spec, values, call):
        list_symbol = None
        for param, value in zip(spec.params, values):
            if len(param) > 2 and param[2] == "list" and value.kind == "list":
                list_symbol = value.data
        if list_symbol is None:
            return values
        if list_symbol.frozen and spec.opcode in {
            "data_addtolist", "data_deleteoflist", "data_deletealloflist", "data_insertatlist", "data_replaceitemoflist",
        }:
            self._error(call, "a tuple cannot be changed")
        shifted = []
        length = None
        for param, value in zip(spec.params, values):
            if len(param) > 2 and param[2] == "index":
                if _index_needs_length(value):
                    if length is None:
                        length = self._length_of(list_symbol)
                    value = self._python_to_scratch_index(value, length, call, allow_menu=True)
                else:
                    value = self._python_to_scratch_index(value, 0, call, allow_menu=True)
            shifted.append(value)
        return shifted

    def _text_index(self, text, expr, node):
        value = self._compile_expr(expr)
        length = self._text_length(text, node) if _index_needs_length(value) else 0
        return self._letter_at(text, self._python_to_scratch_index(value, length, node), node)

    def _compile_text_chain(self, node):
        if isinstance(node.value, ast.Subscript) and not isinstance(node.value.slice, ast.Slice):
            inner = self._compile_subscript(node.value)
        else:
            inner = self._compile_expr(node.value)
        return self._text_index(inner, node.slice, node)

    def _compile_get_slice(self, node):
        base = self._compile_expr(node.value)
        if base.kind == "dict":
            self._error(node, "slice a list or text")
        if base.kind == "list":
            if base.data.shape:
                self._error(node, "slice a one-dimensional list")
            dest = self._hidden_list(node, frozen=base.data.frozen)
            heads = [self._delete_all_items(dest)]
            heads.extend(self._slice_list(dest, base.data, node.slice, node))
            self._hoist(heads)
            return Value("list", dest)
        out = self._hidden_var(node, "")
        heads = [self._store_value(out, Value("lit", ""), node)]
        heads.extend(self._slice_text(out, base, node.slice, node))
        self._hoist(heads)
        return Value("var", out)

    def _slice_list(self, dest, src, sl, node):
        def emit(cursor):
            scratch = self._binary("operator_add", "number", "NUM1", Value("var", cursor), "NUM2", Value("lit", 1), False, node)
            return [self._add_item(dest, self._item_value(src, scratch, node), node)]
        return self._slice_loop(self._length_of(src), sl, node, emit)

    def _slice_text(self, dest, text, sl, node):
        def emit(cursor):
            scratch = self._binary("operator_add", "number", "NUM1", Value("var", cursor), "NUM2", Value("lit", 1), False, node)
            letter = self._letter_at(text, scratch, node)
            return [self._store_value(dest, self._join_values(Value("var", dest), letter, node), node)]
        return self._slice_loop(self._text_length(text, node), sl, node, emit)

    def _slice_step(self, sl, node):
        if sl.step is None:
            return 1
        folded = _constant(sl.step)
        if isinstance(folded, bool) or not isinstance(folded, int) or folded == 0:
            self._error(sl, "a slice step must be a whole number other than 0")
        return folded

    def _slice_loop(self, length, sl, node, emit):
        heads, length = self._pin_value(length, node)
        step = self._slice_step(sl, node)
        if step < 0:
            start_default = self._binary("operator_subtract", "number", "NUM1", length, "NUM2", Value("lit", 1), False, node)
            stop_default = Value("lit", -1)
        else:
            start_default = Value("lit", 0)
            stop_default = length
        bound_heads, start = self._slice_bound(sl.lower, length, start_default, node)
        heads.extend(bound_heads)
        bound_heads, stop = self._slice_bound(sl.upper, length, stop_default, node)
        heads.extend(bound_heads)
        if step > 0:
            bound_heads, start = self._extreme(start, Value("lit", 0), node, high=True)
            heads.extend(bound_heads)
            bound_heads, stop = self._extreme(stop, length, node, high=False)
            heads.extend(bound_heads)
        more, start = self._pin_value(start, node)
        heads.extend(more)
        more, stop = self._pin_value(stop, node)
        heads.extend(more)
        cursor = self._hidden_var(node)
        heads.append(self._store_value(cursor, start, node))
        inside = self._in_range(cursor, length, node)
        body = [self._if_else(inside, emit(cursor), [], node)]
        body.append(self._change_var(cursor, Value("lit", step), node))
        if step > 0:
            done = self._not_value(self._binary("operator_lt", "text", "OPERAND1", Value("var", cursor), "OPERAND2", stop, True, node), node)
        else:
            done = self._not_value(self._binary("operator_gt", "text", "OPERAND1", Value("var", cursor), "OPERAND2", stop, True, node), node)
        heads.append(self._repeat_until_block(done, body, node))
        return heads

    def _slice_bound(self, expr, length, default, node):
        if expr is None:
            return [], default
        value = self._compile_expr(expr)
        if value.kind == "lit" and _is_number(value.data) and value.data == int(value.data) and int(value.data) >= 0:
            return [], Value("lit", int(value.data))
        return self._wrap_negative(value, length, node)

    def _wrap_negative(self, value, length, node):
        heads, pinned = self._pin_value(value, node)
        temp = self._hidden_var(node)
        negative = self._binary("operator_lt", "text", "OPERAND1", pinned, "OPERAND2", Value("lit", 0), True, node)
        wrapped = self._binary("operator_add", "number", "NUM1", length, "NUM2", pinned, False, node)
        block = self._if_else(negative, [self._store_value(temp, wrapped, node)], [self._store_value(temp, pinned, node)], node)
        return heads + [block], Value("var", temp)

    def _extreme(self, left, right, node, high):
        heads, left = self._pin_value(left, node)
        more, right = self._pin_value(right, node)
        heads.extend(more)
        temp = self._hidden_var(node)
        op = "operator_gt" if high else "operator_lt"
        cond = self._binary(op, "text", "OPERAND1", left, "OPERAND2", right, True, node)
        block = self._if_else(cond, [self._store_value(temp, left, node)], [self._store_value(temp, right, node)], node)
        return heads + [block], Value("var", temp)

    def _in_range(self, cursor, length, node):
        not_low = self._not_value(
            self._binary("operator_lt", "text", "OPERAND1", Value("var", cursor), "OPERAND2", Value("lit", 0), True, node),
            node,
        )
        below = self._binary("operator_lt", "text", "OPERAND1", Value("var", cursor), "OPERAND2", length, True, node)
        return self._boolean_pair("operator_and", not_low, below, node)

    def _compile_unpack(self, target, value, stmt):
        names = _target_names(target)
        if not names:
            self._error(stmt, "unpack into names")
        if isinstance(value, ast.Call):
            proc = self._proc_from_call(value)
            if proc is not None and proc.returns and len(proc.results) > 1:
                if len(proc.results) != len(names):
                    self._error(stmt, f"unpack {len(proc.results)} values")
                outputs = self._emit_returning_call(proc, value)
                heads = []
                for name, var in zip(names, outputs):
                    heads.extend(self._assign_existing(name, Value("var", var), stmt))
                return heads
        if isinstance(value, (ast.Tuple, ast.List)):
            if len(value.elts) != len(names):
                self._error(stmt, "unpack the same number of names and values")
            heads = []
            temps = []
            for elt in value.elts:
                if isinstance(elt, ast.Starred):
                    self._error(elt, "unpack into names")
                item = self._compile_expr(elt)
                temp = self._hidden_var(stmt)
                heads.append(self._store_value(temp, item, stmt))
                temps.append(temp)
            for name, temp in zip(names, temps):
                heads.extend(self._assign_existing(name, Value("var", temp), stmt))
            return heads
        seq = self._compile_expr(value)
        if seq.kind != "list":
            self._error(value, "unpack a list or a tuple")
        heads = []
        for index, name in enumerate(names):
            item = self._item_value(seq.data, Value("lit", index + 1), stmt)
            heads.extend(self._assign_existing(name, item, stmt))
        return heads

    def _assign_existing(self, name, value, stmt):
        symbol = self._lookup(name)
        if symbol is None:
            symbol = self._bind_var(name, name, 0, False, False, stmt)
        if not isinstance(symbol, Var):
            self._error(stmt, f"{name} is not a variable")
        return [self._store_value(symbol, value, stmt)]

    def _store_list(self, name, value, stmt):
        if value.kind != "list":
            self._error(stmt, "assign a list")
        symbol = self._lookup(name)
        if symbol is None:
            if value.data.ident is not None:
                symbol = self._bind_ref_list(
                    name, name, [], False, False, stmt,
                    frozen=value.data.frozen, unique=value.data.unique, keep_local=self.frame_arg is not None,
                    shape=value.data.shape,
                )
                if self.current_proc is not None:
                    self.current_proc.owned.append(symbol)
            else:
                symbol = self._bind_list(name, name, [], False, False, stmt, frozen=value.data.frozen, unique=value.data.unique)
        if not isinstance(symbol, Lst):
            self._error(stmt, f"{name} is a variable, not a list")
        if symbol.frozen and not value.data.frozen:
            self._error(stmt, f"{name} is a tuple. Assign another tuple")
        if symbol.unique and not value.data.unique:
            self._error(stmt, f"{name} is a set. Assign another set")
        if value.data is symbol:
            return []
        if symbol.ident is not None and value.data.ident is not None:
            self._adopt_shape(symbol, value.data, stmt)
            return self._alias_ref(symbol, value.data, stmt)
        return [self._delete_all_items(symbol, stmt), *self._copy_list(value.data, symbol, stmt)]

    def _store_dict(self, name, value, stmt):
        if value.kind != "dict":
            self._error(stmt, "assign a dictionary")
        symbol = self._lookup(name)
        if symbol is None:
            symbol = self._bind_dict(name, name, [], False, False, stmt, local=self.frame_arg is not None)
            if self.current_proc is not None:
                self.current_proc.owned.append(symbol)
        if not isinstance(symbol, Map):
            self._error(stmt, f"{name} is not a dictionary")
        if value.data is symbol:
            return []
        if symbol.ident is not None and value.data.ident is not None:
            return self._alias_ref(symbol, value.data, stmt)
        return [
            self._delete_all_items(symbol.keys, stmt),
            self._delete_all_items(symbol.values, stmt),
            *self._copy_list(value.data.keys, symbol.keys, stmt),
            *self._copy_list(value.data.values, symbol.values, stmt),
        ]

    def _emit_list_result(self, proc, call):
        values = self._bind_proc_args(proc, call)
        plain = self._fresh_id(call)
        self._make_ref_stub(proc, plain, proc.result_list, "list", call)
        self.hoist_stack[-1].append(self._call_block(self._list_stub, values, call))
        view = self._hold_id(plain, "list", call)
        if proc.result_list is not None and proc.result_list.shape:
            view.shape = proc.result_list.shape
        return view

    def _emit_dict_result(self, proc, call):
        values = self._bind_proc_args(proc, call)
        plain = self._fresh_id(call)
        self._make_ref_stub(proc, plain, proc.result_dict, "dict", call)
        self.hoist_stack[-1].append(self._call_block(self._list_stub, values, call))
        return self._hold_id(plain, "dict", call)

    def _fresh_id(self, node):
        self._stub_n += 1
        held = self.frame_arg
        self.frame_arg = None
        try:
            return self._bind_var(None, f".r{self._stub_n}", 0, False, False, node, keep_local=True)
        finally:
            self.frame_arg = held

    def _hold_id(self, plain, kind, node):
        held = self.frame_arg
        if held is None:
            ident = plain
        else:
            ident = self._hidden_var(node)
            self.hoist_stack[-1].append(self._store_value(ident, Value("var", plain), node))
            self.hoist_stack[-1].append(self._store_value(plain, Value("lit", 0), node))
        if kind == "list":
            view = self._ref_view(f".hold {ident.name}", self.heaps["list"]["columns"][0], ident, "list")
            view.ephemeral = True
            if self.ephemeral_stack:
                self.ephemeral_stack[-1].append(view)
            return view
        heap = self.heaps["dict"]
        keys = self._ref_view(f".hold {ident.name} keys", heap["columns"][0], ident, "dict")
        values = self._ref_view(f".hold {ident.name} values", heap["columns"][1], ident, "dict")
        mapping = Map(keys.name, keys, values)
        mapping.ident = ident
        mapping.ref_kind = "dict"
        mapping.ephemeral = True
        if self.ephemeral_stack:
            self.ephemeral_stack[-1].append(mapping)
        return mapping

    def _make_ref_stub(self, proc, plain, source, kind, node):
        self._stub_n += 1
        number = self._stub_n
        params = []
        for index, param in enumerate(proc.params):
            copied = Arg(param.name, f"s{number}_{index}", param.boolean)
            copied.default = param.default
            params.append(copied)
        label = f".use {number}"
        stub = Proc(label, params, True, _signature(label, params))
        saved = self.frame_arg
        self.frame_arg = None
        try:
            heap = self.heaps[kind]
            call = self._call_block(proc, [Value("arg", param) for param in params], node)
            body = [
                self._call_block(heap["ops"]["decref"], [Value("var", plain)], node),
                self._store_value(plain, Value("lit", 0), node),
                call,
                self._call_block(heap["ops"]["incref"], [Value("var", source.ident)], node),
                self._store_value(plain, Value("var", source.ident), node),
            ]
            self._define_stack(stub, body, node)
        finally:
            self.frame_arg = saved
        self._list_stub = stub

    def _assign_sequence(self, name, value, stmt):
        symbol = self._lookup(name)
        kind = _expr_sequence_kind(value)
        if kind == "slice":
            kind = "list"
        if symbol is None:
            symbol = self._bind_list(
                name, name, [], False, False, stmt,
                frozen=kind == "tuple", unique=kind == "set", ref=True,
            )
            if self.current_proc is not None and symbol.ident is not None:
                self.current_proc.owned.append(symbol)
        if isinstance(symbol, Map):
            self._error(stmt, f"{name} is a dictionary")
        if not isinstance(symbol, Lst):
            self._error(stmt, f"{name} is a variable, not a list")
        if symbol.frozen and kind not in {None, "tuple", "slice"}:
            self._error(stmt, f"{name} is a tuple. Assign another tuple")
        if symbol.unique and kind not in {None, "set"}:
            self._error(stmt, f"{name} is a set. Assign another set")
        if symbol.ident is not None:
            return [*self._materialize_reuse(symbol, stmt), *self._write_items(symbol, value, stmt)]
        return [self._delete_all_items(symbol), *self._write_items(symbol, value, stmt)]

    def _parse_grid(self, node):
        if not isinstance(node, (ast.List, ast.Tuple)):
            return None
        if not node.elts or not isinstance(node.elts[0], (ast.List, ast.Tuple)):
            return None
        try:
            shape = _ast_grid_shape(node)
            atoms = _ast_grid_atoms(node, 0, shape)
        except ValueError as exc:
            self._error(node, str(exc))
        return shape, atoms

    def _write_items(self, lst, node, owner):
        grid = self._parse_grid(node)
        if grid is not None:
            shape, atoms = grid
            if lst.shape and len(lst.shape) != len(shape):
                self._error(node, self._dim_message(lst))
            lst.shape = shape
            heads = self._write_shape(lst, shape, owner)
            for atom in atoms:
                heads.append(self._add_item(lst, self._compile_expr(atom), owner))
            return heads
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            heads = []
            for elt in node.elts:
                if isinstance(elt, ast.Starred):
                    self._error(elt, "write the items out, or add a list with +=")
                if isinstance(elt, (ast.List, ast.Tuple)):
                    self._error(elt, "a list cannot mix single items and nested lists")
                item = self._compile_expr(elt)
                if lst.unique:
                    heads.extend(self._add_unique(lst, item, owner))
                else:
                    heads.append(self._add_item(lst, item, owner))
            return heads
        if isinstance(node, (ast.ListComp, ast.SetComp)):
            return self._comp_into(lst, node)
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            base = self._compile_expr(node.value)
            if base.kind != "list":
                self._error(node, "assign a list slice to a list")
            if base.data.shape:
                self._error(node, "slice a one-dimensional list")
            return self._slice_list(lst, base.data, node.slice, node)
        if isinstance(node, ast.Call) and _plain_call(node, "set") and self._lookup("set") is None:
            if node.keywords or len(node.args) > 1:
                self._error(node, "set() takes no values, or one list")
            if not node.args:
                return []
            return self._write_items(lst, node.args[0], owner)
        if isinstance(node, ast.Call) and _plain_call(node, "list") and self._lookup("list") is None:
            if node.keywords or len(node.args) != 1:
                self._error(node, "list() takes one list")
            return self._write_items(lst, node.args[0], owner)
        if isinstance(node, ast.Call) and _plain_call(node, "tuple") and self._lookup("tuple") is None:
            if node.keywords or len(node.args) != 1:
                self._error(node, "tuple() takes one list")
            return self._write_items(lst, node.args[0], owner)
        value = self._compile_expr(node)
        if value.kind == "list":
            if value.data is lst:
                self._error(node, "read the list into a new one before replacing it")
            return self._copy_list(value.data, lst, node)
        self._error(node, "assign a list, a tuple, or a set")

    def _copy_list(self, src, dest, node):
        if dest.unique:
            return self._walk_list(
                src,
                lambda index: self._add_unique(dest, self._item_value(src, Value("var", index), node), node),
                node,
            )
        return self._walk_list(
            src,
            lambda index: [self._add_item(dest, self._item_value(src, Value("var", index), node), node)],
            node,
        )

    def _sequence_value(self, node):
        if isinstance(node, (ast.ListComp, ast.SetComp)):
            dest = self._hidden_list(node, unique=isinstance(node, ast.SetComp))
            heads = [self._delete_all_items(dest), *self._comp_into(dest, node)]
            self._hoist(heads)
            return Value("list", dest)
        dest = self._hidden_list(node, frozen=isinstance(node, ast.Tuple), unique=isinstance(node, ast.Set))
        heads = [self._delete_all_items(dest), *self._write_items(dest, node, node)]
        self._hoist(heads)
        return Value("list", dest)

    def _comp_into(self, dest, node):
        if len(node.generators) != 1:
            self._error(node, "a comprehension has one for")
        gen = node.generators[0]
        if getattr(gen, "is_async", False):
            self._error(node, "a comprehension has one for")
        frame = {".": dest}
        for name in _target_names(gen.target):
            frame[name] = self._hidden_var(node)
        self.scope.append(frame)
        try:
            attr = "add" if dest.unique else "append"
            call = ast.Call(
                func=self._mark(ast.Attribute(value=self._name(".", node), attr=attr, ctx=ast.Load()), node),
                args=[node.elt],
                keywords=[],
            )
            body = [self._mark(ast.Expr(value=self._mark(call, node)), node)]
            test = None
            for cond in gen.ifs:
                test = cond if test is None else self._mark(ast.BoolOp(op=ast.And(), values=[test, cond]), node)
            if test is not None:
                body = [self._make_if(test, body, [], node)]
            loop = self._mark(ast.For(target=gen.target, iter=gen.iter, body=body, orelse=[]), node)
            if self._must_expand(loop):
                pieces, _flags = self._expand_loop(loop, [], [])
            else:
                pieces = [loop]
            heads = []
            for piece in pieces:
                heads.extend(self._compile_stmt(piece))
            return heads
        finally:
            self.scope.pop()

    def _set_statement(self, lst, name, call):
        if name == "add":
            self._take_args(call, 1, "add takes one item")
            return self._add_unique(lst, self._compile_expr(call.args[0]), call)
        if name in {"remove", "discard"}:
            self._take_args(call, 1, f"{name} takes one item")
            return self._discard_item(lst, self._compile_expr(call.args[0]), call)
        if name == "clear":
            self._take_args(call, 0, "clear takes no values")
            return [self._delete_all_items(lst)]
        if name == "pop":
            if call.args:
                self._error(call, "pop takes no index on a set")
            return [self._delete_at(lst, Value("lit", "last"), call)]
        self._error(call, "a set has add, discard, remove, pop, and clear")

    def _add_unique(self, lst, item, node):
        heads, item = self._pin_value(item, node)
        setup, flag = self._query_contains(lst, item, node)
        heads.extend(setup)
        cond = self._not_value(flag, node)
        added = self._add_item(lst, item, node)
        heads.append(self._if_else(cond, [added], [], node))
        return heads

    def _discard_item(self, lst, item, node):
        heads, item = self._pin_value(item, node)
        setup, flag = self._query_contains(lst, item, node)
        heads.extend(setup)
        found, index = self._query_index(lst, item, node)
        heads.extend(found)
        heads.append(self._if_else(flag, [self._delete_at(lst, index, node)], [], node))
        return heads

    def _query_contains(self, lst, item, node):
        _storage, frame = self._backing(lst)
        if frame is not None:
            return self._span_contains(lst, item, node)
        return [], self._raw_contains(lst, item, node)

    def _query_index(self, lst, item, node):
        _storage, frame = self._backing(lst)
        if frame is not None:
            return self._span_index_of(lst, item, node)
        return [], self._raw_item_number(lst, item, node)

    def _compile_joined(self, node):
        if not node.values:
            return Value("lit", "")
        parts = []
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                if value.format_spec is not None:
                    self._error(value, "f-string format specs are not supported")
                parts.append(self._compile_expr(value.value))
            elif isinstance(value, ast.Constant):
                parts.append(Value("lit", "" if value.value is None else str(value.value)))
            else:
                parts.append(self._compile_expr(value))
        current = parts[0]
        for part in parts[1:]:
            current = self._join_values(current, part, node)
        return current

    def _text_method_value(self, call):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
            return None
        if call.func.attr not in _TEXT_METHODS:
            return None
        symbol = self._receiver_symbol(call.func.value)
        if isinstance(symbol, (Lst, Map)):
            return None
        return self._compile_text_method(call)

    def _compile_text_method(self, call):
        self._no_keywords(call)
        name = call.func.attr
        text = self._compile_expr(call.func.value)
        if name in {"upper", "lower"}:
            self._take_args(call, 0, f"{name} takes no values")
            pairs = _UPPER if name == "upper" else _LOWER
            return self._map_case(text, pairs, call)
        if name in {"strip", "lstrip", "rstrip"}:
            self._take_args(call, 0, f"{name} takes no values")
            return self._strip_text(text, name, call)
        if name == "replace":
            self._take_args(call, 2, "replace takes the old text and the new text")
            return self._replace_text(text, self._compile_expr(call.args[0]), self._compile_expr(call.args[1]), call)
        if name == "split":
            if len(call.args) > 1:
                self._error(call, "split takes no values, or one separator")
            sep = None if not call.args else self._compile_expr(call.args[0])
            return self._split_text(text, sep, call)
        if name == "join":
            self._take_args(call, 1, "join takes a list")
            seq = self._compile_expr(call.args[0])
            if seq.kind != "list":
                self._error(call, "join takes a list")
            return self._join_list(text, seq.data, call)
        if name in {"startswith", "endswith"}:
            self._take_args(call, 1, f"{name} takes the text to check")
            return self._edge_text(text, self._compile_expr(call.args[0]), call, name == "endswith")
        if name == "find":
            self._take_args(call, 1, "find takes the text to find")
            return self._find_text(text, self._compile_expr(call.args[0]), call)
        if name == "count":
            self._take_args(call, 1, "count takes the text to count")
            return self._count_text(text, self._compile_expr(call.args[0]), call)
        if name in {"isdigit", "isalpha"}:
            self._take_args(call, 0, f"{name} takes no values")
            return self._class_text(text, name, call)
        self._error(call, "this string method has no Scratch block")

    def _map_case(self, text, pairs, node):
        if not self.hoist_stack:
            self._error(node, "use this inside a script")
        out = self._hidden_var(node, "")
        index = self._hidden_var(node, 1)
        letter = self._hidden_var(node, "")
        length = self._text_length(text, node)
        body = [self._store_value(letter, self._letter_at(text, Value("var", index), node), node)]
        body.extend(self._replace_chars(letter, pairs, node))
        body.append(self._store_value(out, self._join_values(Value("var", out), Value("var", letter), node), node))
        body.append(self._change_var(index, Value("lit", 1), node))
        self._hoist([
            self._store_value(out, Value("lit", ""), node),
            self._store_value(index, Value("lit", 1), node),
            self._repeat_block(length, body, node),
        ])
        return Value("var", out)

    def _replace_chars(self, var, pairs, node):
        blocks = []
        current = Value("var", var)
        for src, dst in pairs:
            cond = self._binary("operator_equals", "text", "OPERAND1", current, "OPERAND2", Value("lit", src), True, node)
            blocks.append(self._if_else(cond, [self._store_value(var, Value("lit", dst), node)], [], node))
        return blocks

    def _strip_text(self, text, name, node):
        if not self.hoist_stack:
            self._error(node, "use this inside a script")
        if name == "strip":
            left = self._strip_text(text, "lstrip", node)
            return self._strip_text(left, "rstrip", node)
        out = self._hidden_var(node, "")
        index = self._hidden_var(node)
        length = self._text_length(text, node)
        heads, length = self._pin_value(length, node)
        if name == "lstrip":
            heads.extend(self._skip_spaces(text, index, length, node, reverse=False))
            body = [
                self._store_value(out, self._join_values(Value("var", out), self._letter_at(text, Value("var", index), node), node), node),
                self._change_var(index, Value("lit", 1), node),
            ]
            done = self._not_value(self._binary("operator_lt", "text", "OPERAND1", Value("var", index), "OPERAND2", self._binary("operator_add", "number", "NUM1", length, "NUM2", Value("lit", 1), False, node), True, node), node)
            heads.append(self._store_value(out, Value("lit", ""), node))
            heads.append(self._repeat_until_block(done, body, node))
        else:
            heads.append(self._store_value(index, length, node))
            space = self._binary("operator_equals", "text", "OPERAND1", self._letter_at(text, Value("var", index), node), "OPERAND2", Value("lit", " "), True, node)
            positive = self._binary("operator_gt", "text", "OPERAND1", Value("var", index), "OPERAND2", Value("lit", 0), True, node)
            cond = self._not_value(self._boolean_pair("operator_and", space, positive, node), node)
            heads.append(self._repeat_until_block(cond, [self._change_var(index, Value("lit", -1), node)], node))
            cursor = self._hidden_var(node, 1)
            heads.append(self._store_value(out, Value("lit", ""), node))
            heads.append(self._store_value(cursor, Value("lit", 1), node))
            copy = [
                self._store_value(out, self._join_values(Value("var", out), self._letter_at(text, Value("var", cursor), node), node), node),
                self._change_var(cursor, Value("lit", 1), node),
            ]
            done = self._not_value(self._binary("operator_lt", "text", "OPERAND1", Value("var", cursor), "OPERAND2", self._binary("operator_add", "number", "NUM1", Value("var", index), "NUM2", Value("lit", 1), False, node), True, node), node)
            heads.append(self._repeat_until_block(done, copy, node))
        self._hoist(heads)
        return Value("var", out)

    def _skip_spaces(self, text, index, length, node, reverse):
        heads = [self._store_value(index, Value("lit", 1), node)]
        space = self._binary("operator_equals", "text", "OPERAND1", self._letter_at(text, Value("var", index), node), "OPERAND2", Value("lit", " "), True, node)
        pending = self._binary("operator_lt", "text", "OPERAND1", Value("var", index), "OPERAND2", self._binary("operator_add", "number", "NUM1", length, "NUM2", Value("lit", 1), False, node), True, node)
        cond = self._not_value(self._boolean_pair("operator_and", space, pending, node), node)
        heads.append(self._repeat_until_block(cond, [self._change_var(index, Value("lit", 1), node)], node))
        return heads

    def _replace_text(self, text, old, new, node):
        if not self.hoist_stack:
            self._error(node, "use this inside a script")
        out = self._hidden_var(node, "")
        index = self._hidden_var(node, 1)
        heads, old = self._pin_value(old, node)
        more, new = self._pin_value(new, node)
        heads.extend(more)
        length = self._text_length(text, node)
        size = self._text_length(old, node)
        heads2, length = self._pin_value(length, node)
        heads.extend(heads2)
        heads3, size = self._pin_value(size, node)
        heads.extend(heads3)
        limit = self._binary("operator_add", "number", "NUM1", length, "NUM2", Value("lit", 1), False, node)
        matched, match_heads = self._matches(text, old, index, size, node)
        yes = [
            self._store_value(out, self._join_values(Value("var", out), new, node), node),
            self._change_var(index, size, node),
        ]
        no = [
            self._store_value(out, self._join_values(Value("var", out), self._letter_at(text, Value("var", index), node), node), node),
            self._change_var(index, Value("lit", 1), node),
        ]
        body = match_heads + [self._if_else(matched, yes, no, node)]
        done = self._not_value(self._binary("operator_lt", "text", "OPERAND1", Value("var", index), "OPERAND2", limit, True, node), node)
        heads.extend([
            self._store_value(out, Value("lit", ""), node),
            self._store_value(index, Value("lit", 1), node),
            self._repeat_until_block(done, body, node),
        ])
        self._hoist(heads)
        return Value("var", out)

    def _matches(self, text, sub, index, size, node):
        match = self._hidden_var(node, 1)
        cursor = self._hidden_var(node, 1)
        pos = self._binary("operator_subtract", "number", "NUM1", self._binary("operator_add", "number", "NUM1", Value("var", index), "NUM2", Value("var", cursor), False, node), "NUM2", Value("lit", 1), False, node)
        same = self._binary(
            "operator_equals", "text", "OPERAND1", self._letter_at(text, pos, node), "OPERAND2", self._letter_at(sub, Value("var", cursor), node), True, node,
        )
        step = [
            self._if_else(self._not_value(same, node), [self._store_value(match, Value("lit", 0), node)], [], node),
            self._change_var(cursor, Value("lit", 1), node),
        ]
        heads = [
            self._store_value(match, Value("lit", 1), node),
            self._store_value(cursor, Value("lit", 1), node),
            self._repeat_block(size, step, node),
        ]
        return self._binary("operator_equals", "text", "OPERAND1", Value("var", match), "OPERAND2", Value("lit", 1), True, node), heads

    def _split_text(self, text, sep, node):
        if not self.hoist_stack:
            self._error(node, "use this inside a script")
        dest = self._hidden_list(node)
        word = self._hidden_var(node, "")
        index = self._hidden_var(node, 1)
        length = self._text_length(text, node)
        heads, length = self._pin_value(length, node)
        heads.append(self._delete_all_items(dest))
        heads.append(self._store_value(word, Value("lit", ""), node))
        heads.append(self._store_value(index, Value("lit", 1), node))
        limit = self._binary("operator_add", "number", "NUM1", length, "NUM2", Value("lit", 1), False, node)
        letter = self._letter_at(text, Value("var", index), node)
        if sep is None:
            space = self._binary("operator_equals", "text", "OPERAND1", letter, "OPERAND2", Value("lit", " "), True, node)
            nonempty = self._binary("operator_gt", "text", "OPERAND1", self._text_length(Value("var", word), node), "OPERAND2", Value("lit", 0), True, node)
            yes = [
                self._if_else(nonempty, [self._add_item(dest, Value("var", word), node)], [], node),
                self._store_value(word, Value("lit", ""), node),
                self._change_var(index, Value("lit", 1), node),
            ]
            no = [
                self._store_value(word, self._join_values(Value("var", word), letter, node), node),
                self._change_var(index, Value("lit", 1), node),
            ]
            body = [self._if_else(space, yes, no, node)]
        else:
            more, sep = self._pin_value(sep, node)
            heads.extend(more)
            size = self._text_length(sep, node)
            heads4, size = self._pin_value(size, node)
            heads.extend(heads4)
            matched, match_heads = self._matches(text, sep, index, size, node)
            yes = [
                self._add_item(dest, Value("var", word), node),
                self._store_value(word, Value("lit", ""), node),
                self._change_var(index, size, node),
            ]
            no = [
                self._store_value(word, self._join_values(Value("var", word), letter, node), node),
                self._change_var(index, Value("lit", 1), node),
            ]
            body = match_heads + [self._if_else(matched, yes, no, node)]
        done = self._not_value(self._binary("operator_lt", "text", "OPERAND1", Value("var", index), "OPERAND2", limit, True, node), node)
        heads.append(self._repeat_until_block(done, body, node))
        if sep is None:
            nonempty = self._binary("operator_gt", "text", "OPERAND1", self._text_length(Value("var", word), node), "OPERAND2", Value("lit", 0), True, node)
            heads.append(self._if_else(nonempty, [self._add_item(dest, Value("var", word), node)], [], node))
        else:
            heads.append(self._add_item(dest, Value("var", word), node))
        self._hoist(heads)
        return Value("list", dest)

    def _join_list(self, sep, lst, node):
        if not self.hoist_stack:
            self._error(node, "use this inside a script")
        out = self._hidden_var(node, "")
        index = self._hidden_var(node, 1)
        length = self._length_of(lst)
        later = self._binary("operator_gt", "text", "OPERAND1", Value("var", index), "OPERAND2", Value("lit", 1), True, node)
        body = [
            self._if_else(later, [self._store_value(out, self._join_values(Value("var", out), sep, node), node)], [], node),
            self._store_value(out, self._join_values(Value("var", out), self._item_value(lst, Value("var", index), node), node), node),
            self._change_var(index, Value("lit", 1), node),
        ]
        self._hoist([
            self._store_value(out, Value("lit", ""), node),
            self._store_value(index, Value("lit", 1), node),
            self._repeat_block(length, body, node),
        ])
        return Value("var", out)

    def _edge_text(self, text, other, node, at_end):
        if not self.hoist_stack:
            self._error(node, "use this inside a script")
        ok = self._hidden_var(node, 1)
        index = self._hidden_var(node, 1)
        heads, other = self._pin_value(other, node)
        length = self._text_length(text, node)
        size = self._text_length(other, node)
        heads2, length = self._pin_value(length, node)
        heads.extend(heads2)
        heads3, size = self._pin_value(size, node)
        heads.extend(heads3)
        too_long = self._binary("operator_gt", "text", "OPERAND1", size, "OPERAND2", length, True, node)
        if at_end:
            pos = self._binary(
                "operator_add", "number", "NUM1",
                self._binary("operator_subtract", "number", "NUM1", length, "NUM2", size, False, node),
                "NUM2", Value("var", index), False, node,
            )
        else:
            pos = Value("var", index)
        same = self._binary(
            "operator_equals", "text", "OPERAND1", self._letter_at(text, pos, node), "OPERAND2", self._letter_at(other, Value("var", index), node), True, node,
        )
        body = [
            self._if_else(self._not_value(same, node), [self._store_value(ok, Value("lit", 0), node)], [], node),
            self._change_var(index, Value("lit", 1), node),
        ]
        check = [
            self._store_value(ok, Value("lit", 1), node),
            self._store_value(index, Value("lit", 1), node),
            self._repeat_block(size, body, node),
        ]
        heads.append(self._if_else(too_long, [self._store_value(ok, Value("lit", 0), node)], check, node))
        self._hoist(heads)
        return self._binary("operator_equals", "text", "OPERAND1", Value("var", ok), "OPERAND2", Value("lit", 1), True, node)

    def _find_text(self, text, sub, node):
        if not self.hoist_stack:
            self._error(node, "use this inside a script")
        found = self._hidden_var(node, -1)
        index = self._hidden_var(node, 1)
        heads, sub = self._pin_value(sub, node)
        length = self._text_length(text, node)
        size = self._text_length(sub, node)
        heads2, length = self._pin_value(length, node)
        heads.extend(heads2)
        heads3, size = self._pin_value(size, node)
        heads.extend(heads3)
        last = self._binary("operator_add", "number", "NUM1", self._binary("operator_subtract", "number", "NUM1", length, "NUM2", size, False, node), "NUM2", Value("lit", 1), False, node)
        matched, match_heads = self._matches(text, sub, index, size, node)
        place = self._binary("operator_subtract", "number", "NUM1", Value("var", index), "NUM2", Value("lit", 1), False, node)
        body = match_heads + [
            self._if_else(matched, [self._store_value(found, place, node)], [], node),
            self._change_var(index, Value("lit", 1), node),
        ]
        pending = self._binary("operator_equals", "text", "OPERAND1", Value("var", found), "OPERAND2", Value("lit", -1), True, node)
        room = self._binary("operator_lt", "text", "OPERAND1", Value("var", index), "OPERAND2", self._binary("operator_add", "number", "NUM1", last, "NUM2", Value("lit", 1), False, node), True, node)
        done = self._not_value(self._boolean_pair("operator_and", pending, room, node), node)
        heads.extend([
            self._store_value(found, Value("lit", -1), node),
            self._store_value(index, Value("lit", 1), node),
            self._repeat_until_block(done, body, node),
        ])
        self._hoist(heads)
        return Value("var", found)

    def _count_text(self, text, sub, node):
        if not self.hoist_stack:
            self._error(node, "use this inside a script")
        count = self._hidden_var(node, 0)
        index = self._hidden_var(node, 1)
        heads, sub = self._pin_value(sub, node)
        length = self._text_length(text, node)
        size = self._text_length(sub, node)
        heads2, length = self._pin_value(length, node)
        heads.extend(heads2)
        heads3, size = self._pin_value(size, node)
        heads.extend(heads3)
        last = self._binary("operator_add", "number", "NUM1", self._binary("operator_subtract", "number", "NUM1", length, "NUM2", size, False, node), "NUM2", Value("lit", 1), False, node)
        matched, match_heads = self._matches(text, sub, index, size, node)
        yes = [self._change_var(count, Value("lit", 1), node), self._change_var(index, size, node)]
        no = [self._change_var(index, Value("lit", 1), node)]
        body = match_heads + [self._if_else(matched, yes, no, node)]
        room = self._binary("operator_lt", "text", "OPERAND1", Value("var", index), "OPERAND2", self._binary("operator_add", "number", "NUM1", last, "NUM2", Value("lit", 1), False, node), True, node)
        done = self._not_value(room, node)
        heads.extend([
            self._store_value(count, Value("lit", 0), node),
            self._store_value(index, Value("lit", 1), node),
            self._repeat_until_block(done, body, node),
        ])
        self._hoist(heads)
        return Value("var", count)

    def _class_text(self, text, name, node):
        if not self.hoist_stack:
            self._error(node, "use this inside a script")
        ok = self._hidden_var(node, 1)
        index = self._hidden_var(node, 1)
        letter = self._hidden_var(node, "")
        length = self._text_length(text, node)
        heads, length = self._pin_value(length, node)
        empty = self._binary("operator_equals", "text", "OPERAND1", length, "OPERAND2", Value("lit", 0), True, node)
        kind = self._letter_class(Value("var", letter), name, node)
        body = [
            self._store_value(letter, self._letter_at(text, Value("var", index), node), node),
            self._if_else(self._not_value(kind, node), [self._store_value(ok, Value("lit", 0), node)], [], node),
            self._change_var(index, Value("lit", 1), node),
        ]
        check = [
            self._store_value(ok, Value("lit", 1), node),
            self._store_value(index, Value("lit", 1), node),
            self._repeat_block(length, body, node),
        ]
        heads.append(self._if_else(empty, [self._store_value(ok, Value("lit", 0), node)], check, node))
        self._hoist(heads)
        return self._binary("operator_equals", "text", "OPERAND1", Value("var", ok), "OPERAND2", Value("lit", 1), True, node)

    def _letter_class(self, letter, name, node):
        if name == "isdigit":
            low, high = "0", "9"
            lower_ok = self._span(letter, low, high, node)
            return lower_ok
        lower_ok = self._span(letter, "a", "z", node)
        upper_ok = self._span(letter, "A", "Z", node)
        return self._boolean_pair("operator_or", lower_ok, upper_ok, node)

    def _span(self, letter, low, high, node):
        not_before = self._not_value(self._binary("operator_lt", "text", "OPERAND1", letter, "OPERAND2", Value("lit", low), True, node), node)
        not_after = self._not_value(self._binary("operator_gt", "text", "OPERAND1", letter, "OPERAND2", Value("lit", high), True, node), node)
        return self._boolean_pair("operator_and", not_before, not_after, node)

    def _error(self, node, message):
        lineno = getattr(node, "lineno", "?")
        raise CompileError(f"{self.path}:{lineno}: {message}")


def _mutation(**fields):
    mutation = {"tagName": "mutation", "children": []}
    for key, value in fields.items():
        if isinstance(value, bool):
            mutation[key] = "true" if value else "false"
        elif isinstance(value, list):
            mutation[key] = json.dumps(value)
        else:
            mutation[key] = value
    return mutation


def _cblock_kind(stmt):
    if not isinstance(stmt, ast.With) or len(stmt.items) != 1:
        return None
    call = stmt.items[0].context_expr
    if not isinstance(call, ast.Call):
        return None
    func = call.func
    if isinstance(func, ast.Attribute):
        name = func.attr
    elif isinstance(func, ast.Name):
        name = func.id
    else:
        return None
    if name in {"repeat", "forever", "repeat_until", "if_"}:
        return name
    return None


def _expr_sequence_kind(node):
    if isinstance(node, (ast.List, ast.ListComp)):
        return "list"
    if isinstance(node, ast.Tuple):
        return "tuple"
    if isinstance(node, (ast.Set, ast.SetComp)):
        return "set"
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
        return "slice"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"list", "tuple", "set"}:
        return {"list": "list", "tuple": "tuple", "set": "set"}[node.func.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "split":
        return "list"
    return None


def _target_names(target):
    if target is None:
        return []
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        names = []
        for elt in target.elts:
            if isinstance(elt, ast.Starred):
                names.extend(_target_names(elt.value))
            else:
                names.extend(_target_names(elt))
        return names
    return []


def _root_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        return node.attr
    return None


def _carried_kind(fn, name):
    """A parameter that is used as a list or dictionary carries that object's id."""
    kind = None

    def set_kind(found):
        nonlocal kind
        if found is None:
            return
        if kind is None:
            kind = found
        elif kind != found:
            kind = "mixed"

    assigned, _explicit, _nonlocals = _scan_bindings(list(fn.body), {})
    set_kind({"tuple": "list", "set": "list"}.get(assigned.get(name), assigned.get(name) if assigned.get(name) in {"list", "dict"} else None))
    list_methods = {"append", "extend", "insert", "index", "add", "discard"}
    dict_methods = {"get", "update"}
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == name:
            if node.attr in list_methods:
                set_kind("list")
            elif node.attr in dict_methods:
                set_kind("dict")
        elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == name:
            sl = node.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                set_kind("dict")
            elif not isinstance(sl, ast.Slice):
                set_kind("list")
        elif isinstance(node, ast.For) and isinstance(node.iter, ast.Name) and node.iter.id == name:
            set_kind("list")
    if kind == "mixed":
        return None
    return kind


def _scan_bindings(stmts, list_names, payload=None):
    if not isinstance(list_names, dict):
        list_names = {name: "list" for name in list_names}
    found = []

    def walk(nodes):
        for stmt in nodes:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(stmt, ast.Global):
                found.append(("global", tuple(stmt.names), None))
            elif isinstance(stmt, ast.Nonlocal):
                found.append(("nonlocal", tuple(stmt.names), None))
            elif (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and isinstance(stmt.value, ast.Lambda)
            ):
                pass
            elif isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    names = tuple(_target_names(target))
                    if isinstance(target, (ast.Tuple, ast.List)):
                        found.append(("assign", names, None))
                    else:
                        found.append(("assign", names, stmt.value))
            elif isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name):
                found.append(("assign", (stmt.target.id,), stmt.value))
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value is not None:
                found.append(("assign", (stmt.target.id,), stmt.value))
            elif isinstance(stmt, ast.For):
                names = tuple(name for name in _target_names(stmt.target) if name != "_")
                found.append(("assign", names, None))
            elif isinstance(stmt, ast.ExceptHandler) and stmt.name:
                found.append(("assign", (stmt.name,), None))
            for body in _flow_bodies(stmt):
                walk(body)

    walk(list(stmts))
    assigned = {}
    explicit = set()
    nonlocals = set()
    for kind, names, value in found:
        if kind == "global":
            explicit.update(names)
        elif kind == "nonlocal":
            nonlocals.update(names)

    def resolve(value):
        if payload is not None and value is not None:
            found = payload(value)
            if found == "skip":
                return None
            if found in {"list", "dict", "tuple", "set"}:
                return found
        if value is None:
            return "var"
        if isinstance(value, ast.Name):
            kind = assigned.get(value.id)
            if kind in {"list", "tuple", "set", "dict"}:
                return kind
            if value.id in list_names:
                found = list_names[value.id] if isinstance(list_names, dict) else "list"
                if found in {"list", "dict", "tuple", "set"}:
                    return found
        kind = _expr_sequence_kind(value)
        if kind == "slice":
            base = _root_name(value.value)
            if base in list_names or assigned.get(base) in {"list", "tuple", "set"}:
                return "list"
            return "var"
        return kind or "var"

    changed = True
    while changed:
        changed = False
        for kind, names, value in found:
            if kind != "assign":
                continue
            resolved = resolve(value)
            if resolved is None:
                continue
            for name in names:
                old = assigned.get(name)
                merged = resolved if old is None else _merge_kind(old, resolved)
                if merged != old:
                    assigned[name] = merged
                    changed = True
    return assigned, explicit, nonlocals


def _merge_kind(old, new):
    if old == new:
        return old
    if old == "mixed" or new == "mixed":
        return "mixed"
    sequences = {"list", "tuple", "set"}
    if old in sequences and new in sequences:
        return old if old == new else "list"
    return "mixed"


def _flow_bodies(stmt):
    if isinstance(stmt, (ast.For, ast.While, ast.With)):
        return [list(stmt.body)]
    if isinstance(stmt, ast.If):
        return [list(stmt.body), list(stmt.orelse)]
    if isinstance(stmt, ast.Try):
        bodies = [list(stmt.body), list(stmt.orelse), list(stmt.finalbody)]
        bodies.extend(list(handler.body) for handler in stmt.handlers)
        return bodies
    return []


def _plain_call(node, name):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name and not node.keywords


def _index_needs_length(value):
    if value.kind == "lit" and isinstance(value.data, str):
        return False
    if value.kind == "lit" and _is_number(value.data) and value.data >= 0:
        return False
    return True


def _loop_stmt(stmt):
    if isinstance(stmt, (ast.For, ast.While)):
        return True
    return _cblock_kind(stmt) in {"repeat", "forever", "repeat_until"}


def _direct_nodes(stmts, kinds, enter_loops, enter_try):
    for stmt in stmts:
        if isinstance(stmt, kinds):
            return True
        if isinstance(stmt, ast.Try):
            chunks = [stmt.orelse, stmt.finalbody]
            chunks.extend(handler.body for handler in stmt.handlers)
            if enter_try:
                chunks.append(stmt.body)
            if any(_direct_nodes(chunk, kinds, enter_loops, enter_try) for chunk in chunks):
                return True
            continue
        if _loop_stmt(stmt) and not enter_loops:
            continue
        if isinstance(stmt, ast.If):
            if _direct_nodes(stmt.body, kinds, enter_loops, enter_try) or _direct_nodes(stmt.orelse, kinds, enter_loops, enter_try):
                return True
            continue
        if isinstance(stmt, (ast.For, ast.While, ast.With)) and _direct_nodes(stmt.body, kinds, enter_loops, enter_try):
            return True
    return False


def _direct_break(stmts):
    return _direct_nodes(stmts, (ast.Break, ast.Continue), False, True)


def _direct_raise(stmts):
    return _direct_nodes(stmts, (ast.Raise,), True, False)


_UPPER = [(chr(code), chr(code - 32)) for code in range(ord("a"), ord("z") + 1)]
_LOWER = [(dst, src) for src, dst in _UPPER]
_TEXT_METHODS = {
    "upper", "lower", "strip", "lstrip", "rstrip", "replace", "split", "join",
    "startswith", "endswith", "find", "count", "isdigit", "isalpha",
}

def _loop_can_return(stmt):
    kind = _cblock_kind(stmt)
    if not (isinstance(stmt, (ast.While, ast.For)) or kind in {"repeat", "forever", "repeat_until"}):
        return False
    return _contains_return(stmt.body)


def _expr_is_boolean(node):
    if isinstance(node, (ast.Compare, ast.BoolOp)):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return True
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return True
    if isinstance(node, ast.IfExp):
        return _expr_is_boolean(node.body) and _expr_is_boolean(node.orelse)
    return False


def _returns_boolean(fn):
    flags = []

    def walk(stmts):
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                flags.append(_expr_is_boolean(stmt.value))
            for body in _flow_bodies(stmt):
                walk(body)

    walk(list(fn.body))
    return bool(flags) and all(flags)


def _contains_return(stmts):
    for stmt in stmts:
        if isinstance(stmt, ast.Return):
            return True
        if isinstance(stmt, ast.If) and (_contains_return(stmt.body) or _contains_return(stmt.orelse)):
            return True
        if isinstance(stmt, (ast.While, ast.For, ast.With)) and _contains_return(stmt.body):
            return True
    return False


def _is_bool_arg(arg, default):
    if default is not None and isinstance(_constant(default), bool):
        return True
    annotation = arg.annotation
    return isinstance(annotation, ast.Name) and annotation.id == "bool"


_ND_LIST_BLOCKED = {
    "data_addtolist",
    "data_deleteoflist",
    "data_deletealloflist",
    "data_insertatlist",
    "data_replaceitemoflist",
    "data_itemoflist",
    "data_itemnumoflist",
}


def _known_shape(shape):
    return bool(shape) and all(isinstance(size, int) and size > 0 for size in shape)


def _grid_rank(fn, name):
    rank = 0
    for node in ast.walk(fn):
        if not isinstance(node, ast.Subscript):
            continue
        base, depth = _subscript_chain(node)
        if isinstance(base, ast.Name) and base.id == name:
            rank = max(rank, depth)
    return rank if rank > 1 else 0


def _subscript_chain(node):
    depth = 0
    current = node
    while isinstance(current, ast.Subscript) and not isinstance(current.slice, ast.Slice):
        sl = current.slice
        if isinstance(sl, ast.Tuple):
            if not sl.elts or any(isinstance(elt, ast.Starred) for elt in sl.elts):
                break
            depth += len(sl.elts)
        else:
            depth += 1
        current = current.value
    return current, depth


def _ast_grid_shape(node):
    if any(isinstance(elt, ast.Starred) for elt in node.elts):
        raise ValueError("write the items out, or add a list with +=")
    if not all(isinstance(elt, (ast.List, ast.Tuple)) for elt in node.elts):
        raise ValueError("a list cannot mix single items and nested lists")
    shapes = [_ast_child_shape(elt) for elt in node.elts]
    first = shapes[0]
    for other in shapes[1:]:
        if other != first:
            raise ValueError("higher-dimensional lists must be rectangular")
    return (len(node.elts),) + first


def _ast_child_shape(node):
    if not isinstance(node, (ast.List, ast.Tuple)):
        raise ValueError("higher-dimensional lists must be rectangular")
    if not node.elts:
        raise ValueError("a higher-dimensional list needs at least one item along each dimension")
    if any(isinstance(elt, ast.Starred) for elt in node.elts):
        raise ValueError("write the items out, or add a list with +=")
    if isinstance(node.elts[0], (ast.List, ast.Tuple)):
        if not all(isinstance(elt, (ast.List, ast.Tuple)) for elt in node.elts):
            raise ValueError("nested lists must be the same depth throughout")
        return _ast_grid_shape(node)
    if any(isinstance(elt, (ast.List, ast.Tuple)) for elt in node.elts):
        raise ValueError("nested lists must be the same depth throughout")
    return (len(node.elts),)


def _ast_grid_atoms(node, depth, shape):
    if depth == len(shape):
        if isinstance(node, (ast.List, ast.Tuple)):
            raise ValueError("nested lists must be the same depth throughout")
        return [node]
    if not isinstance(node, (ast.List, ast.Tuple)) or len(node.elts) != shape[depth]:
        raise ValueError("higher-dimensional lists must be rectangular")
    atoms = []
    for elt in node.elts:
        atoms.extend(_ast_grid_atoms(elt, depth + 1, shape))
    return atoms


def _flatten_list(initial):
    """Return (shape, items). A one-dimensional list has shape ()."""
    if any(isinstance(item, list) for item in initial):
        if not all(isinstance(item, list) for item in initial):
            raise ValueError("a list cannot mix single items and nested lists")
        shape = _nested_shape(initial)
        if any(size == 0 for size in shape):
            raise ValueError("a higher-dimensional list needs at least one item along each dimension")
        flat = []
        _walk_rect(initial, shape, 0, (), flat)
        return shape, flat
    for item in initial:
        if isinstance(item, bool) or not isinstance(item, (int, float, str)):
            raise ValueError("list items must be numbers or text")
    return (), initial


def _nested_shape(value):
    if not isinstance(value, list):
        return ()
    if not value:
        return (0,)
    return (len(value),) + _nested_shape(value[0])


def _walk_rect(value, shape, depth, path, flat):
    if depth == len(shape):
        if isinstance(value, list):
            raise ValueError("nested lists must be the same depth throughout")
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise ValueError("list items must be numbers or text")
        flat.append(value)
        return
    where = _index_path(path)
    if not isinstance(value, list):
        raise ValueError(f"higher-dimensional lists must be rectangular. {where} is a single item")
    if len(value) != shape[depth]:
        got = len(value)
        word = "item" if got == 1 else "items"
        raise ValueError(
            f"higher-dimensional lists must be rectangular. {where} has {got} {word}, expected {shape[depth]}"
        )
    for index, item in enumerate(value, start=1):
        _walk_rect(item, shape, depth + 1, path + (index,), flat)


def _index_path(path):
    if not path:
        return "the list"
    return "[" + "][".join(str(index) for index in path) + "]"


def _fold_flat_index(shape, numbers):
    acc = numbers[0]
    for dim in range(1, len(numbers)):
        acc = (acc - 1) * shape[dim] + numbers[dim]
    return acc


def _constant(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (bool, int, float, str)):
            return node.value
        return _NOT_CONSTANT
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _constant(node.operand)
        if _is_number(inner):
            return -inner
        return _NOT_CONSTANT
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        items = _constant_items(node.elts)
        if items is _NOT_CONSTANT:
            return _NOT_CONSTANT
        if isinstance(node, ast.Tuple):
            return FrozenList(items)
        if isinstance(node, ast.Set):
            if len(items) != len(set(items)):
                raise ValueError("a set cannot repeat an item")
            return UniqueList(items)
        return items
    if isinstance(node, ast.Dict):
        return _dict_from(node, _constant)
    return _NOT_CONSTANT


def _constant_items(elts):
    items = []
    for elt in elts:
        item = _constant(elt)
        if item is _NOT_CONSTANT:
            return _NOT_CONSTANT
        if isinstance(item, list):
            items.append(item)
            continue
        if isinstance(item, bool) or not isinstance(item, (int, float, str)):
            raise ValueError("list items must be numbers or text")
        items.append(item)
    return items


def _dict_from(node, convert):
    if any(key is None for key in node.keys):
        raise ValueError("a dictionary is written as {key: value}")
    pairs = []
    seen = []
    for key_node, value_node in zip(node.keys, node.values):
        key = convert(key_node)
        value = convert(value_node)
        if key is _NOT_CONSTANT or value is _NOT_CONSTANT:
            return _NOT_CONSTANT
        if isinstance(key, bool) or not isinstance(key, (int, float, str)):
            raise ValueError("dictionary keys are numbers or text")
        if isinstance(value, bool) or not isinstance(value, (int, float, str, DictLiteral)):
            raise ValueError("dictionary values are numbers or text")
        if isinstance(value, DictLiteral):
            raise ValueError("dictionary values are numbers or text")
        if any(key == item for item in seen):
            raise ValueError("dictionary key is repeated")
        seen.append(key)
        pairs.append((key, value))
    return DictLiteral(pairs)


def _nested_statements(stmt):
    if isinstance(stmt, (ast.FunctionDef, ast.For, ast.While, ast.With)):
        return list(stmt.body)
    if isinstance(stmt, ast.If):
        return list(stmt.body) + list(stmt.orelse)
    return []


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _either_text(left, right):
    for value in (left, right):
        if value.kind == "lit" and isinstance(value.data, str):
            return True
        if getattr(value, "text", False):
            return True
    return False


def _as_text(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if _is_number(value):
        return _format_number(value)
    return str(value)


def _format_number(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return format(value, "g")
    return str(value)


def _scratch_literal(value):
    if isinstance(value, str):
        return value
    if _is_number(value):
        number = float(value)
        if number.is_integer():
            return int(number)
        return number
    return value


def _fold_numbers(op, left, right):
    if isinstance(op, ast.Add):
        return left + right
    if isinstance(op, ast.Sub):
        return left - right
    if isinstance(op, ast.Mult):
        return left * right
    if isinstance(op, ast.Div):
        return left / right
    if isinstance(op, ast.Mod):
        return left % right
    raise CompileError("this operator has no Scratch block")


def _normalize_key(key):
    text = str(key).strip()
    lowered = text.lower()
    if lowered in _KEYS:
        return _KEYS[lowered]
    return lowered


def _normalize_menu(menu, text):
    lowered = text.strip().lower()
    if lowered in _SPECIAL_MENUS and menu in {"goto", "glide", "point", "touching", "distance", "clone", "object"}:
        if menu == "clone" and lowered not in {"myself"}:
            return text
        if menu == "object" and lowered not in {"stage"}:
            return text
        if menu in {"goto", "glide", "point", "touching", "distance"} and lowered == "myself":
            return text
        return _SPECIAL_MENUS[lowered]
    if menu == "key":
        return _normalize_key(text)
    return text


def _normalize_field(slot, text, node):
    key = text.strip().lower()
    tables = {
        "field:effect": _EFFECTS,
        "field:sound_effect": _SOUND_EFFECTS,
        "field:rotation": _ROTATION,
        "field:stop": _STOP,
        "field:drag": _DRAG,
        "field:front": _FRONT,
        "field:layers": _LAYERS,
        "field:current": _CURRENT,
        "field:pen": _PEN,
        "field:property": None,
    }
    if slot == "field:property":
        aliases = {
            "costume number": "costume #",
            "costume name": "costume name",
            "backdrop number": "backdrop #",
            "backdrop name": "backdrop name",
            "x": "x position",
            "y": "y position",
        }
        return aliases.get(key, text)
    table = tables.get(slot)
    if table is None or key not in table:
        raise CompileError(f"line {getattr(node, 'lineno', '?')}: unknown {slot.split(':', 1)[-1]} {text!r}")
    return table[key]


def _normalize_color(value, node):
    if not isinstance(value, str):
        raise CompileError(f"line {getattr(node, 'lineno', '?')}: color must look like #ff8800")
    text = value.strip()
    if not text.startswith("#"):
        text = "#" + text
    if len(text) not in {4, 7}:
        raise CompileError(f"line {getattr(node, 'lineno', '?')}: color must look like #ff8800")
    return text.lower()


def _wav_info(data):
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return 48000, 1
    rate = 48000
    channels = 1
    bits = 16
    data_size = 0
    pos = 12
    while pos + 8 <= len(data):
        chunk = data[pos:pos + 4]
        size = int.from_bytes(data[pos + 4:pos + 8], "little")
        body = data[pos + 8:pos + 8 + size]
        if chunk == b"fmt " and len(body) >= 16:
            channels = int.from_bytes(body[2:4], "little") or 1
            rate = int.from_bytes(body[4:8], "little") or 48000
            bits = int.from_bytes(body[14:16], "little") or 16
        elif chunk == b"data":
            data_size = size
        pos += 8 + size + (size % 2)
    width = max(1, bits // 8)
    count = data_size // max(1, channels * width) if data_size else 1
    return rate, max(1, count)


def _install_project_helpers():
    def shared_vars_by_name(self):
        return {var.name: var for var in self.shared_vars.values()}

    Project.shared_vars_by_name = shared_vars_by_name


_install_project_helpers()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compile kitty Python scripts into a Scratch .sb3 file")
    parser.add_argument("scripts", nargs="+", help="Python scripts or a directory of them. stage.py becomes the stage")
    parser.add_argument("-o", "--output", help="output .sb3 path")
    args = parser.parse_args(argv)
    warnings = []
    try:
        destination = comp(args.scripts, args.output, warnings)
    except CompileError as exc:
        print(exc, file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())