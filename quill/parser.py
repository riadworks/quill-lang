from quill import ast_nodes as A
from quill.errors import ParseError
from quill.tokens import T, Token

COMPARISON_OPS = {T.EQEQ: "==", T.NEQ: "!=", T.LT: "<", T.GT: ">", T.LE: "<=", T.GE: ">="}
ADD_OPS = {T.PLUS: "+", T.MINUS: "-"}
MUL_OPS = {T.STAR: "*", T.SLASH: "/", T.PERCENT: "%", T.SLASHSLASH: "//"}
AUG_ASSIGN_OPS = {T.PLUSEQ: "+", T.MINUSEQ: "-", T.STAREQ: "*", T.SLASHEQ: "/"}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # ---------- token helpers ----------

    def peek(self, offset=0) -> Token:
        i = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[i]

    def check(self, *types) -> bool:
        return self.peek().type in types

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != T.EOF:
            self.pos += 1
        return tok

    def match(self, *types) -> bool:
        if self.check(*types):
            self.advance()
            return True
        return False

    def expect(self, type_, msg) -> Token:
        if not self.check(type_):
            got = self.peek()
            raise ParseError(f"{msg} (got {got.type.name})", got.line)
        return self.advance()

    def skip_newlines(self):
        while self.match(T.NEWLINE):
            pass

    # ---------- program ----------

    def parse_program(self) -> list:
        stmts = []
        self.skip_newlines()
        while not self.check(T.EOF):
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        return stmts

    def parse_block(self) -> list:
        self.expect(T.COLON, "expected ':' to start a block")
        if not self.check(T.NEWLINE):
            # single-line form, e.g. `if x: return 1` - also the only way an anonymous
            # function passed inline as a call argument can have a body at all, since
            # the lexer suppresses INDENT/NEWLINE entirely while inside parentheses.
            stmt = self.parse_stmt()
            self.match(T.NEWLINE)
            return [stmt]
        self.advance()  # NEWLINE
        self.expect(T.INDENT, "expected an indented block")
        stmts = []
        self.skip_newlines()
        while not self.check(T.DEDENT, T.EOF):
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        self.expect(T.DEDENT, "expected the block to end (dedent)")
        return stmts

    # ---------- statements ----------

    def parse_stmt(self):
        if self.check(T.LET):
            return self.parse_let()
        if self.check(T.FN) and self.peek(1).type == T.NAME:
            return self.parse_fn_decl()
        if self.check(T.IF):
            return self.parse_if()
        if self.check(T.WHILE):
            return self.parse_while()
        if self.check(T.FOR):
            return self.parse_for()
        if self.check(T.RETURN):
            return self.parse_return()
        if self.check(T.BREAK):
            tok = self.advance()
            return A.BreakStmt(line=tok.line)
        if self.check(T.CONTINUE):
            tok = self.advance()
            return A.ContinueStmt(line=tok.line)
        if self.check(T.CLASS):
            return self.parse_class()
        if self.check(T.TRY):
            return self.parse_try()
        if self.check(T.RAISE):
            return self.parse_raise()
        if self.check(T.IMPORT):
            return self.parse_import()
        return self.parse_expr_or_assign_stmt()

    def parse_let(self):
        tok = self.advance()
        names = [self.expect(T.NAME, "expected a variable name after 'let'").value]
        while self.match(T.COMMA):
            names.append(self.expect(T.NAME, "expected a variable name").value)
        self.expect(T.EQ, "expected '=' after variable name")
        expr = self.parse_expr()
        return A.LetStmt(names, expr, line=tok.line)

    def parse_params(self):
        params = []
        self.expect(T.LPAREN, "expected '(' before parameter list")
        if not self.check(T.RPAREN):
            params.append(self.expect(T.NAME, "expected a parameter name").value)
            while self.match(T.COMMA):
                params.append(self.expect(T.NAME, "expected a parameter name").value)
        self.expect(T.RPAREN, "expected ')' after parameter list")
        return params

    def parse_fn_decl(self):
        tok = self.advance()
        name = self.expect(T.NAME, "expected a function name").value
        params = self.parse_params()
        body = self.parse_block()
        fn = A.FnExpr(params, body, name=name, line=tok.line)
        return A.LetStmt([name], fn, line=tok.line)

    def parse_if(self):
        tok = self.advance()
        branches = []
        cond = self.parse_expr()
        body = self.parse_block()
        branches.append((cond, body))
        while self.check(T.ELIF):
            self.advance()
            c = self.parse_expr()
            b = self.parse_block()
            branches.append((c, b))
        else_body = None
        if self.check(T.ELSE):
            self.advance()
            else_body = self.parse_block()
        return A.IfStmt(branches, else_body, line=tok.line)

    def parse_while(self):
        tok = self.advance()
        cond = self.parse_expr()
        body = self.parse_block()
        return A.WhileStmt(cond, body, line=tok.line)

    def parse_for(self):
        tok = self.advance()
        names = [self.expect(T.NAME, "expected a loop variable name").value]
        while self.match(T.COMMA):
            names.append(self.expect(T.NAME, "expected a loop variable name").value)
        self.expect(T.IN, "expected 'in' after loop variable")
        iterable = self.parse_expr()
        body = self.parse_block()
        return A.ForStmt(names, iterable, body, line=tok.line)

    def parse_return(self):
        tok = self.advance()
        expr = None
        if not self.check(T.NEWLINE, T.EOF, T.DEDENT):
            expr = self.parse_expr()
        return A.ReturnStmt(expr, line=tok.line)

    def parse_expr_or_assign_stmt(self):
        expr = self.parse_expr()

        if self.check(T.COMMA):
            # bare multi-target assignment: `a, b = pair` (reassigns existing names,
            # no `let`). A bare comma at statement level has no other valid meaning
            # here - list/map/call commas are all already bounded by their own
            # brackets/parens - so this is unambiguous.
            if not isinstance(expr, A.NameExpr):
                raise ParseError("invalid assignment target", expr.line)
            names = [expr.name]
            while self.match(T.COMMA):
                names.append(self.expect(T.NAME, "expected a variable name").value)
            self.expect(T.EQ, "expected '=' for a multi-target assignment")
            value = self.parse_expr()
            return A.UnpackAssignStmt(names, value, line=expr.line)

        if self.match(T.EQ):
            if not isinstance(expr, (A.NameExpr, A.Index, A.Get)):
                raise ParseError("invalid assignment target", expr.line)
            value = self.parse_expr()
            return A.AssignStmt(expr, value, line=expr.line)
        if self.peek().type in AUG_ASSIGN_OPS:
            op = AUG_ASSIGN_OPS[self.advance().type]
            if not isinstance(expr, (A.NameExpr, A.Index, A.Get)):
                raise ParseError("invalid assignment target", expr.line)
            rhs = self.parse_expr()
            combined = A.Binary(op, expr, rhs, line=expr.line)
            return A.AssignStmt(expr, combined, line=expr.line)
        return A.ExprStmt(expr, line=expr.line)

    def parse_class(self):
        tok = self.advance()
        name = self.expect(T.NAME, "expected a class name").value
        superclass_name = None
        if self.match(T.LPAREN):
            superclass_name = self.expect(T.NAME, "expected a superclass name").value
            self.expect(T.RPAREN, "expected ')' after superclass name")
        self.expect(T.COLON, "expected ':' to start the class body")
        self.expect(T.NEWLINE, "expected a newline after ':'")
        self.expect(T.INDENT, "expected an indented class body")
        methods = {}
        self.skip_newlines()
        while not self.check(T.DEDENT, T.EOF):
            mtok = self.expect(T.FN, "only method definitions (pull ...) are allowed directly inside a class body")
            mname = self.expect(T.NAME, "expected a method name").value
            params = self.parse_params()
            body = self.parse_block()
            methods[mname] = A.FnExpr(params, body, name=mname, line=mtok.line)
            self.skip_newlines()
        self.expect(T.DEDENT, "expected the class body to end (dedent)")
        return A.ClassDecl(name, superclass_name, methods, line=tok.line)

    def parse_try(self):
        tok = self.advance()
        body = self.parse_block()
        except_name = None
        except_body = None
        if self.check(T.EXCEPT):
            self.advance()
            if self.check(T.NAME):
                except_name = self.advance().value
            except_body = self.parse_block()
        finally_body = None
        if self.check(T.FINALLY):
            self.advance()
            finally_body = self.parse_block()
        if except_body is None and finally_body is None:
            raise ParseError("expected 'except' or 'finally' after 'try'", tok.line)
        return A.TryStmt(body, except_name, except_body, finally_body, line=tok.line)

    def parse_raise(self):
        tok = self.advance()
        expr = self.parse_expr()
        return A.RaiseStmt(expr, line=tok.line)

    def parse_import(self):
        tok = self.advance()
        path_tok = self.expect(T.STRING, "expected a quoted file path after 'import'")
        path = "".join(text for kind, text in path_tok.value if kind == "lit")
        self.expect(T.AS, "expected 'as' after the import path")
        alias = self.expect(T.NAME, "expected a name after 'as'").value
        return A.ImportStmt(path, alias, line=tok.line)

    # ---------- expressions (precedence climbing) ----------

    def parse_expr(self):
        expr = self.parse_or()
        if self.check(T.IF):
            self.advance()
            cond = self.parse_or()
            self.expect(T.ELSE, "expected 'else' to complete the conditional expression")
            else_expr = self.parse_expr()
            return A.Ternary(cond, expr, else_expr, line=expr.line)
        return expr

    def parse_or(self):
        left = self.parse_and()
        while self.check(T.OR):
            tok = self.advance()
            right = self.parse_and()
            left = A.Logical("or", left, right, line=tok.line)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.check(T.AND):
            tok = self.advance()
            right = self.parse_not()
            left = A.Logical("and", left, right, line=tok.line)
        return left

    def parse_not(self):
        if self.check(T.NOT):
            tok = self.advance()
            operand = self.parse_not()
            return A.Unary("not", operand, line=tok.line)
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_addition()
        while self.peek().type in COMPARISON_OPS:
            tok = self.advance()
            right = self.parse_addition()
            left = A.Binary(COMPARISON_OPS[tok.type], left, right, line=tok.line)
        return left

    def parse_addition(self):
        left = self.parse_term()
        while self.peek().type in ADD_OPS:
            tok = self.advance()
            right = self.parse_term()
            left = A.Binary(ADD_OPS[tok.type], left, right, line=tok.line)
        return left

    def parse_term(self):
        left = self.parse_power()
        while self.peek().type in MUL_OPS:
            tok = self.advance()
            right = self.parse_power()
            left = A.Binary(MUL_OPS[tok.type], left, right, line=tok.line)
        return left

    def parse_power(self):
        left = self.parse_unary()
        if self.check(T.STARSTAR):
            tok = self.advance()
            right = self.parse_power()  # right-associative
            return A.Binary("**", left, right, line=tok.line)
        return left

    def parse_unary(self):
        if self.check(T.MINUS):
            tok = self.advance()
            operand = self.parse_unary()
            return A.Unary("-", operand, line=tok.line)
        return self.parse_call()

    def parse_call(self):
        expr = self.parse_primary()
        while True:
            if self.check(T.LPAREN):
                tok = self.advance()
                args = []
                if not self.check(T.RPAREN):
                    args.append(self.parse_expr())
                    while self.match(T.COMMA):
                        args.append(self.parse_expr())
                self.expect(T.RPAREN, "expected ')' after arguments")
                expr = A.Call(expr, args, line=tok.line)
            elif self.check(T.LBRACKET):
                tok = self.advance()
                index = self.parse_expr()
                self.expect(T.RBRACKET, "expected ']' after index")
                expr = A.Index(expr, index, line=tok.line)
            elif self.check(T.DOT):
                tok = self.advance()
                name = self.expect(T.NAME, "expected a property or method name after '.'").value
                expr = A.Get(expr, name, line=tok.line)
            else:
                break
        return expr

    def parse_primary(self):
        tok = self.peek()

        if self.match(T.NUMBER):
            return A.NumberLit(tok.value, line=tok.line)
        if self.match(T.STRING):
            return A.StringLit(self._parse_string_parts(tok.value), line=tok.line)
        if self.match(T.TRUE):
            return A.BoolLit(True, line=tok.line)
        if self.match(T.FALSE):
            return A.BoolLit(False, line=tok.line)
        if self.match(T.NIL):
            return A.NilLit(line=tok.line)
        if self.match(T.NAME):
            return A.NameExpr(tok.value, line=tok.line)
        if self.match(T.SELF):
            return A.NameExpr("self", line=tok.line)
        if self.match(T.SUPER):
            return A.SuperExpr(line=tok.line)
        if self.match(T.LPAREN):
            expr = self.parse_expr()
            self.expect(T.RPAREN, "expected ')' to close the expression")
            return expr
        if self.check(T.LBRACKET):
            return self.parse_list_lit()
        if self.check(T.LBRACE):
            return self.parse_map_lit()
        if self.check(T.FN):
            return self.parse_fn_expr()

        raise ParseError(f"unexpected token {tok.type.name}", tok.line)

    def parse_list_lit(self):
        tok = self.advance()
        if self.check(T.RBRACKET):
            self.advance()
            return A.ListLit([], line=tok.line)

        first = self.parse_expr()
        if self.check(T.FOR):
            clauses = self._parse_comprehension_clauses()
            node = A.ListComp(first, clauses, line=tok.line)
            self.expect(T.RBRACKET, "expected ']' after list comprehension")
            return node

        elements = [first]
        while self.match(T.COMMA):
            if self.check(T.RBRACKET):
                break
            elements.append(self.parse_expr())
        self.expect(T.RBRACKET, "expected ']' after list")
        return A.ListLit(elements, line=tok.line)

    def parse_map_lit(self):
        tok = self.advance()
        if self.check(T.RBRACE):
            self.advance()
            return A.MapLit([], line=tok.line)

        first_key = self.parse_expr()
        self.expect(T.COLON, "expected ':' between map key and value")
        first_value = self.parse_expr()

        if self.check(T.FOR):
            clauses = self._parse_comprehension_clauses()
            node = A.MapComp(first_key, first_value, clauses, line=tok.line)
            self.expect(T.RBRACE, "expected '}' after map comprehension")
            return node

        pairs = [(first_key, first_value)]
        while self.match(T.COMMA):
            if self.check(T.RBRACE):
                break
            pairs.append(self._parse_map_pair())
        self.expect(T.RBRACE, "expected '}' after map")
        return A.MapLit(pairs, line=tok.line)

    def _parse_map_pair(self):
        key = self.parse_expr()
        self.expect(T.COLON, "expected ':' between map key and value")
        value = self.parse_expr()
        return (key, value)

    def _parse_comprehension_clauses(self):
        """Parses one or more `for NAME in expr (if expr)?` clauses, chained - e.g.
        `for x in a for y in b if x != y` - shared by list and map comprehensions."""
        clauses = []
        while self.check(T.FOR):
            tok = self.advance()
            var_name = self.expect(T.NAME, "expected a loop variable name").value
            self.expect(T.IN, "expected 'in' after comprehension loop variable")
            # parse_or, not parse_expr: avoid swallowing a trailing 'if' as a ternary
            iterable = self.parse_or()
            condition = None
            if self.check(T.IF):
                self.advance()
                condition = self.parse_or()
            clauses.append(A.CompClause(var_name, iterable, condition, line=tok.line))
        return clauses

    def parse_fn_expr(self):
        tok = self.advance()
        params = self.parse_params()
        body = self.parse_block()
        return A.FnExpr(params, body, line=tok.line)

    def _parse_string_parts(self, raw_parts):
        parsed = []
        for kind, text in raw_parts:
            if kind == "lit":
                parsed.append(("lit", text))
            else:
                parsed.append(("expr", parse_expression_source(text)))
        return parsed


def parse_expression_source(src: str):
    """Parse a standalone expression from source text (used for `{expr}` string interpolation)."""
    from quill.lexer import tokenize

    tokens = tokenize(src)
    p = Parser(tokens)
    expr = p.parse_expr()
    return expr


def parse(tokens: list[Token]) -> list:
    return Parser(tokens).parse_program()
