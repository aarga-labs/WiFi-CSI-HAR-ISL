"""
cue_display.py - full-screen, colour-coded cue words in the terminal.

No extra packages. The terminal is cleared and the word is drawn in big
block letters on a coloured background:

  YELLOW  get ready (move to the start position, freeze)
  GREEN   GO        (do it now)
  RED     STOP      (freeze)
  BLUE    clap 3 times
  WHITE   operator screens (break, done, story start)

The last 3 lines of the terminal are left free for the operator's prompts.
Make the terminal full-screen and zoom in (Ctrl+Shift+= in most terminals)
so the word can be read from the participant's spot.
"""
import shutil
import sys

_FONT = {
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#### ", "#   #", "#### "],
    "C": [" ####", "#    ", "#    ", "#    ", " ####"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#### ", "#    ", "#####"],
    "F": ["#####", "#    ", "#### ", "#    ", "#    "],
    "G": [" ####", "#    ", "#  ##", "#   #", " ####"],
    "H": ["#   #", "#   #", "#####", "#   #", "#   #"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "#####"],
    "J": ["#####", "   # ", "   # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#### ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "# # #", "#  # ", " ## #"],
    "R": ["#### ", "#   #", "#### ", "#  # ", "#   #"],
    "S": [" ####", "#    ", " ### ", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "# # #", "## ##", "#   #"],
    "X": ["#   #", " # # ", "  #  ", " # # ", "#   #"],
    "Y": ["#   #", " # # ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "   # ", "  #  ", " #   ", "#####"],
    "0": [" ### ", "#  ##", "# # #", "##  #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", " ### "],
    "2": [" ### ", "#   #", "  ## ", " #   ", "#####"],
    "3": ["#### ", "    #", " ### ", "    #", "#### "],
    "4": ["#   #", "#   #", "#####", "    #", "    #"],
    "5": ["#####", "#    ", "#### ", "    #", "#### "],
    "6": [" ### ", "#    ", "#### ", "#   #", " ### "],
    "7": ["#####", "    #", "   # ", "  #  ", "  #  "],
    "8": [" ### ", "#   #", " ### ", "#   #", " ### "],
    "9": [" ### ", "#   #", " ####", "    #", " ### "],
    " ": ["   ", "   ", "   ", "   ", "   "],
    ",": ["  ", "  ", "  ", " #", "# "],
    ".": [" ", " ", " ", " ", "#"],
    ":": [" ", "#", " ", "#", " "],
    "-": ["    ", "    ", "####", "    ", "    "],
    "/": ["    #", "   # ", "  #  ", " #   ", "#    "],
    "!": ["#", "#", "#", " ", "#"],
    "?": [" ### ", "    #", "  ## ", "     ", "  #  "],
}
_H = 5
_COLOURS = {
    "ready": "\033[1;30;43m",   # black on yellow
    "go":    "\033[1;30;42m",   # black on green
    "stop":  "\033[1;97;41m",   # white on red
    "clap":  "\033[1;97;44m",   # white on blue
    "info":  "\033[1;30;47m",   # black on white
}
_RESET = "\033[0m"
PROMPT_ROWS = 3

enabled = sys.stdout.isatty()


def _render(word, scale):
    rows = [""] * _H
    for ch in word.upper():
        g = _FONT.get(ch, _FONT["?"])
        for r in range(_H):
            rows[r] += g[r].replace("#", "█" * scale).replace(" ", " " * scale) + " " * scale
    out = []
    for r in rows:                       # every row has the same width -> letters stay aligned
        out += [r[:-scale] if r else r] * scale
    return out


def _wrap(text, cols, scale):
    """Split on '\\n' first, then pack words so each rendered line fits."""
    lines = []
    for part in text.split("\n"):
        cur = ""
        for w in part.split():
            trial = (cur + " " + w).strip()
            if cur and len(_render(trial, scale)[0]) > cols - 2:
                lines.append(cur)
                cur = w
            else:
                cur = trial
        if cur:
            lines.append(cur)
    return lines


def _layout(text, cols, rows):
    """Largest scale (3, 2, 1) at which the text fits the screen."""
    for scale in (3, 2, 1):
        lines = _wrap(text, cols, scale)
        big = []
        for i, line in enumerate(lines):
            if i:
                big.append("")
            big += _render(line, scale)
        if max((len(b) for b in big), default=0) <= cols - 2 and len(big) <= rows:
            return big
    return [text.upper()]


def show(state, text, sub="", top=""):
    """Fill the screen with colour `state` and draw `text` in big letters."""
    if not enabled:
        print(f"\n[{state.upper():5s}] {text.replace(chr(10), ' ')}   {sub}", flush=True)
        return
    cols, rows = shutil.get_terminal_size((80, 24))
    body = max(8, rows - PROMPT_ROWS)
    big = _layout(text, cols, body - 4)
    lines = [top, ""]
    pad = max(0, (body - 4 - len(big)) // 2)
    lines += [""] * pad + big + [""] + [sub]
    lines += [""] * (body - len(lines))
    colour = _COLOURS.get(state, _COLOURS["info"])
    out = ["\033[2J\033[H"]
    for line in lines[:body]:
        out.append(colour + line.center(cols)[:cols].ljust(cols) + _RESET + "\n")
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def plain():
    """Clear back to the normal terminal colours."""
    if enabled:
        sys.stdout.write(_RESET + "\033[2J\033[H")
        sys.stdout.flush()
