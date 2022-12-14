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

"""Intermediate code data types."""

# pylint: disable=too-few-public-methods

import logging
from collections import namedtuple
import operator

from logolang.symtable import get_symbol
from logolang.errors import LogoLinkerError, InternalError


def format_value(value, value_type):
    """Format value."""
    if value_type == int:
        return f"{value:d}"
    if value_type == float:
        return f"{value:g}"
    return value


class NoOp:
    """A NoOp operation."""

    @staticmethod
    def gen_code():
        """Generate code for LogoVM."""
        return []


class ConstValue(namedtuple("ConstValue", "value datatype")):
    """Constant/Literal value implementation."""

    def __new__(cls, *args, **kwargs):
        """Initialize the namedtuple."""
        return super().__new__(cls, *args, **kwargs)

    @property
    def type(self):
        """Return datatype."""
        return self.datatype

    @property
    def is_const(self):
        """Return True if value is const."""
        return True

    def gen_code(self):
        """Generate code for LogoVM."""
        return [f"PUSH {self.value}"]


class ReferenceValue:
    """Reference to value (variable) implementation."""

    def __init__(self, symbol):
        """Initialize object."""
        self.symbol = symbol

    def __repr__(self):
        """Retrieve a string representation of the object."""
        return f"<ReferenceValue: {self.symbol['name']}>"

    def __getattr__(self, key):
        """Return a value as a property."""
        return self.symbol.get(key)

    @property
    def type(self):
        """Return datatype."""
        return self.symbol.get("datatype", float)

    @property
    def is_const(self):
        """Return True if value is const."""
        return False

    def gen_code(self):
        """Generate code for LogoVM."""
        scope = self.symbol["scope"]
        return (
            [f"LOAD {scope}.{self.symbol['name']}"]
            if scope
            else [f"LOAD {self.symbol['name']}"]
        )


class BinaryOperator(namedtuple("BinaryOperator", "op lhs rhs")):
    """Arithmetic binary operator implementation."""

    def __new__(cls, op, lhs, rhs):
        """Initialize namedtuple."""
        if lhs.type == str or rhs.type == str:
            raise InternalError("Operations for 'str' not available.")
        if lhs.type != rhs.type:
            if lhs.type == bool or rhs.type == bool:
                raise InternalError(
                    "Invalid operation with 'bool' and 'number'."
                )
        return super().__new__(cls, op, lhs, rhs)

    @property
    def type(self):
        """Return datatype."""
        if self.lhs.type == self.rhs.type:
            return self.lhs.type
        if self.lhs.type == float or self.rhs.type == float:
            return float
        return int

    @property
    def is_const(self):
        """Return True if value is const."""
        return self.lhs.is_const and self.rhs.is_const

    @property
    def value(self):
        """Return the expression value."""
        operation = {}
        if self.is_const:
            operation = {
                "+": operator.add,
                "-": operator.sub,
                "*": operator.mul,
                "/": operator.truediv,
                "%": operator.mod,
                "^": operator.pow,
            }
        return operation.get(self.op, lambda _l, _r: self.type())(
            self.lhs.value, self.rhs.value
        )

    def gen_code(self):
        """Generate code for LogoVM."""
        operators = {
            "+": ["ADD"],
            "-": ["SUB"],
            "*": ["MUL"],
            "/": ["DIV"],
            "%": ["IDIV", "POP"],
            "^": ["POW"],
        }
        return self.lhs.gen_code() + self.rhs.gen_code() + operators[self.op]


class AssignOperator(namedtuple("AssignOperator", "oper lhs rhs datatype")):
    """Assignment operator implementation."""

    def __new__(cls, *args, **kwargs):
        """Initialize namedtuple."""
        return super().__new__(cls, *args, **kwargs)

    @property
    def type(self):
        """Return datatype."""
        return self.rhs.type

    @property
    def is_const(self):
        """Return True if value is const."""
        return self.rhs.is_const

    def gen_code(self):
        """Generate code for LogoVM."""
        # Do operations over "Fully Qualified Scope Name" (fqsn).
        operators = {
            "+": [f"LOAD {self.lhs['fqsn']}", "ADD"],
            "-": [f"LOAD {self.lhs['fqsn']}", "SUB"],
            "*": [f"LOAD {self.lhs['fqsn']}", "MUL"],
            "/": [f"LOAD {self.lhs['fqsn']}", "DIV"],
            "^": [f"LOAD {self.lhs['fqsn']}", "POW"],
        }
        code = operators.get(self.oper[0], [])
        code = code[:1] + self.rhs.gen_code() + code[1:]
        code.append(f"STOR {self.lhs['fqsn']}")
        return code


