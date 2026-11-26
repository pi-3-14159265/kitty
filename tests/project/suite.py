"""One green-flag script. Click the flag in Scratch.

The suite sprite says FAIL and the check name when something is wrong.
Each failed name is also added to the Scratch list "failed tests", which
stays on the screen. A row looks like "lists alias0": the first word is
the group in this file, and the rest is the check.
It finishes with passed N, then failed 0.

Keep the calls at the bottom. A statement between defs becomes a second
green-flag script, and the two scripts run at the same time.
"""

import kitty
import math
from math import sin

passed = 0
failed = 0
area = ""
score = 0
failed_tests = kitty.list("failed tests", [], show=True, scratch=True)
pristine = [4, 5, 6]
box = [1, 2]
got_message = 0
clones = kitty.variable("clones", 0, shared=True)
polls = 0


def expect(name, ok: bool):
    global passed, failed
    if ok:
        passed += 1
    else:
        failed += 1
        failed_tests.append(area + " " + name)
        kitty.say("FAIL " + name)
        kitty.wait(0.7)


def expect_near(name, got, want):
    gap = got - want
    if gap < 0:
        gap = 0 - gap
    expect(name, gap < 0.05)


def run_values():
    global score, area
    area = "values"
    score = 1
    score += 1
    score *= 3
    score //= 4
    expect("add", score == 1)
    score = 7
    score %= 4
    expect("mod aug", score == 3)
    score /= 2
    expect_near("div aug", score, 1.5)
    expect("floor", 7 // 2 == 3)
    expect("mod", 7 % 2 == 1)
    expect_near("div", 7 / 2, 3.5)
    expect("join", "Hello " + "Ada" == "Hello Ada")
    expect("lt", 1 < 2)
    expect("gt", 3 > 2)
    expect("le", 2 <= 2)
    expect("ge", 2 >= 2)
    expect("eq", 2 == 2)
    expect("ne", 2 != 3)
    mark = 0
    if 1 < 2 and 4 > 3:
        mark = 1
    expect("and", mark == 1)
    mark = 0
    if 1 > 2 or 3 > 1:
        mark = 1
    expect("or", mark == 1)
    mark = 0
    if not 1 > 2:
        mark = 1
    expect("not", mark == 1)
    mark = 0
    if 1 > 2:
        mark = 1
    elif 2 > 1:
        mark = 2
    else:
        mark = 3
    expect("elif", mark == 2)
    choice = 4 if 1 < 2 else 5
    expect("if exp", choice == 4)
    expect("abs", abs(-3) == 3)
    expect("round", round(1.6) == 2)
    expect_near("sin0", sin(0), 0)
    expect_near("sin", math.sin(math.pi / 2), 1)
    expect_near("ksin", kitty.sin(90), 1)
    expect_near("cos", math.cos(0), 1)
    expect_near("tan", math.tan(math.pi / 4), 1)
    expect_near("asin", math.asin(1), math.pi / 2)
    expect("sqrt", math.sqrt(9) == 3)
    expect("floorf", math.floor(1.8) == 1)
    expect("ceil", math.ceil(1.2) == 2)
    expect_near("log10", math.log10(100), 2)
    expect_near("log", math.log(math.e), 1)
    expect_near("exp", math.exp(1), math.e)
    expect("pi", math.pi > 3)
    expect("e", math.e > 2)
    expect("fstr", f"n={3}" == "n=3")


def counted(n):
    global polls
    polls += 1
    return n < 3


def ready():
    global polls
    polls += 1
    return polls > 2


def run_loops():
    global area, polls
    area = "loops"
    i = 5
    for i in range(0):
        pass
    expect("empty keep", i == 5)
    for i in range(3, 3):
        pass
    expect("empty same", i == 5)
    for i in range(5, 1):
        pass
    expect("empty down", i == 5)
    for i in range(3):
        pass
    expect("range end", i == 2)
    for i in range(1, 4):
        pass
    expect("range from", i == 3)
    for i in range(10, 0, -2):
        pass
    expect("range step", i == 2)
    total = 0
    for _ in range(4):
        total += 1
    expect("underscore", total == 4)
    total = 0
    for n in range(10):
        if n == 2:
            continue
        if n == 5:
            break
        total += n
    expect("break", total == 8)
    n = 0
    while n < 3:
        n += 1
    expect("while", n == 3)
    n = 0
    with kitty.repeat(4):
        n += 1
    expect("repeat", n == 4)
    n = 0
    with kitty.repeat_until(n == 3):
        n += 1
    expect("until", n == 3)
    n = 0
    with kitty.if_(1 < 2):
        n = 1
    expect("with if", n == 1)
    # A loop test that runs blocks first (in, a custom block call) is worked
    # out again on every pass. The n bound stops a regression from hanging.
    found = ["a"]
    n = 0
    while "z" not in found and n < 5:
        found.append("z")
        n += 1
    expect("while in", n == 1)
    n = 8
    while not big(n) and n < 20:
        n += 1
    expect("while call", n == 11)
    found = ["a"]
    n = 0
    with kitty.repeat_until("z" in found or n > 4):
        found.append("z")
        n += 1
    expect("until in", n == 1)
    polls = 0
    n = 0
    while counted(n):
        n += 1
        if n == 2:
            break
    expect("break skips test", polls == 2)
    polls = 0
    start = kitty.timer()
    # The time limit stops a regression from hanging; a slow build may need several seconds.
    kitty.wait_until(ready() or kitty.timer() > start + 10)
    expect("wait call", polls == 3)


def run_text():
    global area
    area = "text"
    word = "Hello"
    expect("letter", word[0] == "H")
    expect("letter end", word[-1] == "o")
    expect("text slice", word[1:4] == "ell")
    expect("text len", len(word) == 5)
    expect("upper", word.upper() == "HELLO")
    expect("lower", word.lower() == "hello")
    expect("strip", "  hi ".strip() == "hi")
    expect("lstrip", "  hi".lstrip() == "hi")
    expect("rstrip", "hi  ".rstrip() == "hi")
    expect("split", "a-b".split("-")[0] == "a")
    expect("join", "-".join(["a", "b"]) == "a-b")
    expect("replace", "cater".replace("cat", "dog") == "doger")
    expect("find", "cater".find("at") == 1)
    expect("find miss", "zzz".find("at") == -1)
    expect("count", "banana".count("a") == 3)
    mark = 0
    if word.startswith("He") and word.endswith("o"):
        mark = 1
    expect("starts", mark == 1)
    mark = 0
    if "12".isdigit() and "ab".isalpha():
        mark = 1
    expect("digit", mark == 1)
    expect("kitty letter", kitty.letter(2, word) == "e")


def run_lists():
    global area
    area = "lists"
    expect("seed0", pristine[0] == 4)
    expect("seed len", len(pristine) == 3)
    items = [1, 2]
    same = items
    same.append(3)
    expect("alias0", items[0] == 1)
    expect("alias2", items[2] == 3)
    expect("neg", items[-1] == 3)
    expect("last", items["last"] == 3)
    expect("index", items.index(2) == 1)
    expect("index miss", items.index(9) == -1)
    items += [4]
    expect("iadd", items[3] == 4)
    more = [6]
    items.extend(more)
    expect("extend", items[4] == 6)
    items.insert(0, 0)
    expect("insert", items[0] == 0)
    items.remove(2)
    expect("remove", items[2] == 3)
    gone = items.pop(0)
    expect("pop0", gone == 0)
    gone = items.pop()
    expect("pop", gone == 6)
    mark = 0
    if 3 in items and 2 not in items:
        mark = 1
    expect("in list", mark == 1)
    expect("length", kitty.length(items) == len(items))
    mark = 0
    if kitty.contains(items, 3):
        mark = 1
    expect("contains", mark == 1)
    copy = items[:]
    copy.append(7)
    expect("copy old", items[-1] != 7)
    expect("copy new", copy[-1] == 7)
    part = items[0:2]
    expect("part", part[0] == items[0])
    back = [1, 2, 3, 4]
    rev = back[::-1]
    expect("rev", rev[0] == 4)
    stepped = back[0:4:2]
    expect("step0", stepped[0] == 1)
    expect("step1", stepped[1] == 3)
    fresh = list(back)
    fresh.append(9)
    expect("list()", back[3] == 4)
    expect("list new", fresh[4] == 9)
    items = [9]
    expect("rebind", items[0] == 9)
    expect("old same", same[0] == 1 and same[-1] == 4)
    empty = []
    empty.append(1)
    expect("empty add", empty[0] == 1)
    counts = [1, 2, 3]
    doubled = [n * 2 for n in counts if n != 2]
    expect("comp0", doubled[0] == 2)
    expect("comp1", doubled[1] == 6)
    expect("comp len", len(doubled) == 2)
    total_i = 0
    total_v = 0
    for i, item in enumerate(counts):
        total_i += i
        total_v += item
    expect("enum i", total_i == 3)
    expect("enum v", total_v == 6)
    left = [1, 2, 3]
    right = [10, 20]
    pairs = 0
    total = 0
    for a, b in zip(left, right):
        pairs += 1
        total += a + b
    expect("zip n", pairs == 2)
    expect("zip sum", total == 33)
    items.clear()
    expect("clear", len(items) == 0)


def run_module_list():
    global box, area
    area = "module"
    box = [1, 2]
    alias = box
    alias.append(3)
    expect("mod alias", box[2] == 3)
    box = [9]
    expect("mod new", box[0] == 9)
    expect("mod old", alias[2] == 3)


def grow(items):
    items.append(4)


def make_list():
    items = []
    items.append(1)
    return items


def build(n):
    if n == 0:
        items = []
        return items
    items = build(n - 1)
    items.append(n)
    return items


def run_list_calls():
    global area
    area = "calls"
    a = [1]
    grow(a)
    expect("grow0", a[0] == 1)
    expect("grow1", a[1] == 4)
    first = make_list()
    second = make_list()
    first.append(2)
    expect("made len", len(first) == 2)
    expect("made item", first[1] == 2)
    expect("other len", len(second) == 1)
    expect("other item", second[0] == 1)
    built = build(3)
    expect("build len", len(built) == 3)
    expect("build0", built[0] == 1)
    expect("build2", built[2] == 3)


def paint(grid):
    grid[0][1] = 8


def run_grids():
    global area
    area = "grids"
    grid = [
        [1, 2],
        [3, 4],
    ]
    other = grid
    other[0][1] = 9
    expect("grid share", grid[0][1] == 9)
    expect("grid len", len(grid) == 2)
    expect("row len", len(grid[0]) == 2)
    expect("grid neg", grid[-1][-1] == 4)
    grid = [[0, 0], [0, 0]]
    expect("grid old", other[0][1] == 9)
    expect("grid new", grid[0][0] == 0)
    board = [[1, 2], [3, 4]]
    paint(board)
    expect("paint", board[0][1] == 8)
    wide = [
        [1, 2, 3],
        [4, 5, 6],
    ]
    other = [[1, 2], [3, 4]]
    other = wide
    expect("wide", other[1][2] == 6)
    expect("wide len", len(other[0]) == 3)
    space = [
        [[1, 2], [3, 4]],
        [[5, 6], [7, 8]],
    ]
    expect("space", space[1][0][1] == 6)
    expect("space comma", space[1, 0, 1] == 6)
    expect("space len", len(space[0][0]) == 2)


def run_dicts():
    global area
    area = "dicts"
    scores = {"ada": 3}
    other = scores
    other["ada"] = 9
    expect("dict share", scores["ada"] == 9)
    scores = {}
    expect("dict new", other["ada"] == 9)
    scores["ada"] = 3
    scores["bea"] = 5
    scores["ada"] = 9
    expect("dict set", scores["ada"] == 9)
    expect("get", scores.get("nope", 0) == 0)
    expect("get hit", scores.get("bea") == 5)
    scores.update({"bea": 4, "cy": 1})
    expect("update", scores["bea"] == 4)
    expect("update keep", scores["ada"] == 9)
    gone = scores.pop("ada")
    expect("dict pop", gone == 9)
    mark = 0
    if "bea" in scores and "ada" not in scores:
        mark = 1
    expect("dict in", mark == 1)
    total = 0
    count = 0
    for name in scores:
        total += scores[name]
        count += 1
    expect("dict n", count == 2)
    expect("dict sum", total == 5)
    expect("dict len", len(scores) == 2)
    scores.clear()
    expect("dict clear", len(scores) == 0)


def run_try():
    global area
    area = "try"
    seen = ""
    try:
        raise Exception("missing")
    except Exception as problem:
        seen = problem
    else:
        seen = "else"
    finally:
        seen = seen + "!"
    expect("raise", seen == "missing!")
    seen = ""
    try:
        seen = "ok"
    except Exception:
        seen = "bad"
    else:
        seen = seen + "else"
    finally:
        seen = seen + "!"
    expect("try else", seen == "okelse!")


def run_tuples_sets():
    global area
    area = "tuples"
    point = (3, 4)
    x, y = point
    expect("tuple", x == 3)
    expect("tuple y", y == 4)
    x, y = y, x
    expect("swap", x == 4)
    expect("swap y", y == 3)
    point = (0, 1)
    expect("tuple re", point[0] == 0)
    made = tuple([8, 9])
    expect("tuple()", made[1] == 9)
    seen = {1, 2}
    seen.add(2)
    seen.add(3)
    seen.discard(1)
    expect("set len", len(seen) == 2)
    mark = 0
    if 3 in seen and 1 not in seen:
        mark = 1
    expect("set in", mark == 1)
    seen.remove(2)
    expect("set remove", len(seen) == 1)
    seen.add(4)
    seen.pop()
    expect("set pop", len(seen) == 1)
    seen.clear()
    expect("set clear", len(seen) == 0)
    raw = [1, 1, 2]
    bag = set(raw)
    expect("set()", len(bag) == 2)
    folded = {n for n in raw}
    expect("set comp", len(folded) == 2)


def clamp(n):
    if n < 0:
        return 0
    if n > 10:
        return 10
    return n


def factorial(n):
    if n < 2:
        return 1
    return n * factorial(n - 1)


def pair(n):
    return n, n + 1


def nest(n):
    local = n
    if n == 0:
        return local
    return nest(n - 1) + local


def greet(name="ada", times=2):
    return name


def greet_times(name="ada", times=2):
    return times


def total(first, *args):
    result = first
    for item in args:
        result += item
    return result


last_note = ""


def show_extra(n=1, **kwargs):
    global last_note
    last_note = kwargs["note"]
    return n


def missing_kw(**kwargs):
    return kwargs["nope"]


def greet_loud(name, *args, loud=False):
    if loud:
        return 1
    return 0


def outer(n):
    def inner(x):
        return x + n
    return inner(n)


def remember(n):
    def inner(x):
        nonlocal n
        n = n + x
        return n
    return inner(1)


def run_functions():
    global last_note, area
    area = "functions"
    expect("double", double(4) == 8)
    expect("lam now", (lambda n: n + 1)(10) == 11)
    expect("clamp lo", clamp(-3) == 0)
    expect("clamp hi", clamp(12) == 10)
    expect("clamp", clamp(4) == 4)
    expect("fact", factorial(3) == 6)
    expect("nest", nest(3) == 6)
    left, right = pair(3)
    expect("pair l", left == 3)
    expect("pair r", right == 4)
    expect("def name", greet() == "ada")
    expect("def times", greet_times() == 2)
    expect("def arg", greet("bea") == "bea")
    expect("def both", greet_times("bea", 1) == 1)
    expect("def kw", greet_times(times=1) == 1)
    expect("args", total(1, 2, 3) == 6)
    expect("args8", total(0, 1, 2, 3, 4, 5, 6, 7, 8) == 36)
    expect("kw n", show_extra(note="hi") == 1)
    expect("kw text", last_note == "hi")
    expect("kw both", show_extra(4, note="yo") == 4)
    expect("kw miss", missing_kw() == "")
    expect("kw only", greet_loud("hi", 1, 2, loud=True) == 1)
    expect("kw off", greet_loud("hi") == 0)
    expect("nested", outer(5) == 10)
    expect("nonlocal", remember(4) == 5)
    mark = 0
    if big(11) and not big(3):
        mark = 1
    expect("bool fn", mark == 1)


def big(n):
    return n > 10


def run_motion():
    global area
    area = "motion"
    kitty.go_to_xy(30, -20)
    expect("x", kitty.x_position() == 30)
    expect("y", kitty.y_position() == -20)
    kitty.set_x(5)
    kitty.change_x(2)
    expect("change x", kitty.x_position() == 7)
    kitty.set_y(0)
    kitty.change_y(6)
    expect("change y", kitty.y_position() == 6)
    kitty.point_in_direction(90)
    kitty.turn_right(15)
    expect("turn r", kitty.direction() == 105)
    kitty.turn_left(15)
    expect("turn l", kitty.direction() == 90)
    kitty.set_rotation_style("left-right")
    kitty.set_rotation_style("all around")
    kitty.point_towards("mouse-pointer")
    kitty.if_on_edge_bounce()
    kitty.glide_to_xy(0, 1, 2)
    expect("glide x", kitty.x_position() == 1)
    expect("glide y", kitty.y_position() == 2)
    kitty.go_to("random position")


def run_looks():
    global area
    area = "looks"
    kitty.set_size(50)
    expect("size", kitty.size() == 50)
    kitty.change_size(5)
    expect("size ch", kitty.size() == 55)
    kitty.set_effect("ghost", 0)
    kitty.change_effect("color", 1)
    kitty.clear_graphic_effects()
    kitty.go_to_layer("front")
    kitty.go_layers("forward", 1)
    kitty.next_costume()
    kitty.switch_costume("costume1")
    expect("costume", kitty.costume_name() == "costume1")
    kitty.show()
    kitty.hide()
    kitty.show()
    kitty.think("tick")
    kitty.set_volume(40)
    expect("volume", kitty.volume() == 40)
    kitty.change_volume(5)
    expect("vol ch", kitty.volume() == 45)
    kitty.pen_down()
    kitty.set_pen_color("#ff0000")
    kitty.stamp()
    kitty.pen_up()
    kitty.erase_all()


def run_sensing():
    global area
    area = "sensing"
    mark = 1
    if kitty.touching("edge") or kitty.mouse_down() or kitty.key_pressed("space"):
        mark = 1
    expect("sensors", mark == 1)
    # Loudness is -1 until a microphone is connected and allowed, then 0 to 100.
    loud = kitty.loudness()
    expect("loud", loud >= -1 and loud <= 100)
    expect("year", kitty.current("year") > 2020)
    expect("days", kitty.days_since_2000() > 9000)
    kitty.reset_timer()
    expect("timer", kitty.timer() >= 0)
    name = kitty.username()
    expect("user", name == name)


def run_sprites():
    global area
    area = "sprites"
    felix.speak()
    expect("felix x", felix.x_position() == 9)
    expect("felix y", felix.y_position() == 4)
    felix.nudge(3)
    expect("nudge", felix.x_position() == 12)
    felix.wounded()
    expect("lambda", felix.size() == 8)
    game.stamp()
    expect("backdrop", kitty.backdrop_name() == "plain")


@kitty.when_receive("ping")
def on_ping():
    global got_message
    got_message = 1


@kitty.when_cloned
def on_clone():
    global clones
    clones += 1


@kitty.when_key("q")
def ask_hat():
    kitty.ask("name")
    kitty.say(kitty.answer())


@kitty.when_key("space")
def hop():
    kitty.move(0)


@kitty.when_clicked
def poked():
    kitty.change_effect("color", 0)


@kitty.when_stage_clicked
def stage_click():
    kitty.change_effect("color", 0)


@kitty.when_backdrop("plain")
def arrived():
    kitty.change_effect("color", 0)


@kitty.when_loudness(100)
def loud_hat():
    kitty.change_effect("color", 0)


@kitty.when_timer(100000)
def late_hat():
    kitty.change_effect("color", 0)


def run_events():
    global got_message, clones, area
    area = "events"
    got_message = 0
    kitty.broadcast_and_wait("ping")
    expect("message", got_message == 1)
    before = clones
    kitty.create_clone("myself")
    kitty.wait(0.3)
    expect("clone", clones == before + 1)


passed = 0
failed = 0
failed_tests.clear()
run_values()
run_loops()
run_text()
run_lists()
run_module_list()
run_list_calls()
run_grids()
run_dicts()
run_try()
run_tuples_sets()
double = lambda n: n * 2
big_check = lambda n: n > 3
run_functions()
area = "lambda"
shown = 0
if big_check(4):
    shown = 1
expect("lam bool", shown == 1)
run_motion()
run_looks()
run_sensing()
run_sprites()
run_events()
kitty.say(f"passed {passed}")
kitty.wait(1.2)
kitty.say(f"failed {failed}")
 