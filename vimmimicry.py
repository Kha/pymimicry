import os
import os.path

import mimicry
import ropemode.refactor
import ropemode.dialog
import ropevim
import vim

_mimicry = mimicry.RestructureMimicry()

def _goto_window_for_buffer(b):
    w = int(vim.eval('bufwinnr(%d)' % int(b)))
    vim.command('%dwincmd w' % w)

def _goto_window_for_buffer_name(bn):
    b = vim.eval('bufnr("%s")' % bn)
    return _goto_window_for_buffer(b)

def _output_text(lines):
    current_window = vim.eval('winnr()')
    _goto_window_for_buffer_name('__Mimicry__')
    vim.command('setlocal modifiable')
    vim.current.buffer[:] = lines
    vim.command('setlocal nomodifiable')
    vim.command('%swincmd w' % current_window)

def from_undo_step():
    """Appends the changes the last edit has introduced."""
    vim.command('silent undo')
    old_text = '\n'.join(vim.current.buffer[:])
    vim.command('silent redo')
    new_text = '\n'.join(vim.current.buffer[:])
    _mimicry.add_change(old_text, new_text)

def refresh_output():
    try:
        params = _mimicry.get_restructure_params()
        output = ["pattern: %s" % params.pattern,
                  "goal:    %s" % params.goal]
    except mimicry.NoRestructuringError as e:
        output = ["<ERROR: %s>" % e.message]

    def format_code(code):
        # TODO: Do something more sensible with multiline output... if we want
        # it at all
        return str(code).replace("\n", "\\n")

    _output_text(["\" p to preview changes",
                  "\" c to commit changes",
                  "\" u to forget last recorded change"] + output + [""] +
                 ["%2d. %s -> %s" % (idx+1, format_code(old), format_code(new))
                  for idx, (old, new) in enumerate(_mimicry.changes)])

_refactoring = ropemode.refactor.Restructure(ropevim._interface, ropevim._env)

def _get_changes():
    params = _mimicry.get_restructure_params()
    args = {'pattern': params.pattern, 'goal': params.goal, 'args': {}, 'imports': [],
            'resources': None}
    # pretty much an inlining of Refactoring.show()
    ropevim._interface._check_project()
    ropevim._interface._save_buffers()
    _refactoring._create_refactoring()
    def calculate(handle):
        return _refactoring._calculate_changes(args, handle)
    name = 'Calculating %s changes' % _refactoring.name
    return ropemode.refactor.runtask(ropevim._env, calculate, name=name)

def perform_changes():
    _refactoring._perform(_get_changes())

def preview_changes():
    changes = _get_changes()
    if changes is not None:
        print(changes.get_description())
    else:
        print('No changes!')

def pop_change():
    if _mimicry.changes:
        _mimicry.changes.pop()
