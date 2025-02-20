# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/viztracer/blob/master/NOTICE.txt

import multiprocessing
import os

from .cmdline_tmpl import CmdlineTmpl


file_basic = """
from viztracer import log_sparse

@log_sparse
def f():
    return 1

def g():
    return f()

assert g() == 1
"""


file_stack = """
from viztracer import log_sparse

def h():
    return 1

def f():
    return h()

@log_sparse(stack_depth=2)
def g():
    return f()

assert g() == 1
assert g() == 1
"""


file_stack_nested = """
from viztracer import log_sparse

@log_sparse(stack_depth=2)
def h():
    return 1

def f():
    return h()

@log_sparse(stack_depth=2)
def g():
    return f()

assert g() == 1
assert g() == 1
"""


file_multiprocess = """
from multiprocessing import Process
from viztracer import log_sparse
import time

@log_sparse
def f(x):
    return x*x

if __name__ == "__main__":
    for i in range(3):
        p = Process(target=f, args=(i,))
        p.start()
        p.join()
        time.sleep(0.1)
"""


class TestLogSparse(CmdlineTmpl):
    def test_basic(self):
        def check_func(data):
            for entry in data["traceEvents"]:
                self.assertNotEqual(entry["name"], "f")

        self.template(["viztracer", "-o", "result.json", "--log_sparse", "cmdline_test.py"],
                      script=file_basic,
                      expected_output_file="result.json",
                      expected_entries=1)
        self.template(["viztracer", "-o", "result.json", "cmdline_test.py"],
                      script=file_basic,
                      expected_output_file="result.json",
                      check_func=check_func)

    def test_stack(self):
        self.template(["viztracer", "-o", "result.json", "--log_sparse", "cmdline_test.py"],
                      script=file_stack,
                      expected_output_file="result.json",
                      expected_entries=4)

        self.template(["viztracer", "-o", "result.json", "--log_sparse", "cmdline_test.py"],
                      script=file_stack_nested,
                      expected_output_file="result.json",
                      expected_entries=4)

    def test_without_tracer(self):
        self.template(["python", "cmdline_test.py"], script=file_basic, expected_output_file=None)
        self.template(["python", "cmdline_test.py"], script=file_stack, expected_output_file=None)

    def test_multiprocess(self):
        if multiprocessing.get_start_method() == "fork":
            try:
                self.template(["viztracer", "-o", "result.json", "--log_sparse", "cmdline_test.py"],
                              script=file_multiprocess,
                              expected_output_file="result.json",
                              expected_entries=3,
                              concurrency="multiprocessing")
            except Exception as e:
                # coveragepy has some issue with multiprocess pool
                if not os.getenv("COVERAGE_RUN"):
                    raise e
