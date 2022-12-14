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

"""Logo Compiler Syntatic Analysis and Translation."""

import logging

from ply import yacc

from logolang.lexer import lexer, tokens  # noqa: F401

from logolang import codegen
from logolang.symtable import (
    push_scope,
    pop_scope,
    add_symbol,
    get_symbol,
    increase_symbol_usage,
)

from logolang.errors import InvalidExpressionType, InternalError

__parser_error = True
__parser = None

precedence = (
    ("nonassoc", "LOGIC_OP"),
    ("right", "NOT"),
    ("nonassoc", "REL_OP"),
    ("left", "ADD_OP"),
    ("left", "MUL_OP"),
    ("right", "PWR_OP"),
    ("right", "UMINUS"),
)


def p_program(p):
    """program : statement_or_decl more_statements_or_decls"""
    sym = get_symbol("__main__", "")
    sym["code"] = codegen.FunctionDefinition(sym, sym["code"])
    pop_scope()
    p[0] = __parser_error


def p_more_statements_or_decls(p):
    """
    more_statements_or_decls : statement_or_decl more_statements_or_decls
                             | empty
    """


def p_statement_or_decl_primitive_decl(p):
    """
    statement_or_decl : primitive_decl
    """


def p_statement_or_decl_statement(p):
    """
    statement_or_decl : statement
    """
    sym = get_symbol("__main__", "")
    sym["code"].append(p[1])


def p_primitive_decl(p):
    """
    primitive_decl : primitive_signature body END
    """
    p[1]["code"] = codegen.FunctionDefinition(p[1], p[2])
    pop_scope()


def p_primitive_signature(p):
    """
    primitive_signature : TO ID opt_args
    """
    p[0] = add_symbol(
        p[2], "FUNCTION", lineno=p.lineno(2), argv=p[3][::-1], argc=len(p[3])
    )
    push_scope(p[2])


def p_opt_args(p):
    """
    opt_args : COLON_ID opt_args
             | empty
    """
    if p[1] is not None:
        p[2].append(p[1])
        p[0] = p[2]
    else:
        p[0] = []


def p_body(p):
    """
    body : statement body
         | empty
    """
    p[0] = ([p[1]] + p[2]) if p[1] is not None else []


def p_statement(p):
    """
    statement : assignment_expression
               | primitive_call
               | while_statement
               | if_then_else_statement
               | expression
    """
    p[0] = p[1]


def p_primitive_call_print(p):
    """
    primitive_call : PRINT expression opt_params
    """
    sym = get_symbol(p[1])
    if sym is None:
        raise InternalError("PRINT function is not defined.")
    increase_symbol_usage(p[1])
    length = codegen.ConstValue(1 + len(p[3]), int)
    p[0] = codegen.CallProcedure(
        sym,
        [codegen.CallParam(length, int)] + p[3] + [codegen.CallParam(p[2])],
    )


def p_primitive_call_typein(p):
    """
    primitive_call : TYPEIN ID
    """
    sym = get_symbol(p[1])
    if sym is None:
        raise InternalError("TYPEIN function is not defined.")
    increase_symbol_usage(p[1])
    param = add_symbol(p[2], "VAR")
    increase_symbol_usage(param["name"])
    p[0] = codegen.CallProcedure(sym, [codegen.CallParam(param, "out")])


def p_primitive_call(p):
    """
    primitive_call : ID opt_params
    """
    sym = add_symbol(p[1], "FUNCTION")
    increase_symbol_usage(sym["name"])
    p[0] = codegen.CallProcedure(sym, p[2])


def p_opt_params(p):
    """
    opt_params : expression opt_params
               | empty
    """
    if p[1] is not None:
        p[2].append(p[1])
        p[0] = p[2]
    else:
        p[0] = []


def p_assignment_expr(p):
    """
    assignment_expression : ID ASSIGN_OP expression
    """
    # ensure ID exists with lineno
    sym = add_symbol(p[1], "VAR", lineno=p.lineno(1), datatype=p[3].type)
    if sym.get("value") is None and p[3].is_const:
        sym["value"] = p[3].value
        p[0] = codegen.NoOp()
    else:
        if sym.get("value") is None:
            sym["value"] = p[3].type()
        p[0] = codegen.AssignOperator(p[2], sym, p[3], p[3].type)


def p_expression(p):
    """
    expression : number_expression
               | string_expression
               | boolean_expression
    """
    p[0] = p[1]


def p_expression_parenthesis(p):
    """
    expression : OPEN_PAR expression CLOSE_PAR
    """
    p[0] = p[2]