class CallParam(namedtuple("CallParam", "param inout")):
    """Parameters for calling functions."""

    def __new__(cls, param, inout="in", **kwargs):
        """Initialize namedtuple."""
        return super().__new__(cls, param, inout, **kwargs)

    def gen_code(self):
        """Generate code for LogoVM."""
        # Parameter is an "output" paramater ()
        if self.inout == "out":
            return []
        if hasattr(self.param, "gen_code"):
            return self.param.gen_code()
        return f"LOAD {self.param['name']}"

    @property
    def name(self):
        """Return the parameter name."""
        return self.param["name"]


class CallProcedure:
    """Calling an existing procedure."""

    def __init__(self, symbol, params=None, **kwargs):
        """Initialize object."""

        def get_func(name):
            _func = get_symbol(name)
            if _func is None:
                raise LogoLinkerError(f"Cannot resolve function '{name}'.")
            if "alias" in _func:
                return get_func(_func["alias"])
            return _func

        self.symbol = get_func(symbol["name"])
        self.params = params or []
        for k, v in kwargs.items():
            setattr(self, k, v)

    # @property
    # def type(self):
    #     return self.symbol.get("datatype")

    # @property
    # def is_const(self):
    #     return self.symbol.get("is_const")

    def gen_code(self):
        """Generate code for LogoVM."""

        def format_instr(code_block):
            result = []
            for instr in code_block:
                if isinstance(instr, str):
                    result.append(
                        instr.format(
                            params=self.params, params_len=len(self.params)
                        )
                    )
            return result

        code = []
        for param in self.params[
            :: -1 if self.symbol.get("reverse_args", False) else 1
        ]:
            code.extend(param.gen_code())
        code.extend(format_instr(self.symbol.get("precode", [])))
        called = self.symbol.get("target") or self.symbol.get(
            "name", self.symbol["name"]
        )
        code.append(f"CALL {called}")
        code.extend(format_instr(self.symbol.get("postcode", [])))
        return code


class FunctionDefinition(namedtuple("FunctionDefinition", "symbol code")):
    """A new primitive definition."""

    def __new__(cls, symbol, code):
        """Initialize namedtuple."""
        return super().__new__(cls, symbol, code)

    def gen_code(self):
        """Generate code for LogoVM."""
        symbol = self.symbol
        if symbol.get("internal", False):
            return []
        if not symbol["usage"] > 0:
            if not symbol.get("library", False):
                logging.info(
                    "Skipping unused symbol:'%s':%d",
                    symbol["name"],
                    symbol.get("lineno", 0),
                )
            return []
        # print("FUN:", symbol['name'])
        code = ["", f"DEF {symbol['name']}:"]
        scope = f"@{symbol['name']}"
        for arg in symbol.get("argv", []):
            stor_arg = arg if arg.startswith("@") else f"{scope}.{arg}"
            code.append(f"STOR {stor_arg}")
        for entry in self.code:
            if isinstance(entry, str):
                code.append(entry.format(**symbol))
            else:
                code.extend(entry.gen_code())
        if symbol["name"] == "__main__":
            code.append("HALT")
        else:
            code.append("RET")
        return code


