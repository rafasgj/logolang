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

"""Implement the compiler backend."""

import logging
import re


from logolang.syntrans import parse_program
from logolang.symtable import get_symbols_by_class
from logolang.errors import LogoParserError, LogoLinkerError


def init_code(start):
    """Initialize code."""
    logging.log(7, "init_code: %s", start)
    # .START
    code = [f".START {start}"]
    functions = {
        k: v
        for k, v in get_symbols_by_class("FUNCTION").items()
        if v["usage"] > 0
    }

    # .INIT
    if any(
        v
        for v in get_symbols_by_class("FUNCTION").values()
        if v["usage"] > 0 and v.get("graphics", False)
    ):
        code.extend(["", ".INIT 200 200 400 400"])
    # .DATA
    symbols = []
    # symbols = [
    #     arg
    #     for arg in {
    #         arg: (get_symbols_by_class("VAR") or {}).get(arg)
    #         for k, v in primitives.items()
    #         for arg in v.get("__uses", [])
    #         if k in functions.keys() or v.get("target") is functions.keys()
    #     }.values()
    #     if arg is not None
    # ]
    symbols.extend(
        [
            sym
            for sym in (get_symbols_by_class("VAR") or {}).values()
            if sym["usage"] > 0
        ]
    )
    if symbols:
        def sym_value(sym):
            return f"{sym.get('value', sym.get('datatype', lambda: 0)())}"
        
        logging.log(7, "DATA section.")
        code.extend(["", ".DATA"])
        code.extend([f"{sym['fqsn']:<8} {sym_value(sym)}" for sym in symbols])
    return code


def code_gen():
    """Generate target code from 3 address code."""
    functions = {
        k: v
        for k, v in get_symbols_by_class("FUNCTION").items()
        if v["usage"] > 0
    }
    logging.log(7, "Selected functions: %d", len(functions.keys()))
    start = "__main__"
    target_code = init_code(start)
    # .CODE
    logging.log(7, "CODE section.")
    target_code.extend(["", ".CODE"])
    for name, func in functions.items():
        alias = None
        if "alias" in func:
            func = functions.get(func["alias"])
        if not func or (
            not func.get("library", False) and func["code"].code is None
        ):
            raise LogoLinkerError(
                f"Undefined function: '{name}'."
            )
        # fmt: off
        if (
            not func.get("generated", False)
            and not func.get("internal", False)
        ):
            # fmt: on
            logging.log(7, "Function: %s", name)
            func_code = func.get("code")
            if func_code:
                target_code.extend(func_code.gen_code())
            func["generated"] = True
            if alias:
                alias["generated"] = True
        elif not func.get("library"):
            logging.warning(
                "Function %s defined but not used:%d",
                name,
                func['lineno'],
            )
    output_code(target_code)


def output_code(target_code):
    """Output target code."""
    print("#--------------------------")
    for instr in target_code:
        ident = 0 if re.match("([.]|:|DEF)", instr) else 2
        print(f"{' '*ident}{instr}")
