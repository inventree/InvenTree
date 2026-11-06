"""Check that the invoke_commands() macro output rendered correctly.

The invoke_commands() macro runs 'invoke' during the documentation build, and
includes its output in the page. If the command fails, the page may contain an
error (or empty output) without failing the build.

Expected values are derived by statically parsing tasks.py:

- 'invoke --list': every task registered in the task collections is listed
  (and no unknown tasks are listed)
- 'invoke <task> --help': the help text is for the requested task, and
  includes the task docstring summary and all task options

Usage:
    python docs/ci/check_invoke_commands.py [--site-dir <path>]
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from docs_checks import (
    REPO_DIR,
    Checker,
    MacroCall,
    Page,
    check_macro_errors,
    find_macro_calls,
    iter_pages,
    normalize,
    run,
)

TASKS_FILE = REPO_DIR / 'tasks.py'

# A task name in the 'invoke --list' output (indented two spaces, at the start of a line)
LIST_ENTRY_RE = re.compile(r'^  (\S+)', re.MULTILINE)


@dataclass
class Task:
    """Information about an invoke task, parsed from tasks.py."""

    name: str  # Full (dashed) task name, e.g. 'dev.test'
    summary: str  # First paragraph of the docstring
    options: list[str]  # Long option flags, e.g. ['--migrate', '--skip-backup']


def dashed(name: str) -> str:
    """Convert a python identifier to an invoke task / option name."""
    return name.replace('_', '-')


def is_task_decorator(node) -> bool:
    """Return True if the provided decorator node is '@task' or '@task(...)'."""
    if isinstance(node, ast.Call):
        node = node.func
    return isinstance(node, ast.Name) and node.id == 'task'


def parse_tasks() -> dict[str, Task]:
    """Parse tasks.py, and return the registered tasks keyed by full task name."""
    tree = ast.parse(TASKS_FILE.read_text(encoding='utf-8'))

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and any(is_task_decorator(d) for d in node.decorator_list)
    }

    # Collection variable name -> list of task function names
    collections = {}
    # Collection variable name -> namespace prefix
    prefixes = {'ns': ''}

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == 'Collection'
        ):
            collections[node.targets[0].id] = [
                arg.id for arg in node.value.args if isinstance(arg, ast.Name)
            ]

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == 'add_collection'
            and len(node.args) == 2
        ):
            prefixes[node.args[0].id] = ast.literal_eval(node.args[1]) + '.'

    tasks = {}

    for collection, names in collections.items():
        prefix = prefixes.get(collection)

        if prefix is None:
            continue

        for name in names:
            func = functions.get(name)

            if func is None:
                continue

            docstring = ast.get_docstring(func) or ''
            # Skip the first argument (the invoke context)
            args = func.args.args[1:] + func.args.kwonlyargs
            full_name = prefix + dashed(name)

            tasks[full_name] = Task(
                name=full_name,
                summary=docstring.split('\n\n')[0],
                options=[f'--{dashed(arg.arg)}' for arg in args],
            )

    return tasks


def code_blocks(page: Page) -> list[str]:
    """Return the text of all code blocks on a page."""
    return [pre.get_text() for pre in page.soup.select('pre')]


def check_list(page: Page, call: MacroCall, tasks: dict, checker: Checker):
    """Check the rendered output of 'invoke --list'."""
    label = f'{page.label}:{call.line} invoke_commands("--list")'

    blocks = [b for b in code_blocks(page) if 'Available tasks:' in b]

    if not checker.check(bool(blocks), f'{label} task list not rendered'):
        return

    listed = set(LIST_ENTRY_RE.findall(blocks[0]))
    missing = sorted(set(tasks) - listed)
    unknown = sorted(listed - set(tasks))

    checker.check(not missing, f'{label} tasks not listed: {missing}')
    checker.check(not unknown, f'{label} unexpected tasks listed: {unknown}')


def check_help(page: Page, call: MacroCall, command: str, tasks, checker: Checker):
    """Check the rendered output of 'invoke <task> --help'."""
    name = command.split()[0]
    label = f'{page.label}:{call.line} invoke_commands("{command}")'
    task = tasks.get(name)

    if not checker.check(task is not None, f'{label} unknown task "{name}"'):
        return

    usage = f'[--core-opts] {name} '
    blocks = [b for b in code_blocks(page) if usage in b]

    if not checker.check(bool(blocks), f'{label} help text not rendered'):
        return

    text = blocks[0]

    if task.summary:
        checker.check(
            normalize(task.summary) in normalize(text),
            f'{label} docstring summary not rendered: "{task.summary}"',
        )

    # Boolean options which default to True are listed as '--[no-]<name>'
    missing = [
        opt
        for opt in task.options
        if not re.search(r'--(\[no-\])?' + re.escape(opt[2:]) + r'\b', text)
    ]

    checker.check(not missing, f'{label} options not listed: {missing}')


def check_invoke_commands(site_dir: Path, checker: Checker):
    """Check all invoke_commands() macro calls against the rendered documentation."""
    tasks = parse_tasks()

    checker.check(bool(tasks), f'No invoke tasks found in {TASKS_FILE}')

    total = 0

    for page in iter_pages(site_dir):
        calls, skipped = find_macro_calls(page, 'invoke_commands')

        checker.check(
            skipped == 0,
            f'{page.label}: {skipped} invoke_commands() calls with non-literal arguments cannot be checked',
        )

        if not calls:
            continue

        total += len(calls)

        if not checker.check(
            page.output.exists(), f'{page.label}: Missing rendered page {page.output}'
        ):
            continue

        check_macro_errors(page, checker)

        for call in calls:
            command = call.arg(0, 'command', '--list').strip()

            if command == '--list':
                check_list(page, call, tasks, checker)
            elif command.endswith('--help'):
                check_help(page, call, command, tasks, checker)
            else:
                checker.check(
                    False,
                    f'{page.label}:{call.line} invoke_commands("{command}") is not a supported command for checking',
                )

    checker.check(total > 0, 'No invoke_commands() calls found in documentation')
    print(f'  Checked {total} invoke_commands() calls ({len(tasks)} tasks in tasks.py)')


if __name__ == '__main__':
    run('Checking invoke command output', check_invoke_commands)
