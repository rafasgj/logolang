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

"""Logo Compiler Symbol Table implementation."""

import logging
from logolang.errors import SymbolRedeclaration, InternalError


__symtable = {"scopes": [], "FUNCTION": {}, "VAR": {}}


def get_symbols_by_class(cls):
    """Returns all the symbols of a specific class."""
    return __symtable[cls]


def new_label(pattern):
    """Create a new unique label for the given pattern."""
    counter = 1 + getattr(new_label, pattern, 0)
    setattr(new_label, pattern, counter)
    return f"_@{pattern}_{counter}"


def push_scope(name=None):
    """Push a new scope to the symbol table."""

    def new_scope(name):
        return {"name": name, "symbols": {}}

    __symtable["scopes"].append(new_scope(name))


def pop_scope():
    """Pop the last scope, proccess, and return it."""
    scope = __symtable["scopes"].pop()
    for _, symbol in scope["symbols"].items():
        __symtable[symbol["type"]][symbol["fqsn"]] = symbol
    return scope


def current_scope():
    return ".".join(
        "@%s" % scope["name"]
        for scope in __symtable["scopes"]
        if scope["name"]
    )


def get_symbol(symbol, scopename=None, symtype=None):
    symbol = symbol.upper()
    for scope in __symtable["scopes"][::-1]:
        if scopename is None or scopename == scope["name"]:
            sym = scope["symbols"].get(symbol)
            if sym:
                if symtype is None or symtype == sym["type"]:
                    return sym
    if symtype is not None and scopename is None:
        return __symtable[symtype].get(symbol)
    return None


def add_symbol(symbol, symtype, lineno=-1, **kwargs):
    sym = get_symbol(symbol)
    if sym:
        if sym["type"] != symtype:
            raise SymbolRedeclaration(lineno, symbol, sym["lineno"])
        if sym["lineno"] >= 0:
            if "lineno" in kwargs:
                del kwargs["lineno"]
            if "value" in sym and "value" in kwargs:
                del kwargs["value"]
        if "name" in kwargs:
            raise InternalError("Cannot modify object 'name'.")
        logging.log(5, "Updating symbol:%s:%s", symbol, repr(kwargs))
        sym.update(kwargs)
    else:
        sym_scope = current_scope()
        fqsn = f"{sym_scope}.{symbol}" if sym_scope else symbol
        sym = {
            "name": symbol,
            "type": symtype,
            "lineno": lineno,
            "usage": 0,
            "scope": sym_scope,
            "fqsn": fqsn,
            **kwargs,
        }
        logging.log(
            5,
            "Adding symbol:%s:%s:%d:%s",
            symbol,
            symtype,
            lineno,
            repr(kwargs),
        )
        __symtable["scopes"][-1]["symbols"][symbol.upper()] = sym

    arg_scope = f"@{sym['name']}"
    if sym["scope"]:
        arg_scope = sym["scope"] + arg_scope
    args = [
        arg_scope + f".{arg}" if not arg.startswith("@") else arg
        for arg in sym.get("argv", [])
    ]
    sym["argv"] = args
    return sym


def increase_symbol_usage(symbol, symtype=None):
    sym = get_symbol(symbol, symtype=symtype)
    if sym is None:
        if symtype is not None:
            sym = __symtable[symtype].get(symbol)
        if sym is None:
            raise InternalError(f"Increasing unknown symbol usage: {symbol}")
    sym["usage"] += 1
    if "alias" in sym:
        sym = get_symbol(sym["alias"])
        if sym is None:
            raise InternalError(f"Increasing unknown symbol usage: {symbol}")
        sym["usage"] += 1

    for arg in sym.get("argv", []) + sym.get("uses", []):
        if sym["scope"] and not arg.startswith("@"):
            scope = ".@".join(
                lvl for lvl in [sym["scope"], sym["name"]] if lvl
            )
            fqsn = f"@{scope}.{arg}"
            increase_symbol_usage(fqsn, symtype="VAR")
        else:
            increase_symbol_usage(arg, symtype="VAR")
