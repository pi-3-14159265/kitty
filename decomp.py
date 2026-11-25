"""Decompile a Scratch 3 .sb3 file into a Kitty project folder.

    kitty decomp Fishing.sb3
    kitty decomp Fishing.sb3 output_folder
    py -m kitty decomp Fishing.sb3

Fishing.sb3 becomes the folder Fishing/:

    Fishing/
        Assets/            costumes and backdrops
        Sounds/            sounds
        stage.py           the stage
        Cat.py             one Kitty Python file per sprite
        blocksAsText.txt   every script, written out as Scratch blocks

Build it again with `kitty build Fishing/`. Blocks Kitty has no Python for
are kept as comments, and the command warns about each one.
"""

from __future__ import annotations

import json
import keyword
import math
import re
import zipfile
from pathlib import Path, PurePosixPath

from comp import _bitmap_info, _svg_center
from kitty import BLOCKS


def decomp(target, optional_directory=None, warnings=None):
    """Decompile a Scratch .sb3 file into a Kitty project folder.

    target: path to the .sb3 file.
    optional_directory: folder to write. When omitted, the folder is created
        next to the .sb3 file, named after it (Fishing.sb3 becomes Fishing/).
        The folder must be new or empty, so a decompile never overwrites
        Python you have changed.
    warnings: optional list that receives a line for each block Kitty could
        not turn into Python.

    Returns the output directory.
    """
    path = Path(target)
    if not path.is_file():
        raise FileNotFoundError(f"Scratch file not found: {path}")

    directory = Path(optional_directory) if optional_directory is not None else _default_directory(path)
    if directory.exists():
        if not directory.is_dir():
            raise FileExistsError(f"{directory} is a file. Choose a folder name")
        if any(directory.iterdir()):
            raise FileExistsError(f"{directory} already has files in it. Choose a new or empty folder")
    with zipfile.ZipFile(path) as archive:
        try:
            raw = archive.read("project.json")
        except KeyError as exc:
            raise ValueError(f"{path} is not a Scratch .sb3 file (no project.json)") from exc
        project = json.loads(raw.decode("utf-8"))
        text, _sections = _render_project(project, path.name)
        writer = _ProjectWriter(project, archive, path.name)
        files = writer.build()
    files["blocksAsText.txt"] = text.encode("utf-8")
    directory.mkdir(parents=True, exist_ok=True)
    for folder in ("Assets", "Sounds"):
        (directory / folder).mkdir(exist_ok=True)
    for relative, data in files.items():
        destination = directory / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    if warnings is not None:
        warnings.extend(writer.warnings)
    return directory


def _default_directory(path):
    directory = path.with_suffix("")
    if directory.exists() and not directory.is_dir():
        directory = path.with_name(path.stem + "_decompiled")
    return directory


def _render_project(project, filename):
    header = _project_header(project, filename)
    sections = []
    for target in project.get("targets") or []:
        name = target.get("name") or ("Stage" if target.get("isStage") else "sprite")
        sections.append((name, _render_target(target)))
    parts = [header] if header else []
    parts.extend(section for _name, section in sections)
    text = "\n\n".join(part.rstrip("\n") for part in parts if part)
    if text:
        text += "\n"
    return text, sections


def _project_header(project, filename):
    meta = project.get("meta") or {}
    lines = [f"// {filename}"]
    if meta.get("semver"):
        lines.append(f"// Scratch {meta['semver']}")
    if meta.get("vm"):
        lines.append(f"// vm {meta['vm']}")
    extensions = project.get("extensions") or []
    if extensions:
        lines.append("// extensions: " + ", ".join(str(item) for item in extensions))
    for monitor in project.get("monitors") or []:
        if monitor.get("visible", True) is False:
            continue
        params = monitor.get("params") or {}
        label = (
            params.get("VARIABLE")
            or params.get("LIST")
            or monitor.get("opcode")
            or "monitor"
        )
        sprite = monitor.get("spriteName") or "Stage"
        lines.append(f"// monitor on {sprite}: {label}")
    return "\n".join(lines)


def _render_target(target):
    lines = [_target_header(target)]
    body = _TargetDecompiler(target).scripts()
    if body:
        lines.append(body)
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    return text


def _target_header(target):
    name = target.get("name") or ("Stage" if target.get("isStage") else "sprite")
    kind = "Stage" if target.get("isStage") else "Sprite"
    lines = [f"// {kind}: {name}"]
    costumes = [item.get("name") for item in target.get("costumes") or [] if item.get("name")]
    sounds = [item.get("name") for item in target.get("sounds") or [] if item.get("name")]
    if costumes:
        lines.append("// costumes: " + ", ".join(costumes))
    if sounds:
        lines.append("// sounds: " + ", ".join(sounds))

    scope = "for all sprites" if target.get("isStage") else "for this sprite only"
    variables = list((target.get("variables") or {}).values())
    lists = list((target.get("lists") or {}).values())
    if variables:
        lines.append(f"// variables ({scope}):")
        for entry in variables:
            vname = entry[0]
            value = entry[1] if len(entry) > 1 else 0
            lines.append(f"//   {vname} = {_literal(value)}")
    if lists:
        lines.append(f"// lists ({scope}):")
        for entry in lists:
            lname = entry[0]
            value = entry[1] if len(entry) > 1 else []
            lines.append(f"//   {lname} = {_literal(value)}")
    broadcasts = list((target.get("broadcasts") or {}).values())
    if broadcasts:
        lines.append("// broadcasts: " + ", ".join(str(item) for item in broadcasts))
    return "\n".join(lines)


def _literal(value):
    return json.dumps(value, ensure_ascii=False)


