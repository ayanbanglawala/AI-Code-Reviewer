import difflib
from langchain.tools import tool

@tool
def get_diff_lines(original: str, refactored: str):
    """
    Compares original and refactored code line by line.
    Returns a list of dicts — each dict is one line with:
      - type: 'added' | 'removed' | 'unchanged'
      - content: the line text
    This is what Streamlit uses to render the colored diff view.
    """
    original_lines   = original.splitlines()
    refactored_lines = refactored.splitlines()

    differ = difflib.ndiff(original_lines, refactored_lines)

    result = []
    for line in differ:
        if line.startswith("+ "):
            result.append({"type": "added",     "content": line[2:]})
        elif line.startswith("- "):
            result.append({"type": "removed",   "content": line[2:]})
        elif line.startswith("  "):
            result.append({"type": "unchanged", "content": line[2:]})
        # lines starting with "? " are hints from ndiff — skip them

    return result

@tool
def get_summary_stats(diff_lines: list):
    """
    Returns a quick summary dict from the diff result.
    Use this to show the stats bar in Streamlit.
    """
    added   = sum(1 for l in diff_lines if l["type"] == "added")
    removed = sum(1 for l in diff_lines if l["type"] == "removed")
    unchanged = sum(1 for l in diff_lines if l["type"] == "unchanged")

    return {
        "lines_added":   added,
        "lines_removed": removed,
        "lines_unchanged": unchanged,
        "total_changes": added + removed
    }