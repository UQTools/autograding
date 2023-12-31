"""
This file may be used as a starting point for writing Gradescope autograders.

The first part of the file contains a TestCase superclass that introduces
some convenience methods for writing tests with input and output.

The second part of the file contains a copy of the Gradescope provided
unittest wrapper to output results in the Gradescope JSON format.

The third part handles the generation of an appropriate zip file
based on the contents of the current directory.
"""

import io
import unittest.mock
from unittest import TestCase


class TeachingStaffException(Exception):
    """Exception that is raised if the tests have been written incorrectly."""
    pass


def _ignore_whitespace(s):
    return s.replace(r'\s', '')


def _ignore_case(s):
    return s.lower()


class TestCase(TestCase):
    def assertIOEquals(self, func, stdin, stdout, 
                       ignore_whitespace=True, ignore_case=True,
                       output_includes_input=False):
        self.longMessage = True
        for line in stdin:
            if not isinstance(line, str):
                raise TeachingStaffException("Input must be a list of strings")

        if not isinstance(stdout, str):
            raise TeachingStaffException("Expected output must be a string")

        if ignore_whitespace:
            stdin = [_ignore_whitespace(line) for line in stdin]
            stdout = _ignore_whitespace(stdout)

        if ignore_case:
            stdin = [_ignore_case(line) for line in stdin]
            stdout = _ignore_case(stdout)

        gobbled = io.StringIO()
        def send_input(prompt=""):
            gobbled.write(prompt)
            line = stdin.pop(0)
            if output_includes_input:
                gobbled.write(line + '\n')
            return line
        
        with unittest.mock.patch('builtins.input', side_effect=send_input):
            with unittest.mock.patch('sys.stdout', new=gobbled) as fake_out:
                func()
                output = fake_out.getvalue().strip()
                if ignore_whitespace:
                    output = _ignore_whitespace(output)
                if ignore_case:
                    output = _ignore_case(output)

                self.assertEquals(stdout, output,
                                  "Expected: {}\nGot: {}".format(stdout, output))


    def assertIOFromFileEquals(self, func, stdin, stdout_file,
                               ignore_whitespace=True, ignore_case=True,
                               output_includes_input=True):
        with open(stdout_file, 'r') as f:
            stdout = f.read().strip()
            return self.assertIOEquals(func, stdin, stdout,
                                       ignore_whitespace, ignore_case,
                                       output_includes_input)
    

"""
The following code is a copy of the Gradescope provided unittest wrapper
to output results in the Gradescope JSON format.

https://github.com/gradescope/gradescope-utils/blob/master/gradescope_utils/autograder_utils/json_test_runner.py
"""
import sys
import time
import json

from functools import wraps
from unittest import result
from unittest.signals import registerResult


class JSONTestResult(result.TestResult):
    """A test result class that can print formatted text results to a stream.

    Used by JSONTestRunner.
    """
    def __init__(self, stream, descriptions, verbosity, results, leaderboard,
                 failure_prefix):
        super(JSONTestResult, self).__init__(stream, descriptions, verbosity)
        self.descriptions = descriptions
        self.results = results
        self.leaderboard = leaderboard
        self.failure_prefix = failure_prefix

    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return doc_first_line
        else:
            return str(test)

    def getTags(self, test):
        return getattr(getattr(test, test._testMethodName), '__tags__', None)

    def getWeight(self, test):
        return getattr(getattr(test, test._testMethodName), '__weight__', 1)

    def getScore(self, test):
        return getattr(getattr(test, test._testMethodName), '__score__', None)

    def getNumber(self, test):
        return getattr(getattr(test, test._testMethodName), '__number__', None)

    def getVisibility(self, test):
        return getattr(getattr(test, test._testMethodName), '__visibility__', None)

    def getHideErrors(self, test):
        return getattr(getattr(test, test._testMethodName), '__hide_errors__', None)

    def getLeaderboardData(self, test):
        column_name = getattr(getattr(test, test._testMethodName), '__leaderboard_column__', None)
        sort_order = getattr(getattr(test, test._testMethodName), '__leaderboard_sort_order__', None)
        value = getattr(getattr(test, test._testMethodName), '__leaderboard_value__', None)
        return (column_name, sort_order, value)

    def startTest(self, test):
        super(JSONTestResult, self).startTest(test)

    def getOutput(self):
        if self.buffer:
            out = self._stdout_buffer.getvalue()
            err = self._stderr_buffer.getvalue()
            if err:
                if not out.endswith('\n'):
                    out += '\n'
                out += err
            return out

    def buildResult(self, test, err=None):
        failed = err is not None
        weight = self.getWeight(test)
        tags = self.getTags(test)
        number = self.getNumber(test)
        visibility = self.getVisibility(test)
        hide_errors_message = self.getHideErrors(test)
        score = self.getScore(test)
        output = self.getOutput() or ""
        if err:
            if hide_errors_message:
                output += hide_errors_message
            else:
                if output:
                    # Create a double newline if output is not empty
                    if output.endswith('\n'):
                        output += '\n'
                    else:
                        output += '\n\n'
                output += "{0}{1}\n".format(self.failure_prefix, err[1])
        result = {
            "name": self.getDescription(test),
        }
        if score is not None or weight is not None:
            if weight is None:
                weight = 0.0
            if score is None:
                score = 0.0 if failed else weight
            result["score"] = score
            result["max_score"] = weight
             # Also mark failure if points are lost
            failed |= score < weight

        result["status"] = "failed" if failed else "passed"

        if tags:
            result["tags"] = tags
        if output:
            result["output"] = output
        if visibility:
            result["visibility"] = visibility
        if number:
            result["number"] = number
        return result

    def buildLeaderboardEntry(self, test):
        name, sort_order, value = self.getLeaderboardData(test)
        return {
            "name": name,
            "value": value,
            "order": sort_order,
        }

    def processResult(self, test, err=None):
        if self.getLeaderboardData(test)[0]:
            self.leaderboard.append(self.buildLeaderboardEntry(test))
        else:
            self.results.append(self.buildResult(test, err))

    def addSuccess(self, test):
        super(JSONTestResult, self).addSuccess(test)
        self.processResult(test)

    def addError(self, test, err):
        super(JSONTestResult, self).addError(test, err)
        # Prevent output from being printed to stdout on failure
        self._mirrorOutput = False
        self.processResult(test, err)

    def addFailure(self, test, err):
        super(JSONTestResult, self).addFailure(test, err)
        self._mirrorOutput = False
        self.processResult(test, err)