class _TargetDecompiler:
    def __init__(self, target):
        self.blocks = target.get("blocks") or {}
        self.attached = {}
        self.floating = []
        for comment in (target.get("comments") or {}).values():
            text = comment.get("text") or ""
            block_id = comment.get("blockId")
            if block_id:
                self.attached[block_id] = text
            else:
                self.floating.append(comment)
        self.expr_stack = []

    def scripts(self):
        items = []
        for index, (block_id, block) in enumerate(self.blocks.items()):
            if isinstance(block, list):
                items.append((self._coord(block, 4), self._coord(block, 3), index, ("reporter", block)))
            elif isinstance(block, dict) and block.get("topLevel") and not block.get("shadow"):
                items.append((block.get("y") or 0, block.get("x") or 0, index, ("script", block_id)))
        for index, comment in enumerate(self.floating):
            items.append((comment.get("y") or 0, comment.get("x") or 0, index, ("comment", comment)))
        items.sort(key=lambda item: (item[0], item[1], item[2]))

        chunks = []
        for _y, _x, _index, (kind, payload) in items:
            if kind == "comment":
                chunks.append(_comment_block(payload.get("text") or ""))
            elif kind == "reporter":
                chunks.append(self._floating_reporter(payload))
            else:
                rendered = self._chain(payload, 0)
                if rendered:
                    chunks.append("\n".join(rendered))
        return "\n\n".join(chunk for chunk in chunks if chunk)

    def _floating_reporter(self, block):
        name = block[1] if len(block) > 1 else "?"
        return f"({name})"

    def _chain(self, block_id, indent):
        lines = []
        seen = set()
        while block_id and block_id not in seen:
            seen.add(block_id)
            block = self.blocks.get(block_id)
            if not isinstance(block, dict):
                break
            lines.extend(self._statement(block_id, block, indent))
            block_id = block.get("next")
        return lines

    def _statement(self, block_id, block, indent):
        opcode = block.get("opcode")
        pad = "    " * indent
        comment = self.attached.get(block_id, "")

        if opcode == "procedures_definition":
            return _emit(pad, self._define(block), comment)
        if opcode == "procedures_call":
            return _emit(pad, self._call(block), comment)

        spec = _SPECS.get(opcode)
        if spec and spec[0] in ("reporter", "boolean"):
            return _emit(pad, self._expression(block_id), comment)

        if spec:
            shape, template, boolean_inputs = spec
            line = self._fill(template, block, boolean_inputs)
        else:
            shape = _inferred_shape(block)
            line = self._generic(block, frozenset())

        head = _emit(pad, line, comment)
        if shape == "ifelse":
            body = self._chain(self._substack(block, "SUBSTACK"), indent + 1)
            other = self._chain(self._substack(block, "SUBSTACK2"), indent + 1)
            return head + body + [pad + "else"] + other + [pad + "end"]
        if shape == "c":
            body = self._chain(self._substack(block, "SUBSTACK"), indent + 1)
            return head + body + [pad + "end"]
        return head

    def _define(self, block):
        proto = self._prototype(block)
        if proto is None:
            return "define custom block"
        mutation = proto.get("mutation") or block.get("mutation") or {}
        code = mutation.get("proccode") or "custom block"
        arg_ids = _json_list(mutation.get("argumentids"))
        names = _json_list(mutation.get("argumentnames"))
        rendered = _splice_proccode(
            code,
            arg_ids,
            lambda index, arg_id, spec: self._define_arg(proto, arg_id, names, index, spec),
        )
        line = "define " + rendered
        if _is_warp(mutation):
            line += " // run without screen refresh"
        return line

    def _define_arg(self, proto, arg_id, names, index, spec):
        name = self._argument_name(proto, arg_id)
        if not name and index < len(names):
            name = str(names[index])
        if not name:
            name = "arg"
        if spec == "%b":
            return f"<{name}>"
        return f"({name})"

    def _argument_name(self, proto, arg_id):
        inp = (proto.get("inputs") or {}).get(arg_id)
        block_id = _input_block_id(inp)
        block = self.blocks.get(block_id) if block_id else None
        if not isinstance(block, dict):
            return ""
        return self._field_label(block, "VALUE")

    def _call(self, block):
        mutation = block.get("mutation") or {}
        code = mutation.get("proccode") or block.get("opcode") or "custom block"
        arg_ids = _json_list(mutation.get("argumentids"))

        def render_arg(_index, arg_id, spec):
            inp = (block.get("inputs") or {}).get(arg_id)
            if not inp:
                return "<>" if spec == "%b" else "()"
            boolean_inputs = frozenset({arg_id}) if spec == "%b" else frozenset()
            return self._input_value(inp, arg_id, boolean_inputs)

        return _splice_proccode(code, arg_ids, render_arg)

    def _prototype(self, block):
        inp = (block.get("inputs") or {}).get("custom_block")
        block_id = _input_block_id(inp)
        proto = self.blocks.get(block_id) if block_id else None
        if isinstance(proto, dict):
            return proto
        return None

    def _fill(self, template, block, boolean_inputs):
        fields = block.get("fields") or {}
        inputs = block.get("inputs") or {}

        def replace(match):
            name = match.group(1)
            if name in fields:
                return self._dropdown(name, fields[name])
            if name in inputs:
                return self._input_value(inputs[name], name, boolean_inputs)
            if name in boolean_inputs:
                return "<>"
            return "()"

        return _PLACEHOLDER.sub(replace, template)

    def _generic(self, block, boolean_inputs):
        parts = [block.get("opcode") or "block"]
        for name, value in (block.get("fields") or {}).items():
            parts.append(self._dropdown(name, value))
        for name, value in (block.get("inputs") or {}).items():
            if name in ("SUBSTACK", "SUBSTACK2", "custom_block"):
                continue
            parts.append(self._input_value(value, name, boolean_inputs))
        return " ".join(parts)

    def _dropdown(self, field_name, field_value):
        return f"[{self._escape(self._field_text(field_name, field_value))} v]"

    def _field_label(self, block, field_name):
        return self._field_text(field_name, (block.get("fields") or {}).get(field_name))

    def _field_text(self, field_name, field_value):
        if isinstance(field_value, list):
            raw = field_value[0] if field_value else ""
        else:
            raw = "" if field_value is None else field_value
        if raw is None:
            raw = ""
        return _humanize(field_name, str(raw))

    def _input_value(self, inp, input_name, boolean_inputs):
        if not isinstance(inp, list) or not inp:
            return _empty_slot(input_name, boolean_inputs)
        kind = inp[0]
        if kind == 1:
            if len(inp) < 2 or inp[1] is None:
                return _empty_slot(input_name, boolean_inputs)
            return self._shadow_or_primitive(inp[1], input_name, boolean_inputs)
        if kind == 2:
            block_id = inp[1] if len(inp) > 1 else None
            if not isinstance(block_id, str):
                return "<>" if input_name in boolean_inputs else _empty_slot(input_name, boolean_inputs)
            return self._expression(block_id)
        if kind == 3:
            block_id = inp[1] if len(inp) > 1 else None
            shadow = inp[2] if len(inp) > 2 else None
            if isinstance(block_id, str) and block_id:
                return self._expression(block_id)
            if shadow is not None:
                return self._shadow_or_primitive(shadow, input_name, boolean_inputs)
            return _empty_slot(input_name, boolean_inputs)
        return _empty_slot(input_name, boolean_inputs)

    def _shadow_or_primitive(self, value, input_name, boolean_inputs):
        if isinstance(value, list):
            if value and isinstance(value[0], int):
                return self._primitive(value, input_name)
            return _empty_slot(input_name, boolean_inputs)
        if isinstance(value, str):
            block = self.blocks.get(value)
            if not isinstance(block, dict):
                return _empty_slot(input_name, boolean_inputs)
            if block.get("shadow") and block.get("opcode") not in ("procedures_prototype",):
                return self._literal_or_menu(block)
            return self._expression(value)
        return _empty_slot(input_name, boolean_inputs)

    def _literal_or_menu(self, block):
        opcode = block.get("opcode")
        if opcode in _NUMBER_SHADOWS:
            return _wrap_number(self._first_field(block))
        if opcode == "text":
            return _wrap_text(self._first_field(block))
        if opcode in ("colour_picker", "color_picker"):
            return _wrap_color(self._first_field(block))
        if opcode == "note":
            raw = self._first_field(block)
            return _wrap_number(raw) if _looks_numeric(raw) or raw == "" else f"({raw})"
        return self._dropdown_from_block(block)

    def _dropdown_from_block(self, block):
        fields = block.get("fields") or {}
        if not fields:
            return "[ v]"
        name, value = next(iter(fields.items()))
        return self._dropdown(name, value)

    def _first_field(self, block):
        fields = block.get("fields") or {}
        if not fields:
            return ""
        value = next(iter(fields.values()))
        if isinstance(value, list):
            return "" if not value or value[0] is None else str(value[0])
        return "" if value is None else str(value)

    def _primitive(self, prim, input_name):
        ptype = prim[0]
        value = prim[1] if len(prim) > 1 else ""
        if ptype in (4, 5, 6, 7, 8):
            return _wrap_number(value, input_name)
        if ptype == 9:
            return _wrap_color(value)
        if ptype == 10:
            return _wrap_text(value, input_name)
        if ptype == 11:
            return f"[{self._escape(value)} v]"
        if ptype in (12, 13):
            return f"({value})"
        return f"({value})"

    def _expression(self, block_id):
        if block_id in self.expr_stack or len(self.expr_stack) > 100:
            return "(...)"
        block = self.blocks.get(block_id)
        if isinstance(block, list):
            return self._floating_reporter(block)
        if not isinstance(block, dict):
            return "()"
        if block.get("shadow") and block.get("opcode") != "procedures_prototype":
            return self._literal_or_menu(block)

        self.expr_stack.append(block_id)
        try:
            opcode = block.get("opcode")
            if opcode == "data_variable":
                return f"({self._field_label(block, 'VARIABLE')})"
            if opcode == "data_listcontents":
                return f"({self._field_label(block, 'LIST')})"
            if opcode == "argument_reporter_string_number":
                return f"({self._field_label(block, 'VALUE')})"
            if opcode == "argument_reporter_boolean":
                return f"<{self._field_label(block, 'VALUE')}>"
            spec = _SPECS.get(opcode)
            if spec:
                return self._fill(spec[1], block, spec[2])
            return "(" + self._generic(block, frozenset()) + ")"
        finally:
            self.expr_stack.pop()

    def _substack(self, block, name):
        return _input_block_id((block.get("inputs") or {}).get(name))

    def _escape(self, text):
        return str(text).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")

    @staticmethod
    def _coord(block, index):
        if len(block) > index and isinstance(block[index], (int, float)):
            return block[index]
        return 0


def _emit(pad, line, comment):
    """Indent one statement and hang its comment off that line."""
    comment_lines = comment.splitlines() if comment else []
    if not comment_lines:
        return [pad + line]
    lines = [pad + line + " // " + comment_lines[0]]
    lines.extend(pad + "// " + extra for extra in comment_lines[1:])
    return lines


def _input_block_id(inp):
    if not isinstance(inp, list) or len(inp) < 2:
        return None
    # Substacks and shadow menus store the block id in the second slot.
    # An obscured input stores the real block id there too.
    if isinstance(inp[1], str):
        return inp[1]
    return None


def _empty_slot(input_name, boolean_inputs):
    if input_name in boolean_inputs:
        return "<>"
    return "()"


def _wrap_number(value, input_name=None):
    text = "" if value is None else str(value)
    if input_name == "INDEX" and text in {"last", "all", "random"}:
        return f"({text} v)"
    if text.strip() == "":
        return "()"
    return f"({text.strip()})"


def _wrap_text(value, input_name=None):
    text = "" if value is None else str(value)
    if input_name == "INDEX" and text in {"last", "all", "random"}:
        return f"({text} v)"
    if _looks_numeric(text):
        return f"({text.strip()})"
    if text == "":
        return "[]"
    return "[" + text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]") + "]"


def _wrap_color(value):
    text = "" if value is None else str(value)
    if text and not text.startswith("#"):
        text = "#" + text
    return f"[{text}]"


def _looks_numeric(value):
    return _NUMBER.fullmatch(str(value).strip()) is not None


def _humanize(field_name, text):
    if text in _MENU_SPECIAL:
        return _MENU_SPECIAL[text]
    table = _FIELD_LABELS.get(field_name)
    if table and text in table:
        return table[text]
    return text


def _inferred_shape(block):
    inputs = block.get("inputs") or {}
    if "SUBSTACK2" in inputs:
        return "ifelse"
    if "SUBSTACK" in inputs:
        return "c"
    return "stack"


def _json_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else []
    return []


def _is_warp(mutation):
    warp = mutation.get("warp")
    return warp is True or str(warp).lower() == "true"


def _splice_proccode(proccode, arg_ids, render_arg):
    pieces = _PROC_SPLIT.split(proccode)
    arg_index = 0
    out = []
    for piece in pieces:
        if piece in ("%s", "%n", "%b") and arg_index < len(arg_ids):
            out.append(render_arg(arg_index, arg_ids[arg_index], piece))
            arg_index += 1
        else:
            out.append(piece)
    return "".join(out)


def _comment_block(text):
    lines = text.splitlines() or [""]
    return "\n".join("// " + line for line in lines)


_WINDOWS_RESERVED = {"con", "prn", "aux", "nul"} | {f"com{n}" for n in range(1, 10)} | {f"lpt{n}" for n in range(1, 10)}


def _safe_file_stem(name, fallback):
    """A file name stem that works on Windows, macOS, and Linux."""
    cleaned = _UNSAFE_FILENAME.sub("_", str(name)).strip(" .")
    if not cleaned:
        return fallback
    if cleaned.split(".")[0].lower() in _WINDOWS_RESERVED:
        cleaned += "_"
    return cleaned


