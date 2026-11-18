#!/usr/bin/env python3
"""Assemble docs/checkpoint1/CHECKPOINT1.md from the hand-written source + generated tables."""
import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'checkpoint1')
src = open(os.path.join(D, 'CHECKPOINT1.src.md')).read()
for marker, fn in (('POWER_TABLE', '_power_table.md'), ('BATTERY_TABLE', '_battery_table.md'), ('PIN_TABLE', '_pin_table.md'),
                   ('PIN_NC_TABLE', '_pin_nc_table.md'), ('PARTS_TABLE', '_parts_table.md')):
    src = src.replace(f'<!--{marker}-->', open(os.path.join(D, fn)).read().rstrip())
assert '<!--' not in src, 'unreplaced marker'
open(os.path.join(D, 'CHECKPOINT1.md'), 'w').write(src)
print('CHECKPOINT1.md', len(src.splitlines()), 'lines')
