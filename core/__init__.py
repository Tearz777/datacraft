from core.io import read_file, save_result
from core.cleaning import apply_bulk_rules, find_inconsistencies, apply_title_case
from core.merge import find_common_columns, merge_multiple
from core.profiling import analyze_column, suggest_transformation, apply_transformation, compare_and_suggest
from core.utils import show_sample
from core.ui import box, path_completer, auto_map, lebar