def _spec(shape, template, boolean=""):
    names = frozenset(boolean.split()) if boolean else frozenset()
    return (shape, template, names)


# {NAME} is either a dropdown field or an input slot of that block.
_SPECS = {
    # Motion
    "motion_movesteps": _spec("stack", "move {STEPS} steps"),
    "motion_turnright": _spec("stack", "turn right {DEGREES} degrees"),
    "motion_turnleft": _spec("stack", "turn left {DEGREES} degrees"),
    "motion_goto": _spec("stack", "go to {TO}"),
    "motion_gotoxy": _spec("stack", "go to x: {X} y: {Y}"),
    "motion_glideto": _spec("stack", "glide {SECS} secs to {TO}"),
    "motion_glidesecstoxy": _spec("stack", "glide {SECS} secs to x: {X} y: {Y}"),
    "motion_pointindirection": _spec("stack", "point in direction {DIRECTION}"),
    "motion_pointtowards": _spec("stack", "point towards {TOWARDS}"),
    "motion_changexby": _spec("stack", "change x by {DX}"),
    "motion_setx": _spec("stack", "set x to {X}"),
    "motion_changeyby": _spec("stack", "change y by {DY}"),
    "motion_sety": _spec("stack", "set y to {Y}"),
    "motion_ifonedgebounce": _spec("stack", "if on edge, bounce"),
    "motion_setrotationstyle": _spec("stack", "set rotation style {STYLE}"),
    "motion_xposition": _spec("reporter", "(x position)"),
    "motion_yposition": _spec("reporter", "(y position)"),
    "motion_direction": _spec("reporter", "(direction)"),
    # Looks
    "looks_sayforsecs": _spec("stack", "say {MESSAGE} for {SECS} seconds"),
    "looks_say": _spec("stack", "say {MESSAGE}"),
    "looks_thinkforsecs": _spec("stack", "think {MESSAGE} for {SECS} seconds"),
    "looks_think": _spec("stack", "think {MESSAGE}"),
    "looks_switchcostumeto": _spec("stack", "switch costume to {COSTUME}"),
    "looks_nextcostume": _spec("stack", "next costume"),
    "looks_switchbackdropto": _spec("stack", "switch backdrop to {BACKDROP}"),
    "looks_switchbackdroptoandwait": _spec("stack", "switch backdrop to {BACKDROP} and wait"),
    "looks_nextbackdrop": _spec("stack", "next backdrop"),
    "looks_changesizeby": _spec("stack", "change size by {CHANGE}"),
    "looks_setsizeto": _spec("stack", "set size to {SIZE} %"),
    "looks_changeeffectby": _spec("stack", "change {EFFECT} effect by {CHANGE}"),
    "looks_seteffectto": _spec("stack", "set {EFFECT} effect to {VALUE}"),
    "looks_cleargraphiceffects": _spec("stack", "clear graphic effects"),
    "looks_show": _spec("stack", "show"),
    "looks_hide": _spec("stack", "hide"),
    "looks_gotofrontback": _spec("stack", "go to {FRONT_BACK} layer"),
    "looks_goforwardbackwardlayers": _spec("stack", "go {FORWARD_BACKWARD} {NUM} layers"),
    "looks_costumenumbername": _spec("reporter", "(costume {NUMBER_NAME})"),
    "looks_backdropnumbername": _spec("reporter", "(backdrop {NUMBER_NAME})"),
    "looks_size": _spec("reporter", "(size)"),
    # Sound
    "sound_playuntildone": _spec("stack", "play sound {SOUND_MENU} until done"),
    "sound_play": _spec("stack", "start sound {SOUND_MENU}"),
    "sound_stopallsounds": _spec("stack", "stop all sounds"),
    "sound_changeeffectby": _spec("stack", "change {EFFECT} effect by {VALUE}"),
    "sound_seteffectto": _spec("stack", "set {EFFECT} effect to {VALUE}"),
    "sound_cleareffects": _spec("stack", "clear sound effects"),
    "sound_changevolumeby": _spec("stack", "change volume by {VOLUME}"),
    "sound_setvolumeto": _spec("stack", "set volume to {VOLUME} %"),
    "sound_volume": _spec("reporter", "(volume)"),
    # Events
    "event_whenflagclicked": _spec("stack", "when green flag clicked"),
    "event_whenkeypressed": _spec("stack", "when {KEY_OPTION} key pressed"),
    "event_whenthisspriteclicked": _spec("stack", "when this sprite clicked"),
    "event_whenstageclicked": _spec("stack", "when stage clicked"),
    "event_whenbackdropswitchesto": _spec("stack", "when backdrop switches to {BACKDROP}"),
    "event_whengreaterthan": _spec("stack", "when {WHENGREATERTHANMENU} > {VALUE}"),
    "event_whenbroadcastreceived": _spec("stack", "when I receive {BROADCAST_OPTION}"),
    "event_broadcast": _spec("stack", "broadcast {BROADCAST_INPUT}"),
    "event_broadcastandwait": _spec("stack", "broadcast {BROADCAST_INPUT} and wait"),
    # Control
    "control_wait": _spec("stack", "wait {DURATION} seconds"),
    "control_repeat": _spec("c", "repeat {TIMES}"),
    "control_forever": _spec("c", "forever"),
    "control_if": _spec("c", "if {CONDITION} then", "CONDITION"),
    "control_if_else": _spec("ifelse", "if {CONDITION} then", "CONDITION"),
    "control_wait_until": _spec("stack", "wait until {CONDITION}", "CONDITION"),
    "control_repeat_until": _spec("c", "repeat until {CONDITION}", "CONDITION"),
    "control_stop": _spec("stack", "stop {STOP_OPTION}"),
    "control_start_as_clone": _spec("stack", "when I start as a clone"),
    "control_create_clone_of": _spec("stack", "create clone of {CLONE_OPTION}"),
    "control_delete_this_clone": _spec("stack", "delete this clone"),
    # Sensing
    "sensing_touchingobject": _spec("boolean", "<touching {TOUCHINGOBJECTMENU}?>"),
    "sensing_touchingcolor": _spec("boolean", "<touching color {COLOR}?>"),
    "sensing_coloristouchingcolor": _spec("boolean", "<color {COLOR} is touching {COLOR2}?>"),
    "sensing_distanceto": _spec("reporter", "(distance to {DISTANCETOMENU})"),
    "sensing_askandwait": _spec("stack", "ask {QUESTION} and wait"),
    "sensing_answer": _spec("reporter", "(answer)"),
    "sensing_keypressed": _spec("boolean", "<key {KEY_OPTION} pressed?>"),
    "sensing_mousedown": _spec("boolean", "<mouse down?>"),
    "sensing_mousex": _spec("reporter", "(mouse x)"),
    "sensing_mousey": _spec("reporter", "(mouse y)"),
    "sensing_setdragmode": _spec("stack", "set drag mode {DRAG_MODE}"),
    "sensing_loudness": _spec("reporter", "(loudness)"),
    "sensing_timer": _spec("reporter", "(timer)"),
    "sensing_resettimer": _spec("stack", "reset timer"),
    "sensing_of": _spec("reporter", "({PROPERTY} of {OBJECT})"),
    "sensing_current": _spec("reporter", "(current {CURRENTMENU})"),
    "sensing_dayssince2000": _spec("reporter", "(days since 2000)"),
    "sensing_username": _spec("reporter", "(username)"),
    "sensing_userid": _spec("reporter", "(user id)"),
    "sensing_online": _spec("boolean", "<online?>"),
    # Operators
    "operator_add": _spec("reporter", "({NUM1} + {NUM2})"),
    "operator_subtract": _spec("reporter", "({NUM1} - {NUM2})"),
    "operator_multiply": _spec("reporter", "({NUM1} * {NUM2})"),
    "operator_divide": _spec("reporter", "({NUM1} / {NUM2})"),
    "operator_random": _spec("reporter", "(pick random {FROM} to {TO})"),
    "operator_gt": _spec("boolean", "<{OPERAND1} > {OPERAND2}>"),
    "operator_lt": _spec("boolean", "<{OPERAND1} < {OPERAND2}>"),
    "operator_equals": _spec("boolean", "<{OPERAND1} = {OPERAND2}>"),
    "operator_and": _spec("boolean", "<{OPERAND1} and {OPERAND2}>", "OPERAND1 OPERAND2"),
    "operator_or": _spec("boolean", "<{OPERAND1} or {OPERAND2}>", "OPERAND1 OPERAND2"),
    "operator_not": _spec("boolean", "<not {OPERAND}>", "OPERAND"),
    "operator_join": _spec("reporter", "(join {STRING1} {STRING2})"),
    "operator_letter_of": _spec("reporter", "(letter {LETTER} of {STRING})"),
    "operator_length": _spec("reporter", "(length of {STRING})"),
    "operator_contains": _spec("boolean", "<{STRING1} contains {STRING2}?>"),
    "operator_mod": _spec("reporter", "({NUM1} mod {NUM2})"),
    "operator_round": _spec("reporter", "(round {NUM})"),
    "operator_mathop": _spec("reporter", "({OPERATOR} of {NUM})"),
    # Variables and lists
    "data_variable": _spec("reporter", "({VARIABLE})"),
    "data_setvariableto": _spec("stack", "set {VARIABLE} to {VALUE}"),
    "data_changevariableby": _spec("stack", "change {VARIABLE} by {VALUE}"),
    "data_showvariable": _spec("stack", "show variable {VARIABLE}"),
    "data_hidevariable": _spec("stack", "hide variable {VARIABLE}"),
    "data_listcontents": _spec("reporter", "({LIST})"),
    "data_addtolist": _spec("stack", "add {ITEM} to {LIST}"),
    "data_deleteoflist": _spec("stack", "delete {INDEX} of {LIST}"),
    "data_deletealloflist": _spec("stack", "delete all of {LIST}"),
    "data_insertatlist": _spec("stack", "insert {ITEM} at {INDEX} of {LIST}"),
    "data_replaceitemoflist": _spec("stack", "replace item {INDEX} of {LIST} with {ITEM}"),
    "data_itemoflist": _spec("reporter", "(item {INDEX} of {LIST})"),
    "data_itemnumoflist": _spec("reporter", "(item # of {ITEM} in {LIST})"),
    "data_lengthoflist": _spec("reporter", "(length of {LIST})"),
    "data_listcontainsitem": _spec("boolean", "<{LIST} contains {ITEM}?>"),
    "data_showlist": _spec("stack", "show list {LIST}"),
    "data_hidelist": _spec("stack", "hide list {LIST}"),
    # Pen
    "pen_clear": _spec("stack", "erase all"),
    "pen_stamp": _spec("stack", "stamp"),
    "pen_penDown": _spec("stack", "pen down"),
    "pen_penUp": _spec("stack", "pen up"),
    "pen_setPenColorToColor": _spec("stack", "set pen color to {COLOR}"),
    "pen_changePenColorParamBy": _spec("stack", "change pen {COLOR_PARAM} by {VALUE}"),
    "pen_setPenColorParamTo": _spec("stack", "set pen {COLOR_PARAM} to {VALUE}"),
    "pen_changePenSizeBy": _spec("stack", "change pen size by {SIZE}"),
    "pen_setPenSizeTo": _spec("stack", "set pen size to {SIZE}"),
    "pen_changePenHueBy": _spec("stack", "change pen color by {HUE}"),
    "pen_setPenHueToNumber": _spec("stack", "set pen color to {HUE}"),
    # Music
    "music_playDrumForBeats": _spec("stack", "play drum {DRUM} for {BEATS} beats"),
    "music_midiPlayDrumForBeats": _spec("stack", "play drum {DRUM} for {BEATS} beats"),
    "music_restForBeats": _spec("stack", "rest for {BEATS} beats"),
    "music_playNoteForBeats": _spec("stack", "play note {NOTE} for {BEATS} beats"),
    "music_setInstrument": _spec("stack", "set instrument to {INSTRUMENT}"),
    "music_midiSetInstrument": _spec("stack", "set instrument to {INSTRUMENT}"),
    "music_setTempo": _spec("stack", "set tempo to {TEMPO}"),
    "music_changeTempo": _spec("stack", "change tempo by {TEMPO}"),
    "music_getTempo": _spec("reporter", "(tempo)"),
}


