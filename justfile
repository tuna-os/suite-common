# suite-common is a library subproject; it has no app to build on its own.
# These helpers are for working on the shared code in isolation.

default:
    @just --list

# Byte-compile the package to catch syntax errors without a full app build.
check:
    python3 -m compileall suite_common