class JSONTestRunner(object):
    """A test runner class that displays results in JSON form.
    """
    resultclass = JSONTestResult

    def __init__(self, stream=sys.stdout, descriptions=True, verbosity=1,
                 failfast=False, buffer=True, visibility=None,
                 stdout_visibility=None, post_processor=None,
                 failure_prefix="Test Failed: "):
        """
        Set buffer to True to include test output in JSON


        post_processor: if supplied, will be called with the final JSON
        data before it is written, allowing the caller to overwrite the
        test results (e.g. add a late penalty) by editing the results
        dict in the first argument.

        failure_prefix: prepended to the output of each test's json
        """
        self.stream = stream
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer
        self.post_processor = post_processor
        self.json_data = {
            "tests": [],
            "leaderboard": [],
        }
        if visibility:
            self.json_data["visibility"] = visibility
        if stdout_visibility:
            self.json_data["stdout_visibility"] = stdout_visibility
        self.failure_prefix = failure_prefix

    def _makeResult(self):
        return self.resultclass(self.stream, self.descriptions, self.verbosity,
                                self.json_data["tests"], self.json_data["leaderboard"],
                                self.failure_prefix)

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        registerResult(result)
        result.failfast = self.failfast
        result.buffer = self.buffer
        startTime = time.time()
        startTestRun = getattr(result, 'startTestRun', None)
        if startTestRun is not None:
            startTestRun()
        try:
            test(result)
        finally:
            stopTestRun = getattr(result, 'stopTestRun', None)
            if stopTestRun is not None:
                stopTestRun()
        stopTime = time.time()
        timeTaken = stopTime - startTime

        self.json_data["execution_time"] = format(timeTaken, "0.2f")

        total_score = 0
        for test in self.json_data["tests"]:
            total_score += test.get("score", 0.0)
        self.json_data["score"] = total_score

        if self.post_processor is not None:
            self.post_processor(self.json_data)

        json.dump(self.json_data, self.stream, indent=4)
        self.stream.write('\n')
        return result



class weight(object):
    """Simple decorator to add a __weight__ property to a function

    Usage: @weight(3.0)
    """
    def __init__(self, val):
        self.val = val

    def __call__(self, func):
        func.__weight__ = self.val
        return func


class number(object):
    """Simple decorator to add a __number__ property to a function

    Usage: @number("1.1")

    This field will then be used to sort the test results on Gradescope.
    """

    def __init__(self, val):
        self.val = str(val)

    def __call__(self, func):
        func.__number__ = self.val
        return func

class visibility(object):
    """Simple decorator to add a __visibility__ property to a function

    Usage: @visibility("hidden")

    Options for the visibility field are as follows:

    - `hidden`: test case will never be shown to students
    - `after_due_date`: test case will be shown after the assignment's due date has passed.
      If late submission is allowed, then test will be shown only after the late due date.
    - `after_published`: test case will be shown only when the assignment is explicitly published from the "Review Grades" page
    - `visible` (default): test case will always be shown
    """

    def __init__(self, val):
        self.val = val

    def __call__(self, func):
        func.__visibility__ = self.val
        return func


class hide_errors(object):
    """Simple decorator to add a __hide_errors__ property to a function

    Usage: @hide_errors("Error message to be shown upon test failure")

    Used to hide the particular source of an error which caused a test to fail.
    Otherwise, a test's particular assertions can be seen by students.
    """

    def __init__(self, val="Test failed"):
        self.val = val

    def __call__(self, func):
        func.__hide_errors__ = self.val
        return func


class tags(object):
    """Simple decorator to add a __tags__ property to a function

    Usage: @tags("concept1", "concept2")
    """
    def __init__(self, *args):
        self.tags = args

    def __call__(self, func):
        func.__tags__ = self.tags
        return func


