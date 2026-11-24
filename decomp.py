"""Decompile a Scratch 3 .sb3 file into a folder tree.

An .sb3 file is a zip archive. The program lives in project.json as a graph of
blocks. Running this module from the command line writes one folder per stage
or sprite, with that target's script next to its costumes and sounds.

    kitty decompile Fishing.sb3
    py -m kitty decompile Fishing.sb3
    py -m kitty decompile Fishing.sb3 output_folder
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path


def decomp(target, optional_directory=None):
    """Decompile a Scratch .sb3 file into a folder tree.

    target: path to the .sb3 file.
    optional_directory: folder to write. When omitted, the tree is created
        next to the .sb3 file, named after it (Fishing.sb3 becomes Fishing/).

    The tree looks like this:
        project.txt
        Stage/script.txt
        Stage/costumes/...
        Stage/sounds/...
        SpriteName/script.txt
        SpriteName/costumes/...
        SpriteName/sounds/...

    Returns the output directory.
    """
    path = Path(target)
    if not path.is_file():
        raise FileNotFoundError(f"Scratch file not found: {path}")

    directory = Path(optional_directory) if optional_directory is not None else _default_directory(path)
    with zipfile.ZipFile(path) as archive:
        try:
            raw = archive.read("project.json")
        except KeyError as exc:
            raise ValueError(f"{path} is not a Scratch .sb3 file (no project.json)") from exc
        project = json.loads(raw.decode("utf-8"))
        text, sections = _render_project(project, path.name)
        _write_output(archive, project, text, sections, directory)
    return directory


def _default_directory(path):
    directory = path.with_suffix("")
    if directory.exists() and not directory.is_dir():
        directory = path.with_name(path.stem + "_decompiled")
    return directory


def _write_output(archive, project, text, sections, directory):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "project.txt").write_text(text, encoding="utf-8")
    available = set(archive.namelist())
    used_names = {}
    targets = project.get("targets") or []
    for target, (name, section) in zip(targets, sections):
        folder_name = "Stage" if target.get("isStage") else _safe_name(name)
        folder = directory / _unique_stem(used_names, folder_name)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "script.txt").write_text(section, encoding="utf-8")
        _extract_target_assets(archive, available, target, folder)


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


def _safe_name(name):
    cleaned = _UNSAFE_FILENAME.sub("_", str(name)).strip(" .")
    return cleaned or "untitled"


def _unique_stem(used, stem):
    count = used.get(stem, 0) + 1
    used[stem] = count
    if count == 1:
        return stem
    return f"{stem}_{count}"


def _extract_target_assets(archive, available, target, folder):
    for key in ("costumes", "sounds"):
        used = {}
        destination = folder / key
        for item in target.get(key) or []:
            md5ext = item.get("md5ext")
            if not md5ext:
                asset_id = item.get("assetId")
                fmt = item.get("dataFormat")
                if asset_id and fmt:
                    md5ext = f"{asset_id}.{fmt}"
            if not md5ext or md5ext not in available:
                continue
            destination.mkdir(parents=True, exist_ok=True)
            ext = item.get("dataFormat") or md5ext.rsplit(".", 1)[-1]
            filename = _unique_stem(used, _safe_name(item.get("name") or "asset")) + f".{ext}"
            (destination / filename).write_bytes(archive.read(md5ext))


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


def main(source=None, folder=None):
    if source is None:
        import sys
        if len(sys.argv) < 2:
            print("usage: py -m kitty decompile <file.sb3> [directory]", file=sys.stderr)
            return 2
        source = sys.argv[1]
        folder = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        print(decomp(source, folder))
        return 0
    except (FileNotFoundError, ValueError, zipfile.BadZipFile) as exc:
        import sys
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
