# CodeHaircut 💇🏻‍♂️

Give you codebase a haircut.

Have ever tried using a package that is 50MB+ in size? Do you REALLY need all that code?

CodeHaircut removes deadcode and unreachable code by analysing the execution trace when running your app. It rebuilds your dependencies to only contain code that you would use.

Realisitcally, this project is pretty useless in building usable code, in the current version, the rebuilt code is broken with syntax errors.

However, it was created to give developers a better understanding of how the packages they are using work internally. By removing large chunks of code that is meant for edge cases, developers have a much better reading experience, focusing only on code that will execute for specific to the core functionality. This significantly saves on reading time, no time wasted on reading code that is meant for the 9 billion long tail of edge cases, only read code for the core functionality.

## Usage

### Recording execution trace

Use [Python Hunter](https://github.com/ionelmc/python-hunter) to collect the execution trace of your app, using the Q filters to filter only parts of the code you want to have a haircut.

In Python:

```python
hunter.trace(stdlib=False, action=hunter.CallPrinter(stream=open("execution_trace.txt", "w"))
```

With bash to run Django:

```bash
PYTHONHUNTER='Q(module_startswith=["db"])' python manage.py runserver --noreload --nothreading
```

Make sure to save the execution trace as a file, such `execution_trace.txt`.

### Rebuilding source from execution trace

```python
from haircut import TraceCompiler

tc = TraceCompiler(trace_path="execution_trace.txt", output_path="output")

tc.pre_process()
tc.compile()
tc.build()
```
