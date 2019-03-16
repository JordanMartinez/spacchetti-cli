import subprocess
import os.path
import signal
import time
import difflib
import platform
import json


def fail(msg):
    """
    Print a message and exit
    """
    print(msg)
    exit(1)


def call(expected_code, command, failure_msg, expected_output_fixture=None):
    """
    Try to run a command and exit if fails
    """
    try:
        out = subprocess.check_output(command, stderr=subprocess.STDOUT).decode('utf-8')
    except subprocess.CalledProcessError as e:
        if e.returncode == expected_code:
            out = e.output.decode('utf-8')
        else:
            print("FAILURE: " + failure_msg)
            print("Program output:")
            fail(e.output.decode('utf-8'))

    # Optionally check the output matches
    if expected_output_fixture is not None:
        with open('../fixtures/' + expected_output_fixture, 'r', encoding='utf-8') as expected:
            # We have to do this crazy lines whitespace cleaning because of Windows line endings
            exp_lines = expected.readlines()
            res_lines = out.splitlines(keepends=False)
            expected_str = '\n'.join([line.strip() for line in exp_lines])
            result_str = '\n'.join([line.strip() for line in res_lines])
            if expected_str != result_str:
                diff = difflib.context_diff(
                    [line + "\n" for line in res_lines],
                    exp_lines,
                    fromfile='generated',
                    tofile='expected'
                )
                print("\nOutput doesn't match fixture!\n")
                fail("\nDiff:\n" + ''.join(diff))

    return out


def expect_success(command, *args):
    print('Expecting success from: "' + ' '.join(command) + '"')
    return call(0, command, *args)


def expect_failure(command, *args):
    print('Expecting failure from: "' + ' '.join(command) + '"')
    return call(1, command, *args)


# Credit: https://stackoverflow.com/questions/4789837/
def run_for(delay, command):
    """
    Run a command and kill it after a certain delay
    """
    print('Going to run this for {}s: "{}"'.format(delay, ' '.join(command)))
    with open(os.devnull, 'w') as FNULL:
        # Windows wants a different treatment, see this issue:
        # https://stackoverflow.com/questions/7085604/
        if platform.system() == 'Windows':
            wrapper_command = "start python3 windows_test_wrapper.py " + str(delay) + " '" + json.dumps(command) + "'"
            print("Running the following command: \"" + wrapper_command + "\"")
            p = subprocess.Popen(wrapper_command, shell=True)
            # Terminate the whole shell after enough time has passed
            time.sleep(delay + 1)
            subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=p.pid))
        else:
            process = subprocess.Popen(command, stdout=FNULL, stderr=FNULL)
            time.sleep(delay)
            process.send_signal(signal.SIGINT)


def check_fixture(name):
    fixture = '../fixtures/' + name
    with open(name, 'r', encoding='utf-8') as result, \
         open(fixture, 'r', encoding='utf-8') as expected:
        res_lines = result.readlines()
        exp_lines = expected.readlines()
        res_str = ''.join(res_lines)
        exp_str = ''.join(exp_lines)
        if res_str != exp_str:
            print("\nFAILURE: Fixture doesn't match")
            diff = difflib.context_diff(res_lines, exp_lines, fromfile='generated', tofile='expected')
            fail("\nDiff:\n" + ''.join(diff))
        else:
            print('Successfully verified fixture for "{}"'.format(name))
