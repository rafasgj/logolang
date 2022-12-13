# This file is part of logolang
#
# Copyright (C) 2022 Rafael Guterres Jeffman
#
# This software is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <https://www.gnu.org/licenses/>.

"""Logolang compiler driver."""

import sys
import logging
import argparse

from logolang.lexer import tokens, lexer
from logolang.syntrans import parse_program
from logolang.symtable import push_scope, add_symbol
from logolang.logolib import initialize_standard_library
from logolang.compiler import code_gen
import logolang.errors


def cli_parser():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="LogoVM",
        description="LogoVM is a Compiler teaching tool",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="count",
        default=0,
        help="Set debug level (up to -ddd). Implies PGM/PPM graphics.",
    )
    parser.add_argument(
        "filename", nargs="?", help="LogoASM source file name."
    )

    return parser.parse_args()


def parse_command_line():
    """Parse command line arguments."""
    options = cli_parser()
    log_format = "%(levelname)s (%(funcName)s) %(message)s"
    level = 30 - (10 * (3 if options.debug > 3 else options.debug))
    logging.basicConfig(force=True, format=log_format, level=level)
    logging.addLevelName(3, "LEXER")
    logging.addLevelName(5, "PARSER")
    return options.filename


def main():
    """Entry point for the LogoVM."""
    filename = parse_command_line()
    # Load standard library
    push_scope("")
    add_symbol("__main__", "FUNCTION", lineno=0, usage=1, code=[])
    initialize_standard_library()
    # parse source code
    try:
        with (open(filename, "rt") if filename else sys.stdin) as input_file:
            if parse_program(input_file.read()):
                code_gen()
                return 0
            return 1
    except (logolang.errors.LogoLexerError, logolang.errors.LogoParserError, logolang.errors.LogoLinkerError, logolang.errors.InternalError, ) as error:
        print(str(error), file=sys.stderr)
        raise error
        return 1


if __name__ == "__main__":
    sys.exit(main())
