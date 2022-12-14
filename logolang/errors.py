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

"""Logolang compiler errors."""


class LogoLexerError(Exception):
    """Lexer exception base class."""


class InvalidCharacter(LogoLexerError):
    """Lexer invalid character."""

    def __init__(self, lineno, char):
        """Initialize error with detected invalid char."""
        super().__init__(f"Illegal character::{lineno}:{char}")


class InvalidIdentifier(LogoLexerError):
    """An invalid identifier definition."""

    def __init__(self, lineno, identifier):
        """Initialize error with invalid identifier."""
        super().__init__(f"Invalid identifier:{lineno}:{identifier}")


class LogoLinkerError(Exception):
    """Lexer exception."""

    def __init__(self, msg):
        """Initialize error with detected invalid char."""
        super().__init__(f"Linker Error: {msg}")


class InternalError(Exception):
    """An invalid type was used in an expression."""

    def __init__(self, msg):
        """Initialize an Internal Error."""
        super().__init__(f"InternalError:{msg}")


class LogoParserError(Exception):
    """Base class for Parser errors."""

    def __init__(self, lineno, msg):
        """Initialize a Logo Parser Error."""
        super().__init__(f"{self.__class__.__name__}:{lineno}:{msg}")


class InvalidExpressionType(LogoParserError):
    """An invalid type was used in an expression."""

    def __init__(self, lineno, datatype, msg="Invalid data type"):
        """Initialize an Invalid Expression Type exception."""
        super().__init__(lineno, f"{msg}:{repr(datatype)}")


class SymbolRedeclaration(LogoParserError):
    """A symbol was redeclared with a different semantic."""

    def __init__(self, lineno, symbol, original):
        """Initialize a Symbol Redeclaration exception."""
        super().__init__(
            lineno, f"Redefining symbol {symbol} defined at {original}"
        )
