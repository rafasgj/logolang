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

"""Logo Compiler Lexer."""

import logging

from ply import lex
from ply.lex import TOKEN

from logolang.errors import InvalidCharacter, InvalidIdentifier

# Characters to be ignored by lexer.
t_ignore = " \t\r"  # pylint: disable=invalid-name

RESERVED = (
    "BOOLEAN",
    "IF",
    "THEN",
    "ELSE",
    "WHILE",
    "TO",
    "END",
    "NOT",
    "ASSIGN_OP",
    "REL_OP",
    "LOGIC_OP",
    "PRINT",
    "TYPEIN",
    "RANDOM",
)
NON_RESERVED = ("NUMBER", "STRING", "ID", "COLON_ID")
OPERATORS = {
    r"\^": "PWR_OP",
    "[+-]": "ADD_OP",
    "[/*%]": "MUL_OP",
    "[(]": "OPEN_PAR",
    "[)]": "CLOSE_PAR",
}
BOOLEAN_TOKENS = ("TRUE", "FALSE", "YES", "NO")
LOGIC_TOKENS = ("AND", "OR")

tokens = tuple(RESERVED + NON_RESERVED + tuple(set(OPERATORS.values())))

globals().update({f"t_{v}": k for k, v in OPERATORS.items()})

t_ASSIGN_OP = "[-+*/]?="  # pylint: disable=invalid-name
t_REL_OP = "==|<>|>=|<=|>|<"  # pylint: disable=invalid-name


@TOKEN(r"[_a-zA-Z][_a-zA-Z0-9]*")
def t_ID(token):  # pylint: disable=invalid-name
    """Extract an identifier."""
    uppervalue = token.value.upper()
    if uppervalue in RESERVED:
        logging.log(3, "RESERVED: '%s'", token.value)
        token.type = uppervalue
    elif uppervalue in BOOLEAN_TOKENS:
        token.value = uppervalue
        token.type = "BOOLEAN"
    elif uppervalue in LOGIC_TOKENS:
        token.value = uppervalue
        token.type = "LOGIC_OP"
    else:
        token.type = "ID"
    logging.log(3, "%s:%d:'%s'", token.type, token.lexer.lineno, token.value)
    return token


@TOKEN(r"[:][_a-zA-Z][_a-zA-Z0-9]*")
def t_COLON_ID(token):  # pylint: disable=invalid-name
    """Extract an identifier with a colon."""
    identifier = token.value[1:]
    if identifier.upper in RESERVED:
        raise InvalidIdentifier(token.lexer.lineno, identifier)
    token.value = identifier
    logging.log(3, "%s:%d:'%s'", token.type, token.lexer.lineno, token.value)
    return token


@TOKEN(r"[+-]?\d+([.]\d*)?")
def t_NUMBER(token):  # pylint: disable=invalid-name
    """Extract a number."""
    if "." in token.value:
        token.value = (float(token.value), float)
    else:
        token.value = (int(token.value), int)
    logging.log(
        3,
        "NUMBER:%d:(%s, %s)",
        token.lexer.lineno,
        token.value,
        type(token.value).__name__,
    )
    return token


@TOKEN(r"'[^']*'|\"[^\"]*\"")
def t_STRING(token):  # pylint: disable=invalid-name
    """Extract an string."""
    token.value = (token.value, str)
    logging.log(3, "STRING:%d:(%s, str)", token.lexer.lineno, token.value)
    return token


@TOKEN(r"[#][^\n]*")
def t_COMMENT(token):  # pylint: disable=invalid-name
    """Ignore comments."""
    logging.log(3, "Comment:%d:'%s'", token.lexer.lineno, token.value)


@TOKEN(r"\n+")
def t_newline(token):
    """Count new lines."""
    logging.log(3, "NL: %d", len(token.value))
    # For some unknown reason, new lines are being doubled
    token.lexer.lineno += len(token.value)


def lexer():
    """Create a new lexer object."""
    return lex.lex()


def t_error(tokenizer):
    """Report lexer error."""
    raise InvalidCharacter(tokenizer.lexer.lineno, tokenizer.value[0])