class RelationalOperator:
    """Code generator for relational operators."""

    def __init__(self, oper, lhs, rhs):
        """Initialize object."""
        if lhs.type == str or rhs.type == str and oper not in ["==", "<>"]:
            raise InternalError(
                "Relational operators for 'str' are not available."
            )
        if lhs.type != rhs.type:
            if lhs.type == bool or rhs.type == bool:
                raise InternalError(
                    "Invalid relation operation with 'bool' and 'number'."
                )
        self.oper = oper
        self.lhs = lhs
        self.rhs = rhs
        self.true = None
        self.false = None

    @property
    def type(self):
        """Return datatype."""
        return bool

    @property
    def is_const(self):
        """Return True if value is const."""
        return self.lhs.is_const and self.rhs.is_const

    def gen_code(self):
        """Generate code for LogoVM."""
        # This is the rule implemented for rel_op:
        #
        # if true != fall and false != fall:
        #   code = "ifTrue {test} goto <true>; goto {false}"
        # if true != fall and false == fall:
        #   code = "ifTrue {test} goto {true}"
        # if true == fall and false != fall:
        #   code = "ifFalse {testt} goto {false}"
        # else:
        #   code = []
        # code = lhs.gen_code + rhs.gen_code + code
        #
        test = {
            "<": {
                "ifTrue": ["JLESS :{true}"],
                "ifFalse": ["JMORE :{false}", "JZ :{false}"],
            },
            "<=": {
                "ifTrue": ["JLESS :{true}", "JZ :{true}"],
                "ifFalse": ["JMORE :{false}"],
            },
            ">": {
                "ifTrue": ["JMORE :{true}"],
                "ifFalse": ["JLESS :{false}", "JZ :{false}"],
            },
            ">=": {
                "ifTrue": ["JMORE :{true}", "JZ :{true}"],
                "ifFalse": ["JLESS :{false}"],
            },
            "==": {
                "ifTrue": ["JZ :{true}"],
                "ifFalse": ["JNZ :{false}"],
            },
            "<>": {
                "ifTrue": ["JNZ :{true}"],
                "ifFalse": ["JZ :{false}"],
            },
        }

        op_test = test[self.oper]
        code = []
        if all([self.true, self.false]):
            code = op_test["ifTrue"] + ["JP :{false}"]
        elif self.true and not self.false:
            code = op_test["ifTrue"]
        elif not self.true and self.false:
            code = op_test["ifFalse"]
        code = (
            self.lhs.gen_code() + self.rhs.gen_code() + ["SUB", "POP"] + code
        )
        code = [
            entry.format(
                true=self.true.name if self.true else None,
                false=self.false.name if self.false else None,
            )
            for entry in code
        ]
        return code


class BooleanValue:
    """Code generation for AND, OR and NOT."""

    def __init__(self, value):
        """Initialize object."""
        self.value = value
        self.type = bool
        self.is_const = True
        self.true = None
        self.false = None

    def gen_code(self):
        """Generate code for LogoVM."""
        if self.true is None and self.false is None:
            return [f"PUSH {0 if self.value else 1}", "CMP 0"]
        if self.value and self.true:
            return [f"JP {self.true.gen_code()[0]}"]
        if not self.value and self.false:
            return [f"JP {self.false.gen_code()[0]}"]
        return []


class BooleanOperator:
    """Code generation for AND, OR and NOT."""

    def __init__(self, oper, lhs, rhs=None):
        """Initialize object."""
        self.oper = oper
        self.lhs = lhs
        self.rhs = rhs
        self.type = bool
        self.is_const = self.lhs.is_const and (
            self.rhs is None or self.rhs.is_const
        )
        self.true = None
        self.false = None

    def __not(self):
        """NOT operator implementation."""
        self.lhs.true = self.false
        self.lhs.false = self.true
        return self.lhs.gen_code()

    def __and(self):
        """AND operator implementation."""
        # Use fallback for true values
        self.lhs.true = None
        self.rhs.true = self.true
        self.lhs.false = self.rhs.false = self.false
        return self.lhs.gen_code() + self.rhs.gen_code()

    def __or(self):
        """OR operator implementation."""
        self.lhs.true = self.rhs.true = self.true
        self.lhs.false = self.rhs.false = self.false
        return self.lhs.gen_code() + self.rhs.gen_code()

    def gen_code(self):
        """Generate code for LogoVM."""
        if self.is_const:
            value = BooleanValue(self.value)
            value.true = self.true
            value.false = self.false
            return value.code_gen()
        return {"NOT": self.__not, "AND": self.__and, "OR": self.__or}.get(
            self.oper, lambda: []
        )()


class Label:
    """A target label for a jump."""

    @staticmethod
    def __new_label():
        """Create a new label."""
        count = getattr(Label.__new_label, "count", 0) + 1
        logging.log(5, "New label: %d", count)
        setattr(Label.__new_label, "count", count)
        return f"_@trgt_{Label.__new_label.count}"

    def __init__(self, label=None):
        """Initilize the label with the given name or a unique name."""
        self.name = label if label else Label.__new_label()

    def gen_code(self):
        """Generate code for LogoVM."""
        return [f":{self.name}"]


class CodeBlock:
    """A list of statements as a coeherent block."""

    def __init__(self, block):
        """Initialize the code block."""
        self.block = block
        # for k, v in kwargs.items():
        #     setattr(self, k, v)

    def gen_code(self):
        """Generate code for LogoVM."""
        code = []
        for instr in self.block:
            if isinstance(instr, str):
                code.append(instr)
            else:
                code.extend(instr.gen_code())
        return code