class leaderboard(object):
    """Decorator that indicates that a test corresponds to a leaderboard column

    Usage: @leaderboard("high_score"). The string parameter indicates
    the name of the column on the leaderboard

    Then, within the test, set the value by calling
    kwargs['set_leaderboard_value'] with a value. You can make this convenient by
    explicitly declaring a set_leaderboard_value keyword argument, eg.

    ```
    def test_highscore(set_leaderboard_value=None):
        set_leaderboard_value(42)
    ```

    """

    def __init__(self, column_name, sort_order='desc'):
        self.column_name = column_name
        self.sort_order = sort_order

    def __call__(self, func):
        func.__leaderboard_column__ = self.column_name
        func.__leaderboard_sort_order__ = self.sort_order

        def set_leaderboard_value(x):
            wrapper.__leaderboard_value__ = x

        @wraps(func)
        def wrapper(*args, **kwargs):
            kwargs['set_leaderboard_value'] = set_leaderboard_value
            return func(*args, **kwargs)

        return wrapper


class partial_credit(object):
    """Decorator that indicates that a test allows partial credit

    Usage: @partial_credit(test_weight)

    Then, within the test, set the value by calling
    kwargs['set_score'] with a value. You can make this convenient by
    explicitly declaring a set_score keyword argument, eg.

    ```
    @partial_credit(10)
    def test_partial(set_score=None):
        set_score(4.2)
    ```

    """

    def __init__(self, weight):
        self.weight = weight

    def __call__(self, func):
        func.__weight__ = self.weight

        def set_score(x):
            wrapper.__score__ = x

        @wraps(func)
        def wrapper(*args, **kwargs):
            kwargs['set_score'] = set_score
            return func(*args, **kwargs)

        return wrapper


"""
Handle the generation of a Gradescope autograder zip file.
"""
import os
import datetime
from zipfile import ZipFile

RUN_AUTOGRADER_TEMPALTE = """#!/bin/bash

cd /autograder/source
cp -r /autograder/submission/{} .
python3 {} > /autograder/results/results.json
"""

SETUP_TEMPLATE = """#!/bin/bash

apt install python3
"""


def generate_autograder_zip(submission_file, test_file):
    print("Generating autograder.zip")
    # Create the zip file
    with ZipFile('autograder.zip', 'w') as zf:
        # Write required scripts
        zf.writestr('run_autograder', RUN_AUTOGRADER_TEMPALTE.format(submission_file, test_file))
        zf.writestr('setup.sh', SETUP_TEMPLATE)
        # Write the test file
        zf.write(test_file)
        # Write the current file, tool.py
        zf.write('tool.py')

        # Find any non-submission files and write them
        for filename in os.listdir('.'):
            if filename.startswith("autograder-"):
                continue
            if filename not in ['autograder.zip', submission_file, test_file, 'tool.py']:
                print(f"\tFound extra file {filename} in directory, should this be included? (y/n)", end=' ')
                if input().lower() == 'y':
                    zf.write(filename)
                    print(f"\tAdded {filename} to autograder.zip")
                else:
                    print(f"\tNot including {filename}")


"""
Handles user interaction or lack thereof.
"""

def main():
    # save a copy of the autograder just in case
    if os.path.exists('autograder.zip'):
        dateandtime = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        os.rename('autograder.zip', f'autograder-{dateandtime}.zip')

    submission_file = None
    test_file = None

    for filename in os.listdir('.'):
        if filename == 'tool.py':
            continue
        if not filename.endswith('.py'):
            continue

        if filename.startswith('test') and not test_file:
            test_file = filename
            continue
        elif filename.startswith('test') and test_file:
            print("Found multiple possible test files: {} and {}".format(test_file, filename))
            print("Please remove one of them and try again")
            return

        if not filename.startswith('test') and not submission_file:
            submission_file = filename
            continue
        elif not filename.startswith('test') and submission_file:
            print("Found multiple possible submission files: {} and {}".format(submission_file, filename))
            print("Please remove one of them and try again")
            return 

    if not submission_file:
        print("No submission file found, please add a file to the directory and try again")
        return
    if not test_file:
        print("No test file found, please add a file to the directory and try again")
        return

    print("Executing tests")
    # load tests from the test file
    gobbled = io.StringIO()
    with unittest.mock.patch('sys.stdout', new=gobbled):
        suite = unittest.TestLoader().loadTestsFromName(test_file[:-3])
        runner = JSONTestRunner(visibility='visible', stream=sys.stdout)
        runner.run(suite)

    for test in runner.json_data["tests"]:
        print(f"\t{test['name']}", test["status"])
        if test["status"] != "passed":
            print("\tError: test {} did not pass".format(test["name"]))
            print("\tPlease fix the test or solution and try again")
            return

    generate_autograder_zip(submission_file, test_file)


if __name__ == '__main__':
    main()
elif __name__ == 'tool':
    # If we're being imported, run the tests
    suite = unittest.defaultTestLoader.discover('.')
    JSONTestRunner(visibility='visible', stream=sys.stdout).run(suite)

