import time

from setuptools_scm import ScmVersion
from setuptools_scm._integration.pyproject_reading import read_pyproject
from setuptools_scm._modify_version import _bump_regex
from setuptools_scm import version


def custom(version: ScmVersion) -> str:
    scheme = read_pyproject(tool_name="setuptools_scm_custom").section["version_scheme"]
    return _parse_version_for_scheme(version, scheme)


def custom_local(version: ScmVersion) -> str:
    scheme = read_pyproject(tool_name="setuptools_scm_custom").section["local_scheme"]
    return _parse_version_for_scheme(version, scheme)


def _parse_version_for_scheme(version: ScmVersion, scheme: str) -> str:
    while True:
        start = scheme.find("[")
        if start > -1:
            end = _find_matching_bracket(scheme, start)
            group = scheme[start + 1 : end]
            scheme = scheme.replace(
                f"[{group}]", _parse_version_for_scheme(version, group)
            )
        else:
            if "?" not in scheme:
                scheme = _do_brace_expansion(scheme, version)
            elif ":" not in scheme:
                test = scheme[scheme.find("?") + 1 :]
                test_result = _evaluate_test(test, version)
                if test_result:
                    scheme = _do_brace_expansion(scheme[0 : scheme.find("?")], version)
                else:
                    scheme = ""
            else:
                test = scheme[scheme.find("?") + 1 : scheme.find(":")]
                test_result = _evaluate_test(test, version)
                if test_result:
                    scheme = _do_brace_expansion(scheme[0 : scheme.find("?")], version)
                else:
                    scheme = _do_brace_expansion(
                        scheme[scheme.find(":") + 1 :], version
                    )
            break
    return scheme


def _evaluate_test(test: str, version: ScmVersion) -> bool:
    if "==" in test:
        operator = "=="
    elif ">" in test:
        operator = ">"
    elif "<" in test:
        operator = "<"
    else:
        raise ValueError(f"unknown operator in {test}")

    first_arg = _do_brace_expansion(test[0 : test.find(operator)], version)
    second_arg = _do_brace_expansion(
        test[test.find(operator) + len(operator) :], version
    )
    if operator == "==":
        rtn = first_arg == second_arg
    elif operator == ">":
        rtn = first_arg > second_arg
    elif operator == "<":
        rtn = first_arg < second_arg
    return rtn


def _do_brace_expansion(group: str, version: ScmVersion) -> str:
    index = 0
    while index < len(group):
        start = group.find("{", index)
        if start > -1:
            index = _find_matching_bracket(group, start, brackets={"{": "}"})
            key = group[start + 1 : index]
            if key == "next_tag":
                value = _bump_regex(str(version.tag))
            else:
                value = str(version.__getattribute__(key))
            group = group.replace("{" + key + "}", value)
        else:
            break
    return group


def _find_matching_bracket(string, index, brackets: dict[str, str] = None):
    openers = brackets or {"[": "]"}
    closers = {v: k for k, v in openers.items()}
    stack = []
    result = []

    if string[index] not in openers:
        raise ValueError(f"char at index {index} was not an opening brace")

    for ii in range(index, len(string)):
        c = string[ii]

        if c in openers:
            stack.append([c, ii])
        elif c in closers:
            if not stack:
                raise ValueError(
                    f"tried to close brace without an open at position {index}"
                )

            pair, idx = stack.pop()

            if pair != closers[c]:
                raise ValueError(f"mismatched brace at position {index}")

            if idx == index:
                return ii

    if stack:
        raise ValueError(f"no closing brace at position {index}")

    return result


if __name__ == "__main__":
    _find_matching_bracket("test[fsdfdf]", 4)
