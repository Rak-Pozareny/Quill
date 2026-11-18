"""Write the project symbol library (lib/cm5h.kicad_sym) and sym-lib-table for generated symbols."""
import copy
import os
from sexpr import Q, dump


def write_project_libs(outdir, symbols):
    os.makedirs(os.path.join(outdir, 'lib'), exist_ok=True)
    lib = ['kicad_symbol_lib', ['version', 20251024], ['generator', Q('kicad_symbol_editor')], ['generator_version', Q('10.0')]]
    for lib_id, s in sorted(symbols.items()):
        node = copy.deepcopy(s.node)
        node[1] = Q(lib_id.split(':', 1)[1])
        lib.append(node)
    open(os.path.join(outdir, 'lib', 'cm5h.kicad_sym'), 'w').write(dump(lib) + '\n')
    table = ['sym_lib_table', ['version', 7],
             ['lib', ['name', Q('cm5h')], ['type', Q('KiCad')], ['uri', Q('${KIPRJMOD}/lib/cm5h.kicad_sym')],
              ['options', Q('')], ['descr', Q('CM5 handheld project symbols (generated)')]]]
    open(os.path.join(outdir, 'sym-lib-table'), 'w').write(dump(table) + '\n')
    os.makedirs(os.path.join(outdir, 'lib', 'cm5h.pretty'), exist_ok=True)
    fpt = ['fp_lib_table', ['version', 7],
           ['lib', ['name', Q('cm5h')], ['type', Q('KiCad')], ['uri', Q('${KIPRJMOD}/lib/cm5h.pretty')],
            ['options', Q('')], ['descr', Q('CM5 handheld project footprints (from datasheet drawings)')]]]
    open(os.path.join(outdir, 'fp-lib-table'), 'w').write(dump(fpt) + '\n')
