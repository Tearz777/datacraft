import shutil
import unicodedata
import os
import glob

auto_map = {
    "mixed_numeric_format": "remove_separator",
    "whitespace_issue": "strip_whitespace",
    "case_inconsistent": "eval",
}

lebar = shutil.get_terminal_size().columns


def box(title):
    vis = sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in title)
    pad_total = lebar - 2 - vis
    pad_left = pad_total // 2
    pad_right = pad_total - pad_left

    print("╔" + "═" * (lebar - 2) + "╗")
    print("║" + " " * pad_left + title + " " * pad_right + "║")
    print("╚" + "═" * (lebar - 2) + "╝")


def path_completer(text, state):
    expanded = os.path.expanduser(text)
    matches = glob.glob(expanded + '*')

    matches = [
        m.replace(os.path.expanduser('~'), '~').replace(' ', '\\ ')
        for m in matches
    ]

    return matches[state] if state < len(matches) else None

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause(msg="Enter..."):
    input(msg)