_PLACEHOLDER = re.compile(r"\{([A-Z][A-Z0-9_]*)\}")
_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_PROC_SPLIT = re.compile(r"(%[sbn])")
_UNSAFE_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_NUMBER_SHADOWS = {
    "math_number",
    "math_positive_number",
    "math_whole_number",
    "math_integer",
    "math_angle",
    "math_slider",
}
_MENU_SPECIAL = {
    "_mouse_": "mouse-pointer",
    "_random_": "random position",
    "_myself_": "myself",
    "_stage_": "Stage",
    "_edge_": "edge",
}
_FIELD_LABELS = {
    "EFFECT": {
        "COLOR": "color",
        "FISHEYE": "fisheye",
        "WHIRL": "whirl",
        "PIXELATE": "pixelate",
        "MOSAIC": "mosaic",
        "BRIGHTNESS": "brightness",
        "GHOST": "ghost",
        "PITCH": "pitch",
        "PAN": "pan left/right",
    },
    "CURRENTMENU": {
        "YEAR": "year",
        "MONTH": "month",
        "DATE": "date",
        "DAYOFWEEK": "day of week",
        "HOUR": "hour",
        "MINUTE": "minute",
        "SECOND": "second",
    },
    "WHENGREATERTHANMENU": {
        "LOUDNESS": "loudness",
        "TIMER": "timer",
    },
}


# ---------------------------------------------------------------------------
# Kitty Python. Everything below turns project.json into .py files that
# `kitty build` turns back into the same project.

class _Unsupported(Exception):
    """A block Kitty has no Python for. The message finishes "Not decompiled, ..."."""


# Expression precedence, lowest first. A child with lower precedence than its
# parent gets parentheses.
_OR, _AND, _NOT, _CMP, _ADD, _MUL, _UNARY, _ATOM = range(1, 9)

# Names the decompiled code uses itself, or Python keywords.
_RESERVED = set(keyword.kwlist) | {
    "kitty", "math", "self", "super", "len", "abs", "round", "range", "list", "tuple", "set", "dict",
    "str", "int", "float", "bool", "print", "enumerate", "zip", "ignore", "Exception", "_",
}
# Kitty skips these file names in a folder build, or gives them a meaning.
_RESERVED_FILES = {"stage", "kitty", "comp", "decomp", "cli"}
_CANONICAL_NUMBER = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d*[1-9])?")
_JS_DECIMAL = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_JS_PREFIXED = re.compile(r"0[xX][0-9a-fA-F]+|0[bB][01]+|0[oO][0-7]+")
_MENU_VALUES = {
    "_mouse_": "mouse-pointer",
    "_random_": "random position",
    "_myself_": "myself",
    "_stage_": "stage",
    "_edge_": "edge",
}
_MATH_CALLS = {
    "abs": "abs", "floor": "kitty.floor", "ceiling": "kitty.ceiling", "sqrt": "kitty.sqrt",
    "sin": "kitty.sin", "cos": "kitty.cos", "tan": "kitty.tan", "asin": "kitty.asin", "acos": "kitty.acos",
    "atan": "kitty.atan", "ln": "kitty.ln", "log": "kitty.log", "e ^": "kitty.exp", "10 ^": "kitty.power10",
}
_BOOLEAN_OPCODES = {
    "operator_gt", "operator_lt", "operator_equals", "operator_and", "operator_or", "operator_not",
    "operator_contains", "data_listcontainsitem", "sensing_touchingobject", "sensing_touchingcolor",
    "sensing_coloristouchingcolor", "sensing_keypressed", "sensing_mousedown", "argument_reporter_boolean",
}
_HATS = {
    "event_whenflagclicked", "event_whenkeypressed", "event_whenthisspriteclicked", "event_whenstageclicked",
    "event_whenbackdropswitchesto", "event_whengreaterthan", "event_whenbroadcastreceived", "control_start_as_clone",
}
# kitty.<name> blocks by opcode. A few opcodes share one block with a fixed field.
_BY_OPCODE = {}
for _name, _block_spec in BLOCKS.items():
    _BY_OPCODE.setdefault(_block_spec.opcode, []).append((_name, _block_spec))
del _name, _block_spec


def _wrap(expr, prec, right=False):
    code, own = expr
    if own < prec or (own == prec and (right or prec == _CMP)):
        return f"({code})"
    return code


def _py_str(text):
    return json.dumps(str(text), ensure_ascii=False)


def _js_number(value):
    """Scratch reads text as JavaScript's Number() does. None means not a number, which Scratch counts as 0."""
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text == "":
        return 0.0
    if text in ("Infinity", "+Infinity"):
        return math.inf
    if text == "-Infinity":
        return -math.inf
    if _JS_DECIMAL.fullmatch(text):
        return float(text)
    if _JS_PREFIXED.fullmatch(text):
        return float(int(text, 0))
    return None


def _number_code(value):
    if math.isinf(value):
        return "kitty.divide(1, 0)" if value > 0 else "kitty.divide(-1, 0)"
    if math.isnan(value):
        return "0"
    if value.is_integer() and abs(value) < 1e16:
        return str(int(value))
    return repr(value)


def _number_literal(raw):
    """A number input's literal. Scratch counts text that is not a number as 0."""
    text = str(raw).strip() if not isinstance(raw, (int, float)) or isinstance(raw, bool) else None
    if text is not None and _CANONICAL_NUMBER.fullmatch(text) and text != "-0":
        code = text
    else:
        number = _js_number(raw)
        code = _number_code(0.0 if number is None else number)
    return code, _UNARY if code.startswith("-") else _ATOM


def _text_literal(raw):
    """A text input's literal. Text that is exactly a number, such as 10 or 2.5, is written as the number."""
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return _number_literal(raw)
    text = "" if raw is None else str(raw)
    if _CANONICAL_NUMBER.fullmatch(text) and text != "-0":
        return text, _UNARY if text.startswith("-") else _ATOM
    return _py_str(text), _ATOM


def _value_literal(value):
    """A declaration's starting value: a number or text literal."""
    if isinstance(value, bool):
        return _py_str("true" if value else "false")
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isinf(number) or math.isnan(number):
            return _py_str(_format_js(number))
        return _number_code(number)
    if value is None:
        return "0"
    if isinstance(value, (list, dict)):
        return _py_str(json.dumps(value))
    return _py_str(value)


def _format_js(number):
    if math.isnan(number):
        return "NaN"
    return "Infinity" if number > 0 else "-Infinity"


def _color_code(raw):
    text = str(raw or "").strip()
    if not text.startswith("#"):
        text = "#" + text
    if len(text) not in (4, 7):
        text = "#000000"
    return _py_str(text.lower()), _ATOM


def _first_field(block):
    fields = block.get("fields") or {}
    if not fields:
        return ""
    value = next(iter(fields.values()))
    if isinstance(value, list):
        return "" if not value or value[0] is None else value[0]
    return "" if value is None else value


def _identifier(text):
    chars = []
    for char in str(text):
        ok = char == "_" or (char.isalnum() and ("a" + char).isidentifier())
        chars.append(char if ok else "_")
    return re.sub(r"_+", "_", "".join(chars)).strip("_")


