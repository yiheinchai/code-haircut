# AUTOGENERATED! DO NOT EDIT! File to edit: haircut.ipynb.

# %% auto 0
__all__ = ['ftransform', 'FTransform', 'split_meta_data_and_code_for_line', 'split_meta_data_and_code', 'RegexNoMatchError',
           'StackItem', 'TraceCompiler']

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

class StackItem:
    def __init__(self, class_name, func_name, skip=False) -> None:
        self.class_name = class_name
        self.func_name = func_name
        self.skip = skip

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

        #######################################
        # Removing ifs that evaluate to false #
        #######################################

        df['has_complete_if'] = df['code'].apply(lambda x: x.strip().endswith(':') and x.strip().startswith('if'))
        next_line_will_jump = df['line_no'].diff().shift(-1) > 1
        next_line_new_file = df['file_path'].shift(-1) != df['file_path']
        next_line_not_has_call = ~df['code'].shift(-1).str.contains('=>', na=False)

        df['prune if'] = df['has_complete_if'] & (next_line_new_file | next_line_will_jump) & next_line_not_has_call
        df = df[~df['prune if']]
        df.drop(columns=['has_complete_if', 'prune if'], inplace=True)
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
            previous_line = self._line_log[-2]
            return self._get_inline_class_name_from_func_name(self._get_func_name(code_snippet), previous_line)
        except RegexNoMatchError:
            pass

        try:
            # Just use func name as class anme
            return self._get_func_name(code_snippet)
        except RegexNoMatchError:
            raise

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
        
        self.classes[class_name][func_name] = [f"def {code_snippet[3:]}:"]

    def _compile_line(self, code_snippet):
        code_snippet = code_snippet.strip()
        self.classes[self._stack[-1].class_name][self._stack[-1].func_name].append(code_snippet)

    def _compile_func_return(self, code_snippet):
        self._stack.pop()

    def _log_line(self, code_snippet):
        "History of last 5 lines processed. Useful to track back to find more info abt called function"
        if len(self._line_log) > 5:
                self._line_log = self._line_log[-5:]
        self._line_log.append(code_snippet)

    def compile(self):
        for index, row in df.iterrows():
            file_path = row["file_path"]
            line_no = row["line_no"]
            indent = int(row["indent"])
            code_snippet = row["code"].strip()

            self._log_line(code_snippet)
            
            if code_snippet.startswith("<="):
                self._compile_func_return(code_snippet)
                continue


            if code_snippet.startswith("=>"):
                self._compile_func_calls(code_snippet)
                continue
            
            # Skip functions marked to skip, eg. lambda functions
            if self._stack[-1].skip:
                continue

            self._compile_line(code_snippet)

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

            with p.open(mode="w") as file:
                file.write(self._build_file(class_name, func_dict))
