#!/usr/bin/env python3
"""Fast regression tests for TRIAD."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import triad_core as t

def check(expr, expected):
    got = t.safe_calculate(expr)
    assert got is not None, f"should calculate: {expr}"
    assert abs(float(got['result']) - expected) < 1e-9, (expr, got, expected)

check('2 + 2 * 3', 8)
check('(10 - 4) / 3', 2)
check('2 ** 10', 1024)
check('7 // 2', 3)
check('−5 + 2', -3)
assert t.safe_calculate("__import__('os').system('id')") is None
assert t.safe_calculate('1 / 0') is None
assert t.safe_calculate('2 ** 1000') is None
triad = t.analyze_triad([1, 1, 1])
assert triad['variance_population'] == 0
assert triad['balance_index_0_to_1'] == 1
assert all(abs(x - 1/3) < 1e-9 for x in triad['normalized_shares'])
assert t.search_memory('цифровой материк', 3), 'seed memory should be searchable'

# Natural Russian arithmetic is normalized, then passed through the same safe AST evaluator.
for phrase, expected in [
    ('Сколько будет два плюс два?', 4),
    ('чему равно двадцать три минус пять?', 18),
    ('посчитай три умножить на четыре', 12),
    ('пять разделить на два', 2.5),
    ('сто двадцать три плюс семь', 130),
    ('2 плюс 2', 4),
    ('два - один', 1),
    ('два × три', 6),
]:
    result = t.ask(phrase)
    assert result['calculation'] is not None, (phrase, result)
    assert abs(float(result['calculation']['result']) - expected) < 1e-9, (phrase, result)

assert t.normalize_russian_arithmetic('два три плюс два') is None
assert t.normalize_russian_arithmetic('запусти терминал плюс два') is None
assert t.ask('Сколько будет два плюс два?')['calculation']['result'] == 4
print('TRIAD regression tests: PASS')
print('Arithmetic, unsafe-input rejection, triple-vector invariants, and memory search verified.')