def _comment_lines(text, pad):
    lines = str(text).splitlines() or [""]
    return [f"{pad}# {line}".rstrip() for line in lines]


class _Names:
    """Python names in one file. Each Scratch name gets a valid identifier that no other name uses."""

    def __init__(self, taken=()):
        self.taken = set(taken)

    def claim(self, text, prefix):
        base = _identifier(text)
        if not base:
            base = prefix
        elif base[0].isdigit():
            base = f"{prefix}_{base}"
        if base in _RESERVED or keyword.iskeyword(base):
            base += "_"
        name = base
        number = 2
        while name in self.taken:
            name = f"{base}_{number}"
            number += 1
        self.taken.add(name)
        return name


class _Item:
    """A variable or list: its Python name, its Scratch name, and how it starts."""

    def __init__(self, py, scratch, value, show, cloud):
        self.py = py
        self.scratch = scratch
        self.value = value
        self.show = show
        self.cloud = cloud

    @property
    def display(self):
        # A leading dot marks Kitty's own hidden names. A rebuild makes those again, so rename these.
        return self.py if self.scratch.startswith(".") or not self.scratch else self.scratch


class _Proc:
    def __init__(self, py, params, warp, define_id):
        self.py = py
        self.params = params
        self.warp = warp
        self.define_id = define_id


class _ProjectWriter:
    def __init__(self, project, archive, source_name):
        self.targets = [item for item in project.get("targets") or [] if isinstance(item, dict)]
        self.stage = next((item for item in self.targets if item.get("isStage")), None)
        self.archive = archive
        self.available = set(archive.namelist())
        self.source_name = source_name
        self.warnings = []
        self.files = {}
        self.assets = {}
        self.used_files = {"Assets": set(), "Sounds": set()}
        self.shown = {
            monitor.get("id") for monitor in project.get("monitors") or []
            if isinstance(monitor, dict) and monitor.get("visible")
        }
        names = _Names()
        self.stage_vars = {}
        self.stage_lists = {}
        if self.stage is not None:
            for vid, entry in (self.stage.get("variables") or {}).items():
                self.stage_vars[vid] = _new_item(names, entry, vid in self.shown, False)
            for lid, entry in (self.stage.get("lists") or {}).items():
                self.stage_lists[lid] = _new_item(names, entry, lid in self.shown, True)
        self.global_names = names.taken

    def build(self):
        used = {"stage"}
        sprites = [item for item in self.targets if not item.get("isStage")]
        if self.stage is not None:
            self.files["stage.py"] = _TargetWriter(self, self.stage, "stage", 0).source().encode("utf-8")
        for index, target in enumerate(sprites, start=1):
            name = str(target.get("name") or "sprite")
            stem = _safe_file_stem(name, "sprite")
            if stem.lower() in _RESERVED_FILES:
                stem += "_sprite"
            candidate = stem
            number = 2
            while candidate.lower() in used:
                candidate = f"{stem}_{number}"
                number += 1
            used.add(candidate.lower())
            layer = target.get("layerOrder") if isinstance(target.get("layerOrder"), int) else index
            source = _TargetWriter(self, target, candidate, layer).source()
            self.files[f"{candidate}.py"] = source.encode("utf-8")
        return self.files

    def asset(self, item, folder):
        """Write a costume or sound file once, and return (relative path, bytes), or None if it is missing."""
        md5ext = item.get("md5ext")
        if not md5ext and item.get("assetId") and item.get("dataFormat"):
            md5ext = f"{item['assetId']}.{item['dataFormat']}"
        key = (folder, md5ext)
        if key in self.assets:
            return self.assets[key]
        if not md5ext or md5ext not in self.available:
            return None
        data = self.archive.read(md5ext)
        ext = str(item.get("dataFormat") or md5ext.rsplit(".", 1)[-1]).lower()
        if ext == "jpeg":
            ext = "jpg"
        stem = _safe_file_stem(item.get("name") or "", "asset")
        used = self.used_files[folder]
        candidate = stem
        number = 2
        while f"{candidate}.{ext}".lower() in used:
            candidate = f"{stem}_{number}"
            number += 1
        used.add(f"{candidate}.{ext}".lower())
        path = f"{folder}/{candidate}.{ext}"
        self.files[path] = data
        self.assets[key] = (path, data)
        return self.assets[key]


def _new_item(names, entry, show, is_list):
    entry = entry if isinstance(entry, list) else [str(entry)]
    scratch = str(entry[0]) if entry else ""
    value = entry[1] if len(entry) > 1 else ([] if is_list else 0)
    cloud = len(entry) > 2 and entry[2] is True
    py = names.claim(scratch.lstrip("."), "items" if is_list else "value")
    return _Item(py, scratch, value, show, cloud)


