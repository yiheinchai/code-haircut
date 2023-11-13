# AUTOGENERATED! DO NOT EDIT! File to edit: haircut.ipynb.

# %% auto 0
__all__ = ['ftransform', 'FTransform', 'split_meta_data_and_code_for_line', 'split_meta_data_and_code', 'RegexNoMatchError',
           'Line', 'StackItem', 'BlockStackItem', 'TraceCompiler']

# %% haircut.ipynb 2
import pandas as pd
import numpy as np
from pathlib import Path

# %% haircut.ipynb 6
# Importing necessary library
import re
import os
from functools import wraps

def ftransform(func):
    @wraps(func)
    def wrapper(args):
        return FTransform(func(args))
    return wrapper

class FTransform:
    def __init__(self, file) -> None:
        self.file = file

    def apply(self, f):
        return f(self.file)

def split_meta_data_and_code_for_line(line):
    meta_data = line[:60]
    code = line[60:]
    return meta_data, code

@ftransform
def split_meta_data_and_code(file):
    return [split_meta_data_and_code_for_line(line) for line in file]

# %% haircut.ipynb 30
class RegexNoMatchError(Exception):
    pass

class Line:
    def __init__(self, line_no, line_code):
        self.line_no = line_no
        self.line_code = line_code

    def tab(self):
        self.line_code = '\t' + self.line_code

class StackItem:
    def __init__(self, class_name, func_name, skip=False) -> None:
        self.class_name = class_name
        self.func_name = func_name
        self.skip = skip

class BlockStackItem(StackItem):
    '''This is a stateful stack item'''
    def __init__(self, parent_class_name, parent_func_name, block_type, definition_line):
        super().__init__(parent_class_name, parent_func_name)
        self.block_type = block_type
        self._lines = [definition_line]

    def add_line(self, line):
        self._lines.append(line)

    def add_line_many(self, lines):
        self._lines.extend(lines)

    def tab_lines(self):
        for line in self._lines:
            line.tab()

    @property
    def lines(self):
        return self._lines

    @property
    def line_indices(self):
        return [line.line_no for line in self._lines]

    @property
    def line_codes(self):
        return [line.line_code for line in self._lines]

    def __repr__(self):
        return self._lines[0].line_code + "\n".join(['\t' + line.line_code for line in self._lines[1:]])


