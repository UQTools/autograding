# Autograding

This is a simple single python file tool that can be used to easily deploy GradeScope autograders.

## Instructions

1. Download `tool.py` and place it with your assignment files.
2. Create a test suite in a file prefixed with `test_` (e.g. `test_assign.py`).

    Refer to the `test_identity.py` example in this repository.
    Ensure that your tests import the student's submission and import the `tool.py` file with `from tool import *`.
    During development, you can run your tests by running the tests file (e.g. `python3 test_assign.py`).

3. Once you are satisfied with your tests, run `tool.py` to generate an `autograder.zip` file.

    This file can be uploaded to GradeScope as an autograder.


