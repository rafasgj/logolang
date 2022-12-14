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

"""Logolang standard library."""

from logolang.symtable import add_symbol, push_scope, pop_scope
from logolang.codegen import FunctionDefinition


__standard_library = {
    "PRINT": {
        "library": True,
        "internal": True,
        "reverse_args": True,
        "target": "WRITE",
    },
    "TYPEIN": {
        "library": True,
        "internal": True,
        "inout": "out",
        "target": "READ",
        "postcode": ["STOR {params[0].name}"],
    },
    "RANDOM": {
        "library": True,
        "datatype": int,
        "is_const": False,
        "code": ["RAND", "PUSH 10", "MUL", "TRUNC"],
    },
    "FORWARD": {
        "library": True,
        "graphics": True,
        "args": 1,
        "argv": ["length"],
        "uses": ["_@ang"],
        "code": ["LOAD _@ang", "LOAD {argv[0]}", "CALL MOVE"],
    },
    "BACKWARD": {
        "library": True,
        "graphics": True,
        "args": 1,
        "argv": ["length"],
        "uses": ["_@ang"],
        "code": [
            "LOAD _@ang",
            "PUSH 180",
            "ADD",
            "LOAD {argv[0]}",
            "CALL MOVE",
        ],
    },
    "RIGHT": {
        "library": True,
        "graphics": True,
        "args": 1,
        "argv": ["angle"],
        "uses": ["_@ang"],
        "code": ["LOAD _@ang", "LOAD {argv[0]}", "SUB", "STOR _@ang"],
    },
    "LEFT": {
        "library": True,
        "graphics": True,
        "args": 1,
        "argv": ["angle"],
        "uses": ["_@ang"],
        "code": ["LOAD _@ang", "LOAD {argv[0]}", "ADD", "STOR _@ang"],
    },
    "PENUP": {
        "library": True,
        "graphics": True,
        "args": 0,
        "argv": [],
        "code": ["UNSET 0"],
    },
    "PENDOWN": {
        "library": True,
        "graphics": True,
        "args": 0,
        "argv": [],
        "code": ["SET 0"],
    },
    "HEADING": {
        "library": True,
        "graphics": True,
        "args": 0,
        "argv": [],
        "uses": ["_@ang"],
        "code": ["LOAD _@ang"],
    },
    "SETXY": {
        "library": True,
        "graphics": True,
        "args": 2,
        "argv": ["x", "y"],
        "code": ["LOAD {argv[0]}", "LOAD {argv[1]}", "MVTO"],
    },
    "WIPECLEAN": {
        "library": True,
        "graphics": True,
        "target": "CLRSCR",
    },
    "FO": {
        "library": True,
        "graphics": True,
        "alias": "FORWARD",
    },
    "BW": {
        "library": True,
        "graphics": True,
        "alias": "BACKWARD",
    },
    "RT": {
        "library": True,
        "graphics": True,
        "alias": "RIGHT",
    },
    "LT": {
        "library": True,
        "graphics": True,
        "alias": "LEFT",
    },
    "PU": {
        "library": True,
        "graphics": True,
        "alias": "PENUP",
    },
    "PD": {
        "library": True,
        "graphics": True,
        "alias": "PENDOWN",
    },
    "WC": {
        "library": True,
        "graphics": True,
        "alias": "WIPECLEAN",
    },
}


def initialize_standard_library():
    add_symbol("_@ang", "VAR", lineno=-1)
    for name, data in __standard_library.items():
        sym = add_symbol(name, "FUNCTION", lineno=-1, **data)
        sym["code"] = FunctionDefinition(sym, data.get("code", []))
        push_scope(name)
        new_args = []
        for arg in sym.get("argv", []):
            symarg = add_symbol(arg, "VAR", lineno=-1)
            symarg["fqsn"] = (
                f"{symarg['scope']}.{arg}"
                if symarg["scope"] and not arg.startswith("@")
                else arg
            )
            new_args.append(symarg["fqsn"])
        sym["argv"] = new_args
        pop_scope()