def p_expression_binop(p):
    """
    expression : expression ADD_OP expression
               | expression MUL_OP expression
               | expression PWR_OP expression
    """
    if p[1].type not in [int, float]:
        raise InvalidExpressionType(p.lineno(2), p[1].type)
    if p[3].type not in [int, float]:
        raise InvalidExpressionType(p.lineno(2), p[3].type)

    p[0] = codegen.BinaryOperator(p[2], p[1], p[3])


def p_expression_uminus(p):
    "expression : ADD_OP expression %prec UMINUS"
    if p[2].type not in [int, float]:
        raise InvalidExpressionType(p.lineno(1), p[2].type)
    p[0] = codegen.BinaryOperator("*", codegen.ConstValue(-1, int), p[2])


def p_expression_id(p):
    """
    expression : COLON_ID
    """
    sym = add_symbol(p[1], "VAR")
    increase_symbol_usage(sym["name"])
    p[0] = codegen.ReferenceValue(sym)


def p_expression_random(p):
    """
    expression : RANDOM
    """
    sym = get_symbol(p[1])
    if sym is None:
        raise InternalError("RANDOM function is not defined.")
    increase_symbol_usage(p[1])
    p[0] = codegen.CallProcedure(sym, type=int, is_const=False)


def p_string_expr(p):
    """
    string_expression : STRING
    """
    p[0] = codegen.ConstValue(*p[1])


def p_number_expr(p):
    """
    number_expression : number_constant
    """
    p[0] = p[1]


def p_number_constant(p):
    """
    number_constant : NUMBER
    """
    p[0] = codegen.ConstValue(*p[1])


def p_if_then_else_statement(p):
    """
    if_then_else_statement : IF boolean_expression THEN body opt_else END
    """
    p[2].true = None
    p[2].false = codegen.Label()
    if p[5] is not None:
        force_jp = codegen.BooleanValue(True)
        force_jp.true = codegen.Label()
        p[0] = codegen.CodeBlock(
            [p[2]] + p[4] + [force_jp, p[2].false] + p[5] + [force_jp.true]
        )
    else:
        p[0] = codegen.CodeBlock([p[2]] + p[4] + [p[2].false, p[5]])


def p_opt_else(p):
    """
    opt_else : ELSE body
             | empty
    """
    p[0] = [] if p[1] is None else p[2]


def p_while_statement(p):
    """
    while_statement : WHILE boolean_expression body END
    """
    start_st = codegen.Label()
    next_st = codegen.Label()
    jp_start = codegen.BooleanValue(True)
    jp_start.true = start_st
    p[2].true = None  # fall
    p[2].false = next_st
    p[0] = codegen.CodeBlock([start_st, p[2]] + p[3] + [jp_start, next_st])


def p_boolean_expression(p):
    """
    boolean_expression :  boolean_const
    """
    p[0] = p[1]


def p_boolean_const(p):
    """
    boolean_const :  BOOLEAN
    """
    p[0] = codegen.BooleanValue(p[1].upper() in ["TRUE", "YES"])


def p_boolean_relop(p):
    """
    boolean_expression :  expression REL_OP expression
    """
    for i in [1, 3]:
        if p[i].type == bool:
            raise InvalidExpressionType(p.lineno(i), bool)
    if p[1].type == str or p[3].type == str:
        if p[1].type != p[3].type:
            raise InvalidExpressionType(
                p.lineno(2), "Cannot compare STRING to other data type"
            )
        if p[2] not in ["==", "<>"]:
            raise InvalidExpressionType(
                p.lineno(2), "Can only compare STRING equality"
            )
    p[0] = codegen.RelationalOperator(p[2], p[1], p[3])


def p_boolean_expression_logicop(p):
    """
    boolean_expression :  boolean_expression LOGIC_OP boolean_expression
    """
    for i in [1, 3]:
        if p[i].type != bool:
            raise InvalidExpressionType(p.lineno(i), p[i].type)
    p[0] = codegen.BooleanOperator(p[2], p[1], p[3])


def p_empty(p):
    """empty :"""
    # An empty production rule.
    p[0] = None


def p_error(p):
    """Provide a simple error message."""
    global parser_error  # pylint: disable=global-statement,invalid-name
    parser_error = True
    if p:
        logging.error(
            "Invalid Token:%d: %s (%s)", p.lexer.lineno, p.value, p.type
        )
        # Just discard the token and tell the parser it's okay.
        __parser.errok()
    else:
        logging.error("Syntax error at EOF.")


def parse_program(source):
    """Parse LogoASM program."""
    global tokens  # pylint: disable=global-variable-undefined, invalid-name
    global __parser
    # Parse program
    __parser = yacc.yacc(start="program", debug=True)
    return __parser.parse(source, lexer=lexer(), tracking=False)