class _TargetWriter:
    def __init__(self, project, target, file_stem, layer):
        self.project = project
        self.target = target
        self.blocks = target.get("blocks") or {}
        self.is_stage = bool(target.get("isStage"))
        self.name = str(target.get("name") or ("Stage" if self.is_stage else "sprite"))
        self.label = "Stage" if self.is_stage else f"sprite {self.name}"
        self.file_stem = file_stem
        self.layer = layer
        self.names = _Names(project.global_names)
        self.text = _TargetDecompiler(target)
        self.comments = {}
        self.floating = []
        for comment in (target.get("comments") or {}).values():
            if not isinstance(comment, dict):
                continue
            text = str(comment.get("text") or "")
            if comment.get("blockId"):
                self.comments[comment["blockId"]] = text
            elif text.strip():
                self.floating.append(comment)
        if self.is_stage:
            self.vars = project.stage_vars
            self.lists = project.stage_lists
        else:
            self.vars = {}
            self.lists = {}
            for vid, entry in (target.get("variables") or {}).items():
                self.vars[vid] = _new_item(self.names, entry, vid in project.shown, False)
            for lid, entry in (target.get("lists") or {}).items():
                self.lists[lid] = _new_item(self.names, entry, lid in project.shown, True)
        self.used_stage_vars = {}
        self.used_stage_lists = {}
        self.procs = {}
        self.assigned = set()
        self.params = {}
        self.pending = []
        self._collect_procs()

    # -- the file ----------------------------------------------------------

    def source(self):
        order = []
        for index, (block_id, block) in enumerate(self.blocks.items()):
            if isinstance(block, dict) and block.get("topLevel") and not block.get("shadow"):
                order.append((block.get("y") or 0, block.get("x") or 0, index, block_id))
            elif isinstance(block, list):
                order.append((_coord(block, 4), _coord(block, 3), index, block_id))
        order.sort(key=lambda item: item[:3])
        procs = []
        scripts = []
        loose = []
        for _y, _x, _index, block_id in order:
            block = self.blocks[block_id]
            opcode = block.get("opcode") if isinstance(block, dict) else None
            if opcode == "procedures_definition":
                proc = next((item for item in self.procs.values() if item.define_id == block_id), None)
                if proc is not None:
                    procs.append(self._proc_source(proc, block_id, block))
            elif opcode in _HATS or (opcode and "_when" in opcode.lower()):
                scripts.append(self._hat_source(block_id, block))
            else:
                loose.append(block_id)
        functions = procs + scripts
        lines = [f"# {self._title()}, decompiled from {self.project.source_name} by kitty decomp.", "import kitty", ""]
        media = self._media_lines()
        if media:
            lines.extend(media + [""])
        declarations = self._declaration_lines()
        if declarations:
            lines.extend(declarations + [""])
        for function in functions:
            lines.extend(["", function, ""])
        for tail in (self._loose_lines(loose), self._floating_lines()):
            if tail:
                lines.extend([""] + tail)
        while lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines) + "\n"

    def _title(self):
        return "The stage" if self.is_stage else f"Sprite {self.name.strip()}"

    def _warn(self, message):
        self.project.warnings.append(f"{self.label}: {message}")

    def _media_lines(self):
        lines = []
        if not self.is_stage and self.name.strip() != self.file_stem:
            lines.append(f"kitty.sprite_name({_py_str(self.name)})")
        call = "kitty.backdrop" if self.is_stage else "kitty.costume"
        kept = set()
        for costume in self.target.get("costumes") or []:
            line = self._costume_line(call, costume)
            lines.append(line)
            if not line.startswith("#"):
                kept.add(str(costume.get("name") or ""))
        for sound in self.target.get("sounds") or []:
            found = self.project.asset(sound, "Sounds")
            name = str(sound.get("name") or "")
            if found is None:
                self._warn(f"the sound {name!r} is missing from the .sb3 file")
                continue
            path, _data = found
            args = [_py_str(path)]
            if name != PurePosixPath(path).stem:
                args.append(f"name={_py_str(name)}")
            lines.append(f"kitty.sound({', '.join(args)})")
        start = self._start_args(kept)
        if start:
            lines.append(f"kitty.start_with({', '.join(start)})")
        return lines

    def _costume_line(self, call, costume):
        name = str(costume.get("name") or "")
        found = self.project.asset(costume, "Assets")
        if found is None:
            self._warn(f"the costume {name!r} is missing from the .sb3 file")
            return f"# {call}(...)  # {name!r} was missing from the .sb3 file"
        path, data = found
        fmt = PurePosixPath(path).suffix.lstrip(".")
        args = [_py_str(path)]
        if name != PurePosixPath(path).stem:
            args.append(f"name={_py_str(name)}")
        default = None
        if fmt == "svg":
            default = _svg_center(data)
        else:
            try:
                info = _bitmap_info(data)
            except ValueError:
                info = None
            if info is None:
                self._warn(f"the costume {name!r} is a {fmt} file. Save it as png to use it")
                return f"# {call}({', '.join(args)})  # Kitty takes svg, png, or jpg"
            default = (info[1] / 2, info[2] / 2)
            if costume.get("bitmapResolution") == 2:
                args.append("resolution=2")
        center_x = costume.get("rotationCenterX")
        center_y = costume.get("rotationCenterY")
        if isinstance(center_x, (int, float)) and isinstance(center_y, (int, float)):
            if default is None or abs(default[0] - center_x) > 1e-6 or abs(default[1] - center_y) > 1e-6:
                args.append(f"center=({_number_code(float(center_x))}, {_number_code(float(center_y))})")
        return f"{call}({', '.join(args)})"

    def _start_args(self, kept):
        target = self.target
        costumes = target.get("costumes") or []
        args = []

        def number(key, value, default):
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value != default:
                args.append(f"{key}={_number_code(float(value))}")

        current = target.get("currentCostume")
        if isinstance(current, int) and 0 < current < len(costumes):
            name = str(costumes[current].get("name") or "")
            if name in kept:
                key = "backdrop" if self.is_stage else "costume"
                args.append(f"{key}={_py_str(name)}")
        if self.is_stage:
            number("volume", target.get("volume"), 100)
            number("tempo", target.get("tempo"), 60)
            return args
        number("x", target.get("x"), 0)
        number("y", target.get("y"), 0)
        number("direction", target.get("direction"), 90)
        number("size", target.get("size"), 100)
        if target.get("visible") is False:
            args.append("visible=False")
        style = target.get("rotationStyle")
        if isinstance(style, str) and style != "all around":
            args.append(f"rotation_style={_py_str(style)}")
        if target.get("draggable") is True:
            args.append("draggable=True")
        number("volume", target.get("volume"), 100)
        args.append(f"layer={self.layer}")
        return args

    def _declaration_lines(self):
        lines = []
        for item in self.used_stage_vars.values():
            lines.append(f"{item.py} = kitty.variable({_py_str(item.display)}, {_value_literal(item.value)}, shared=True)")
        for item in self.vars.values():
            if item.cloud:
                self._warn(f"the cloud variable {item.scratch!r} is a plain variable in Kitty")
            extra = ", show=True" if item.show else ""
            if item.py == item.display and not extra:
                lines.append(f"{item.py} = {_value_literal(item.value)}")
            else:
                lines.append(f"{item.py} = kitty.variable({_py_str(item.display)}, {_value_literal(item.value)}{extra})")
        for item in self.used_stage_lists.values():
            lines.append(f"{item.py} = kitty.list({_py_str(item.display)}, {self._items(item)}, scratch=True, shared=True)")
        for item in self.lists.values():
            extra = ", show=True" if item.show else ""
            lines.append(f"{item.py} = kitty.list({_py_str(item.display)}, {self._items(item)}, scratch=True{extra})")
        return lines

    def _items(self, item):
        values = item.value if isinstance(item.value, list) else []
        return "[" + ", ".join(_value_literal(value) for value in values) + "]"

    def _loose_lines(self, loose):
        lines = []
        for block_id in loose:
            block = self.blocks[block_id]
            if isinstance(block, list):
                text = [self.text._floating_reporter(block)]
            else:
                text = self.text._chain(block_id, 0)
            if not lines:
                lines.append("# Blocks that are not under a hat block. Scratch never runs them.")
            lines.append("#")
            lines.extend(f"#     {line}".rstrip() for line in text)
        return lines

    def _floating_lines(self):
        lines = []
        for comment in self.floating:
            if not lines:
                lines.append("# Comments from the Scratch workspace:")
            lines.append("#")
            lines.extend(_comment_lines(comment.get("text") or "", ""))
        return lines

    # -- custom blocks and hats --------------------------------------------

    def _collect_procs(self):
        for block_id, block in self.blocks.items():
            if not isinstance(block, dict) or block.get("opcode") != "procedures_definition":
                continue
            proto = self.text._prototype(block)
            mutation = (proto or {}).get("mutation") or {}
            code = mutation.get("proccode")
            if not code or code in self.procs:
                continue
            pieces = _PROC_SPLIT.split(code)
            slots = [piece for piece in pieces if piece in ("%s", "%n", "%b")]
            label = " ".join(piece for piece in pieces if piece not in ("%s", "%n", "%b"))
            py = self.names.claim(label, "block")
            ids = _json_list(mutation.get("argumentids"))
            arg_names = _json_list(mutation.get("argumentnames"))
            param_names = _Names(self.names.taken)
            params = []
            for index, arg_id in enumerate(ids):
                arg_name = str(arg_names[index]) if index < len(arg_names) else f"arg {index + 1}"
                boolean = index < len(slots) and slots[index] == "%b"
                params.append((arg_id, arg_name, param_names.claim(arg_name, "value"), boolean))
            self.procs[code] = _Proc(py, params, _is_warp(mutation), block_id)

    def _proc_source(self, proc, block_id, block):
        self.assigned = set()
        self.params = {}
        for _arg_id, arg_name, py, boolean in proc.params:
            self.params.setdefault(arg_name, py)
        body = self._body_lines(block.get("next"), 0)
        self.params = {}
        lines = _comment_lines(self.comments[block_id], "") if block_id in self.comments else []
        if not proc.warp:
            # Scratch draws the screen between steps of this block.
            lines.append("@kitty.block(warp=False)")
        params = ", ".join(f"{py}: bool" if boolean else py for _arg_id, _name, py, boolean in proc.params)
        lines.append(f"def {proc.py}({params}):")
        return "\n".join(lines + self._globals() + body)

    def _hat_source(self, block_id, block):
        try:
            decorator, stem = self._hat(block)
        except _Unsupported as exc:
            self._warn(str(exc))
            lines = [f"# Not decompiled, {exc}:"]
            lines.extend(f"#     {line}".rstrip() for line in self.text._chain(block_id, 0))
            return "\n".join(lines)
        name = self.names.claim(stem, "script")
        self.assigned = set()
        body = self._body_lines(block.get("next"), 0)
        lines = _comment_lines(self.comments[block_id], "") if block_id in self.comments else []
        lines.extend([decorator, f"def {name}():"])
        return "\n".join(lines + self._globals() + body)

    def _globals(self):
        if not self.assigned:
            return []
        return ["    global " + ", ".join(sorted(self.assigned))]

    def _hat(self, block):
        opcode = block.get("opcode")
        if opcode == "event_whenflagclicked":
            return "@kitty.green_flag", "on_green_flag"
        if opcode == "event_whenkeypressed":
            key = str(self._field(block, "KEY_OPTION"))
            return f"@kitty.when_key({_py_str(key)})", f"on_key_{key}"
        if opcode == "event_whenthisspriteclicked":
            return "@kitty.when_clicked", "on_click"
        if opcode == "event_whenstageclicked":
            return ("@kitty.when_clicked" if self.is_stage else "@kitty.when_stage_clicked"), "on_stage_click"
        if opcode == "event_whenbackdropswitchesto":
            name = str(self._field(block, "BACKDROP"))
            return f"@kitty.when_backdrop({_py_str(name)})", f"on_backdrop_{name}"
        if opcode == "event_whenbroadcastreceived":
            message = str(self._field(block, "BROADCAST_OPTION"))
            return f"@kitty.when_receive({_py_str(message)})", f"on_{message}"
        if opcode == "control_start_as_clone":
            return "@kitty.when_cloned", "on_clone_start"
        if opcode == "event_whengreaterthan":
            kind = "loudness" if str(self._field(block, "WHENGREATERTHANMENU")).upper() == "LOUDNESS" else "timer"
            found, data = self._input(block, "VALUE")
            if found == "lit":
                value = _number_literal(data[1] if len(data) > 1 else 0)[0]
            elif found == "shadow":
                value = _number_literal(_first_field(data))[0]
            else:
                raise _Unsupported(f"a when {kind} > hat with a changing value")
            return f"@kitty.when_{kind}({value})", f"on_{kind}"
        raise _Unsupported(f"the hat block {opcode} has no Kitty decorator")

    # -- statements ----------------------------------------------------------

    def _body_lines(self, block_id, indent):
        lines = self._chain(block_id, indent + 1)
        if not any(not line.strip().startswith("#") for line in lines):
            lines.append("    " * (indent + 1) + "pass")
        return lines

    def _chain(self, block_id, indent):
        lines = []
        seen = set()
        while isinstance(block_id, str) and block_id not in seen:
            seen.add(block_id)
            block = self.blocks.get(block_id)
            if not isinstance(block, dict):
                break
            lines.extend(self._statement(block_id, block, indent))
            block_id = block.get("next")
        return lines

    def _statement(self, block_id, block, indent):
        pad = "    " * indent
        self.pending.append([])
        try:
            try:
                lines = self._statement_lines(block, indent)
            except _Unsupported as exc:
                self._warn(str(exc))
                lines = [f"{pad}# Not decompiled, {exc}:"]
                lines.extend(f"{pad}#     {line}".rstrip() for line in self.text._statement(block_id, block, 0))
            notes = self.pending[-1]
        finally:
            self.pending.pop()
        head = []
        for note in ([self.comments[block_id]] if block_id in self.comments else []) + notes:
            head.extend(_comment_lines(note, pad))
        return head + lines

    def _header(self, render, placeholder, what):
        """Render a C block's condition or count. If Kitty has no Python for it, note it and use the placeholder."""
        try:
            return render()
        except _Unsupported as exc:
            self._warn(str(exc))
            self.pending[-1].append(f"Not decompiled, {exc}. {what} below is a placeholder.")
            return placeholder

    def _statement_lines(self, block, indent):
        opcode = block.get("opcode")
        pad = "    " * indent
        if opcode == "control_repeat":
            count = self._header(lambda: self._number(block, "TIMES"), ("0", _ATOM), "The repeat count")
            return [f"{pad}for _ in range({count[0]}):"] + self._body(block, "SUBSTACK", indent)
        if opcode == "control_forever":
            return [f"{pad}while True:"] + self._body(block, "SUBSTACK", indent)
        if opcode in ("control_if", "control_if_else"):
            return self._if_lines(block, indent, "if")
        if opcode == "control_repeat_until":
            until = self._header(lambda: self._condition(block, "CONDITION"), None, "The loop test")
            test = "False" if until is None else f"not {_wrap(until, _NOT)}"
            return [f"{pad}while {test}:"] + self._body(block, "SUBSTACK", indent)
        if opcode == "control_while":
            test = self._header(lambda: self._condition(block, "CONDITION"), ("False", _ATOM), "The loop test")
            return [f"{pad}while {test[0]}:"] + self._body(block, "SUBSTACK", indent)
        if opcode == "control_for_each":
            var = self._ref_field(block, "VARIABLE", False, assign=True)
            count = self._number(block, "VALUE")
            return [f"{pad}for {var} in range(1, {_wrap(count, _ADD)} + 1):"] + self._body(block, "SUBSTACK", indent)
        if opcode == "control_all_at_once":
            return self._chain(self._substack(block, "SUBSTACK"), indent)
        if opcode == "data_setvariableto":
            value = self._text(block, "VALUE")
            var = self._ref_field(block, "VARIABLE", False, assign=True)
            return [f"{pad}{var} = {value[0]}"]
        if opcode == "data_changevariableby":
            value = self._number(block, "VALUE")
            var = self._ref_field(block, "VARIABLE", False, assign=True)
            if value[1] == _UNARY and value[0].startswith("-"):
                return [f"{pad}{var} -= {value[0][1:]}"]
            return [f"{pad}{var} += {value[0]}"]
        if opcode in _LIST_STATEMENTS:
            return [pad + _LIST_STATEMENTS[opcode](self, block)]
        if opcode == "procedures_call":
            return [pad + self._call(block)]
        found = self._spec(block)
        if found is not None and found[1].shape == "stack":
            name, spec = found
            return [f"{pad}kitty.{name}({', '.join(self._spec_args(block, spec))})"]
        if found is not None and found[1].shape == "c":
            raise _Unsupported(f"the C block {opcode}")
        raise _Unsupported(f"{opcode} has no Kitty block")

    def _if_lines(self, block, indent, keyword_text):
        pad = "    " * indent
        test = self._header(lambda: self._condition(block, "CONDITION"), ("False", _ATOM), "The condition")
        lines = [f"{pad}{keyword_text} {test[0]}:"] + self._body(block, "SUBSTACK", indent)
        if block.get("opcode") != "control_if_else":
            return lines
        other_id = self._substack(block, "SUBSTACK2")
        other = self.blocks.get(other_id) if other_id else None
        if (
            isinstance(other, dict)
            and other.get("opcode") in ("control_if", "control_if_else")
            and not other.get("next")
            and other_id not in self.comments
        ):
            return lines + self._if_lines(other, indent, "elif")
        return lines + [f"{pad}else:"] + self._body(block, "SUBSTACK2", indent)

    def _body(self, block, name, indent):
        return self._body_lines(self._substack(block, name), indent)

    def _substack(self, block, name):
        return _input_block_id((block.get("inputs") or {}).get(name))

    def _call(self, block):
        mutation = block.get("mutation") or {}
        code = mutation.get("proccode")
        proc = self.procs.get(code)
        if proc is None:
            raise _Unsupported(f"a call to the custom block {code!r}, which has no define block")
        inputs = block.get("inputs") or {}
        call_ids = _json_list(mutation.get("argumentids"))
        args = []
        for index, (arg_id, _name, _py, boolean) in enumerate(proc.params):
            key = arg_id if arg_id in inputs or index >= len(call_ids) else call_ids[index]
            args.append((self._condition(block, key) if boolean else self._text(block, key))[0])
        return f"{proc.py}({', '.join(args)})"

    # -- inputs ----------------------------------------------------------------

    def _input(self, block, name):
        """What fills an input: ("empty", None), ("lit", primitive), ("shadow", block),
        ("block", id), ("var", [12, name, id]), or ("list", [13, name, id])."""
        value = (block.get("inputs") or {}).get(name)
        if not isinstance(value, list) or len(value) < 2 or value[1] is None:
            return "empty", None
        payload = value[1]
        if isinstance(payload, str):
            payload = self.blocks.get(payload, payload)
            if isinstance(payload, dict):
                return ("shadow", payload) if payload.get("shadow") else ("block", value[1])
        if isinstance(payload, list) and payload:
            if payload[0] == 12:
                return "var", payload
            if payload[0] == 13:
                return "list", payload
            return "lit", payload
        return "empty", None

    def _value(self, found, data):
        if found == "var":
            return self._ref(data[1], data[2] if len(data) > 2 else None, False), _ATOM
        if found == "list":
            return f'kitty.join({self._ref(data[1], data[2] if len(data) > 2 else None, True)}, "")', _ATOM
        return self._reporter(data)

    def _number(self, block, name):
        found, data = self._input(block, name)
        if found == "empty":
            return "0", _ATOM
        if found == "lit":
            return _number_literal(data[1] if len(data) > 1 else "")
        if found == "shadow":
            return _number_literal(_first_field(data))
        return self._value(found, data)

    def _text(self, block, name):
        found, data = self._input(block, name)
        if found == "empty":
            return '""', _ATOM
        if found == "lit":
            if data[0] == 9:
                return _color_code(data[1] if len(data) > 1 else "")
            return _text_literal(data[1] if len(data) > 1 else "")
        if found == "shadow":
            return _text_literal(_first_field(data))
        return self._value(found, data)

    def _condition(self, block, name):
        found, data = self._input(block, name)
        if found == "empty":
            return "False", _ATOM
        if found != "block":
            raise _Unsupported("a round value in a condition slot")
        target = self.blocks.get(data)
        if not isinstance(target, dict) or target.get("opcode") not in _BOOLEAN_OPCODES:
            raise _Unsupported("a round value in a condition slot")
        return self._reporter(data)

    def _menu(self, block, name):
        found, data = self._input(block, name)
        if found == "empty":
            return '""', _ATOM
        if found == "shadow":
            value = str(_first_field(data))
            return _py_str(_MENU_VALUES.get(value, value)), _ATOM
        if found == "lit":
            return _py_str(data[1] if len(data) > 1 else ""), _ATOM
        return self._value(found, data)

    def _color(self, block, name):
        found, data = self._input(block, name)
        if found == "empty":
            return '"#000000"', _ATOM
        if found == "lit":
            return _color_code(data[1] if len(data) > 1 else "")
        if found == "shadow":
            return _color_code(_first_field(data))
        return self._value(found, data)

    def _field(self, block, name):
        """A dropdown's chosen value, from a field or from the menu block in an input."""
        value = (block.get("fields") or {}).get(name)
        if value is not None:
            return value[0] if isinstance(value, list) and value else value
        found, data = self._input(block, name)
        if found == "shadow":
            return _first_field(data)
        if found == "lit":
            return data[1] if len(data) > 1 else ""
        if found == "empty":
            return ""
        raise _Unsupported(f"a changing {name.lower()} menu")

    def _ref_field(self, block, name, is_list, assign=False):
        value = (block.get("fields") or {}).get(name) or ["", None]
        return self._ref(value[0], value[1] if len(value) > 1 else None, is_list, assign)

    def _ref(self, name, ident, is_list, assign=False):
        """The Python name of a variable or list. Scratch finds it by id first, then by name."""
        own = self.lists if is_list else self.vars
        stage = self.project.stage_lists if is_list else self.project.stage_vars
        used = self.used_stage_lists if is_list else self.used_stage_vars
        item = own.get(ident)
        if item is None and not self.is_stage and ident in stage:
            item = used.setdefault(ident, stage[ident])
        if item is None:
            item = next((each for each in own.values() if each.scratch == name), None)
        if item is None and not self.is_stage:
            for key, each in stage.items():
                if each.scratch == name:
                    item = used.setdefault(key, each)
                    break
        if item is None:
            # Scratch makes a missing variable when it loads the project. Kitty declares it.
            key = ident or f"missing {name}"
            item = own[key] = _new_item(self.names, [str(name), [] if is_list else 0], False, is_list)
        if assign and not is_list:
            self.assigned.add(item.py)
        return item.py

    def _broadcast(self, block, name):
        found, data = self._input(block, name)
        if found == "lit":
            return data[1] if len(data) > 1 else ""
        if found == "shadow":
            return _first_field(data)
        if found == "empty":
            return ""
        raise _Unsupported("a broadcast whose message changes")

    # -- kitty.<name>(...) blocks ----------------------------------------------

    def _spec(self, block):
        choices = _BY_OPCODE.get(block.get("opcode"))
        if not choices:
            return None
        for name, spec in choices:
            if all(str(self._field(block, field)).lower() == str(raw).lower() for field, raw in spec.fixed_fields):
                return name, spec
        return choices[0]

    def _spec_args(self, block, spec):
        return [self._slot(block, param[1], param[2])[0] for param in spec.params]

    def _slot(self, block, scratch, slot):
        if slot in ("number", "positive", "whole", "integer", "angle"):
            return self._number(block, scratch)
        if slot == "text":
            return self._text(block, scratch)
        if slot == "boolean":
            return self._condition(block, scratch)
        if slot == "color":
            return self._color(block, scratch)
        if slot.startswith("menu:"):
            return self._menu(block, scratch)
        if slot.startswith("field:"):
            value = str(self._field(block, scratch))
            kind = slot.split(":", 1)[1]
            if kind in ("effect", "sound_effect", "current"):
                value = value.lower()
            elif kind == "stop" and value.startswith("other scripts"):
                value = "other scripts"
            return _py_str(value), _ATOM
        if slot == "variable":
            return self._ref_field(block, scratch, False), _ATOM
        if slot == "list":
            return self._ref_field(block, scratch, True), _ATOM
        if slot == "broadcast_input":
            return _py_str(self._broadcast(block, scratch)), _ATOM
        raise _Unsupported(f"the {slot} input of {block.get('opcode')}")

    # -- reporters ---------------------------------------------------------------

    def _reporter(self, block_id):
        block = self.blocks.get(block_id)
        if isinstance(block, list) and block:
            if block[0] in (12, 13):
                return self._value("var" if block[0] == 12 else "list", block)
            return _text_literal(block[1] if len(block) > 1 else "")
        if not isinstance(block, dict):
            raise _Unsupported("a block that is missing from the project")
        if block_id in self.comments and self.pending:
            self.pending[-1].append(self.comments[block_id])
        opcode = block.get("opcode")
        if opcode == "data_variable":
            return self._ref_field(block, "VARIABLE", False), _ATOM
        if opcode == "data_listcontents":
            return f'kitty.join({self._ref_field(block, "LIST", True)}, "")', _ATOM
        if opcode in ("argument_reporter_string_number", "argument_reporter_boolean"):
            name = str(self._field(block, "VALUE"))
            if name in self.params:
                return self.params[name], _ATOM
            return ("False" if opcode == "argument_reporter_boolean" else "0"), _ATOM
        if opcode in _ARITHMETIC:
            symbol, prec, call = _ARITHMETIC[opcode]
            left = self._number(block, "NUM1")
            right = self._number(block, "NUM2")
            if call and right[0] in ("0", "0.0"):
                # Kitty works out literal arithmetic while it compiles, and x / 0 would stop the build.
                return f"kitty.{call}({left[0]}, {right[0]})", _ATOM
            return f"{_wrap(left, prec)} {symbol} {_wrap(right, prec, right=True)}", prec
        if opcode in _COMPARE:
            left = self._text(block, "OPERAND1")
            right = self._text(block, "OPERAND2")
            return f"{_wrap(left, _CMP)} {_COMPARE[opcode]} {_wrap(right, _CMP, right=True)}", _CMP
        if opcode in ("operator_and", "operator_or"):
            prec = _AND if opcode == "operator_and" else _OR
            word = "and" if opcode == "operator_and" else "or"
            left = self._condition(block, "OPERAND1")
            right = self._condition(block, "OPERAND2")
            return f"{_wrap(left, prec)} {word} {_wrap(right, prec, right=True)}", prec
        if opcode == "operator_not":
            return f"not {_wrap(self._condition(block, 'OPERAND'), _NOT)}", _NOT
        if opcode == "operator_join":
            return f"kitty.join({self._text(block, 'STRING1')[0]}, {self._text(block, 'STRING2')[0]})", _ATOM
        if opcode == "operator_letter_of":
            return f"kitty.letter({self._number(block, 'LETTER')[0]}, {self._text(block, 'STRING')[0]})", _ATOM
        if opcode == "operator_length":
            return f"len({self._text(block, 'STRING')[0]})", _ATOM
        if opcode == "operator_contains":
            text = self._text(block, "STRING1")
            part = self._text(block, "STRING2")
            return f"{_wrap(part, _CMP)} in {_wrap(text, _CMP, right=True)}", _CMP
        if opcode == "operator_round":
            return f"round({self._number(block, 'NUM')[0]})", _ATOM
        if opcode == "operator_mathop":
            operation = str(self._field(block, "OPERATOR")).lower()
            if operation not in _MATH_CALLS:
                raise _Unsupported(f"the math operation {operation!r}")
            return f"{_MATH_CALLS[operation]}({self._number(block, 'NUM')[0]})", _ATOM
        if opcode in _LIST_REPORTERS:
            return _LIST_REPORTERS[opcode](self, block)
        found = self._spec(block)
        if found is not None and found[1].shape in ("reporter", "boolean"):
            name, spec = found
            return f"kitty.{name}({', '.join(self._spec_args(block, spec))})", _ATOM
        raise _Unsupported(f"{opcode} has no Kitty block")

    # -- lists. Scratch counts items from 1, and Kitty's Python from 0. ------------

    def _index(self, block):
        """("menu", "last"/"all"/"random"), ("number", n), or ("expr", code for the Python index)."""
        found, data = self._input(block, "INDEX")
        raw = None
        if found == "lit":
            raw = data[1] if len(data) > 1 else ""
        elif found == "shadow":
            raw = _first_field(data)
        elif found == "empty":
            raw = ""
        if raw is not None:
            text = str(raw).strip()
            if text in ("last", "all", "random"):
                return "menu", text
            number = _js_number(text)
            return "number", math.floor(number) if number is not None and math.isfinite(number) else 0
        if found == "block":
            target = self.blocks.get(data)
            if isinstance(target, dict) and target.get("opcode") == "operator_add":
                # item (i + 1) of list is items[i].
                for one, other in (("NUM1", "NUM2"), ("NUM2", "NUM1")):
                    side, side_data = self._input(target, one)
                    literal = side_data[1] if side == "lit" and len(side_data) > 1 else (
                        _first_field(side_data) if side == "shadow" else None)
                    if literal is not None and _js_number(literal) == 1:
                        return "expr", self._number(target, other)[0]
        return "expr", f"{_wrap(self._value(found, data), _ADD)} - 1"

    def _list_add(self, block):
        return f"{self._ref_field(block, 'LIST', True)}.append({self._text(block, 'ITEM')[0]})"

    def _list_delete(self, block):
        items = self._ref_field(block, "LIST", True)
        kind, index = self._index(block)
        if kind == "menu":
            return {"all": f"{items}.clear()", "last": f"{items}.pop()"}.get(index, f'kitty.delete("random", {items})')
        if kind == "number":
            if index < 1:
                return f"pass  # delete item {index} of {items}: Scratch has no item there"
            return f"{items}.pop({index - 1})"
        return f"{items}.pop({index})"

    def _list_insert(self, block):
        items = self._ref_field(block, "LIST", True)
        item = self._text(block, "ITEM")[0]
        kind, index = self._index(block)
        if kind == "menu":
            if index == "last":
                return f"{items}.append({item})"
            if index == "random":
                return f'kitty.insert({item}, "random", {items})'
            return f"pass  # insert at all of {items}: Scratch skips this"
        if kind == "number":
            if index < 1:
                return f"pass  # insert at {index} of {items}: Scratch skips this"
            return f"{items}.insert({index - 1}, {item})"
        return f"{items}.insert({index}, {item})"

    def _list_replace(self, block):
        items = self._ref_field(block, "LIST", True)
        item = self._text(block, "ITEM")[0]
        kind, index = self._index(block)
        if kind == "menu":
            if index == "all":
                return f"pass  # replace item all of {items}: Scratch skips this"
            return f"kitty.replace({_py_str(index)}, {items}, {item})"
        if kind == "number":
            if index < 1:
                return f"pass  # replace item {index} of {items}: Scratch has no item there"
            return f"{items}[{index - 1}] = {item}"
        return f"{items}[{index}] = {item}"

    def _list_item(self, block):
        items = self._ref_field(block, "LIST", True)
        kind, index = self._index(block)
        if kind == "menu":
            return ('""', _ATOM) if index == "all" else (f"kitty.item_of({_py_str(index)}, {items})", _ATOM)
        if kind == "number":
            return ('""', _ATOM) if index < 1 else (f"{items}[{index - 1}]", _ATOM)
        return f"{items}[{index}]", _ATOM

    def _list_item_number(self, block):
        items = self._ref_field(block, "LIST", True)
        return f"{items}.index({self._text(block, 'ITEM')[0]}) + 1", _ADD

    def _list_length(self, block):
        return f"len({self._ref_field(block, 'LIST', True)})", _ATOM

    def _list_contains(self, block):
        item = self._text(block, "ITEM")
        return f"{_wrap(item, _CMP)} in {self._ref_field(block, 'LIST', True)}", _CMP