class TraceCompiler:
    classes= {}
    _stack = []
    _line_log = []

    def __init__(self, trace_path, output_path = "haircutted"):
        self._df = None
        self._trace_path = trace_path
        self._output_path = output_path

    def pre_process(self):
        try:
            with open(self._trace_path, 'r') as file:
                execution_trace = file.read()
        except FileNotFoundError:
            print(repr(file_path) + " not found. Please check the file path and try again.")


        df = pd.DataFrame(FTransform(execution_trace.split('\n')).apply(split_meta_data_and_code).file, columns=['meta_data', 'code'])
        df['indent'] = df['code'].apply(lambda x: len(x) - len(x.lstrip()))
        df['diff'] = df.indent.diff()
        df['line_no'] = df['meta_data'].apply(lambda x: x.split(':')[-1].split(' ')[0])
        df['file_path'] = df['meta_data'].apply(lambda x: x.split(':')[0])

        # Remove empty row
        df = df[:-1]

        df['line_no'] = df['line_no'].astype(int)
        df['execution_order'] = df.index

        # Rearrange columns
        df = df[['execution_order', 'file_path', 'line_no', 'indent', 'diff', 'code']]

        # #######################################
        # # Removing ifs that evaluate to false #
        # #######################################

        # df['has_complete_if'] = df['code'].apply(lambda x: x.strip().endswith(':') and x.strip().startswith('if'))
        # next_line_will_jump = df['line_no'].diff().shift(-1) > 1
        # next_line_new_file = df['file_path'].shift(-1) != df['file_path']
        # next_line_not_has_call = ~df['code'].shift(-1).str.contains('=>', na=False)

        # df['prune if'] = df['has_complete_if'] & (next_line_new_file | next_line_will_jump) & next_line_not_has_call
        # df = df[~df['prune if']]
        # df.drop(columns=['has_complete_if', 'prune if'], inplace=True)
        self._df = df

    def _get_func_name(self, code_snippet):
        match = re.match(r"=>\s+(\w+)", code_snippet)

        if match is None:
            raise RegexNoMatchError(f"Could not find function name in {code_snippet}")

        return match.group(1)


    def _get_self_class_name(self, code_snippet):
        match = re.match(r"=>(.*)\((self|cls)=<(\S*).*\)", code_snippet)
        
        if match is None:
            raise RegexNoMatchError(f"Could not find class name in {code_snippet}")

        return match.group(3)

    def _get_inline_class_name_from_func_name(self, func_name, code_snippet):
        match =  re.match(r".* (\S*)\." + func_name + r"\(\S*\)", code_snippet)
        
        # if match is None:
        #     match = 
        
        if match is None:
            raise RegexNoMatchError(f"Could not find class name in {code_snippet}")

        return match.group(1)

    def _get_class_name(self, code_snippet):
        try:
            return self._get_self_class_name(code_snippet)
        except RegexNoMatchError:
            pass

        try:
            previous_line = self._line_log[-2].line_code
            return self._get_inline_class_name_from_func_name(self._get_func_name(code_snippet), previous_line)
        except RegexNoMatchError:
            pass

        try:
            # Just use func name as class anme
            return self._get_func_name(code_snippet)
        except RegexNoMatchError:
            raise

    def _add_line(self, class_name, func_name, line):
        self.classes[class_name].setdefault(func_name, []).append(line)

    def _add_line_many(self, class_name, func_name, lines):
        self.classes[class_name].setdefault(func_name, []).extend(lines)

    def _compile_func_calls(self, code_snippet):

        # Skip lambda functions TODO: might want to handle this better in the future
        if "genexpr" in code_snippet or "listcomp" in code_snippet or "lambda" in code_snippet:
            self._stack.append(StackItem(None, 'lambda', skip=True))
            return

        # Skip decorators TODO:might want to handle this better in the future
        if "=> inner(" in code_snippet:
            self._stack.append(StackItem(None, 'lambda', skip=True))
            return

        func_name = self._get_func_name(code_snippet)
        class_name = self._get_class_name(code_snippet)

        self._stack.append(StackItem(class_name, func_name))

        if class_name not in self.classes:
            self.classes[class_name] = {}
        
        self._add_line(class_name, func_name, f"def {code_snippet[3:]}:")

    def _compile_line_in_block(self, code_snippet, line_no):
        # For lines that are in a block within the function OR in a nested block
        if self._check_is_in_block():
            line = Line(line_no, code_snippet)
            line.tab()
            self._stack[-1].add_line(line)
            return
        
        code_snippet = code_snippet.strip()
        class_name = self._stack[-1].class_name
        func_name = self._stack[-1].func_name

        self._add_line(class_name, func_name, code_snippet)

    def _compile_func_return(self, code_snippet):
        self._stack.pop()

    def _compile_block_return(self):
        block = self._stack.pop()

        if len(block.lines) <= 1:
            if self._check_is_in_block():
                self._compile_block_return()
            return

        if self._check_is_in_block():
            block.tab_lines()
            self._stack[-1].add_line_many(block.lines)
        
            # Recurse until all existing blocks are closed
            # TODO: This assumes that if there is a line jump, then all previous nested blocks are escaped
            self._compile_block_return()
        
    
        self._add_line_many(block.class_name, block.func_name, block.line_codes)

    def _compile_block_entry(self, code_snippet, line_no):
        parent_block = self._stack[-1]

        parent_class_name, parent_func_name = parent_block.class_name, parent_block.func_name
        block_type = code_snippet.split(" ")[0]

        self._stack.append(BlockStackItem(parent_class_name, parent_func_name, block_type, Line(line_no, code_snippet)))

    def _compile_line(self, code_snippet, line_no):
        if self._check_is_in_block() and self._check_line_jump():
            # TODO: if -> nested if -> nested else - the code in nested else will not be added to top level if (as it is considered a line jump)
            self._compile_block_return()
            # Do not return has we have not yet processed the current line
            # Just only know that current line is no longer in block

        if code_snippet.startswith("<="):
            self._compile_func_return(code_snippet)
            return

        if code_snippet.startswith("=>"):
            self._compile_func_calls(code_snippet)
            return

        # Skip functions marked to skip, eg. lambda functions
        if self._stack[-1].skip:
            return

        if code_snippet.startswith(("if", "elif", "else", "for", "with", 'while', 'try', 'except', 'finally')) and code_snippet.endswith(":"):
            self._compile_block_entry(code_snippet, line_no)
            return
        
        self._compile_line_in_block(code_snippet, line_no)

    def _log_line(self, code_snippet, line_no):
        "History of last 5 lines processed. Useful to track back to find more info abt called function"
        if len(self._line_log) > 10:
                self._line_log = self._line_log[-10:]
        self._line_log.append(Line(line_no, code_snippet))

    def _check_line_jump(self):
        return self._line_log[-1].line_no - self._line_log[-2].line_no > 1

    def _check_is_in_block(self):
        if len(self._stack) == 0:
            return False

        return isinstance(self._stack[-1], BlockStackItem)

    def compile(self):
        for index, row in self._df.iterrows():
            file_path = row["file_path"]
            line_no = row["line_no"]
            indent = int(row["indent"])
            code_snippet = row["code"].strip()

            self._log_line(code_snippet, line_no)
            self._compile_line(code_snippet, line_no)

    def _build_class(self, class_name):
        return f"class {class_name}:"

    def _build_func(self, func_code):
        func_def = func_code[0]
        func_body = func_code[1:]

        return "\n".join(['\t' + func_def] + ['\t\t' + line for line in func_body])

    def _build_file(self, class_name, func_dict):
        code = []

        code.append(self._build_class(class_name))
        for func_code in func_dict.values():
            code.append(self._build_func(func_code))
            code.append('\n')

        return "\n".join(code)

    def build(self):
        for class_info, func_dict in self.classes.items():
            class_info = class_info.split(".")

            if len(class_info) < 3:
                class_path = Path("external")

            if len(class_info) < 2:
                class_file = Path(class_info[-1] + ".py")
            
            if len(class_info) >= 3:   
                class_name = class_info[-1]
                class_file = Path(class_info[-2] + ".py")
                class_path = Path("/".join(class_info[:-2]))

            os.makedirs(self._output_path / class_path, exist_ok=True)

            p = self._output_path / class_path / class_file
            
            if p.exists():
                with p.open(mode="a") as file:
                    file.write(self._build_file(class_name, func_dict))
            else:
                with p.open(mode="w") as file:
                    file.write(self._build_file(class_name, func_dict))

# %% haircut.ipynb 40
if __name__ == "__main__":
    tc = TraceCompiler("test.txt")
    tc.pre_process()
    tc.compile()