_LIST_STATEMENTS = {
    "data_addtolist": _TargetWriter._list_add,
    "data_deleteoflist": _TargetWriter._list_delete,
    "data_deletealloflist": lambda writer, block: f"{writer._ref_field(block, 'LIST', True)}.clear()",
    "data_insertatlist": _TargetWriter._list_insert,
    "data_replaceitemoflist": _TargetWriter._list_replace,
}
_LIST_REPORTERS = {
    "data_itemoflist": _TargetWriter._list_item,
    "data_itemnumoflist": _TargetWriter._list_item_number,
    "data_lengthoflist": _TargetWriter._list_length,
    "data_listcontainsitem": _TargetWriter._list_contains,
}
# opcode: (Python operator, precedence, kitty block to use when dividing by a literal 0)
_ARITHMETIC = {
    "operator_add": ("+", _ADD, None),
    "operator_subtract": ("-", _ADD, None),
    "operator_multiply": ("*", _MUL, None),
    "operator_divide": ("/", _MUL, "divide"),
    "operator_mod": ("%", _MUL, "mod"),
}
_COMPARE = {"operator_gt": ">", "operator_lt": "<", "operator_equals": "=="}


def _coord(block, index):
    if len(block) > index and isinstance(block[index], (int, float)):
        return block[index]
    return 0


def main(source=None, folder=None):
    import sys

    if source is None:
        if len(sys.argv) < 2:
            print("usage: kitty decomp <file.sb3> [folder]", file=sys.stderr)
            return 2
        source = sys.argv[1]
        folder = sys.argv[2] if len(sys.argv) > 2 else None
    warnings = []
    try:
        result = decomp(source, folder, warnings)
    except (FileNotFoundError, FileExistsError, ValueError, zipfile.BadZipFile) as exc:
        print(exc, file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(result)
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
