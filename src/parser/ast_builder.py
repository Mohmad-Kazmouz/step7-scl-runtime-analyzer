# ast_builder.py – ANTLR-Visitor → ASTNode-Baum
#
# Wandelt den von ANTLR erzeugten Parse-Tree in unsere eigenen
# ASTNode-Datenstrukturen um (Visitor-Pattern).
import re
from .ast_nodes import (
    ASTNode, FunctionBlockNode, VarSectionNode, VariableNode,
    StatementListNode, AssignmentNode, IfNode, ForNode, WhileNode,
    RepeatNode, CaseNode, CallNode, ReturnNode, ExitNode,
    BinaryOpNode, UnaryOpNode, LiteralNode, IdentifierNode,
    IndexNode, MemberNode,
)
from .generated.SCLVisitor import SCLVisitor


class ASTBuilder(SCLVisitor):
    """
    Traversiert den ANTLR-Parse-Tree und baut den ASTNode-Baum auf.
    Jede visit_*-Methode entspricht einer Grammatikregel in SCL.g4.
    """

    def visitFunctionBlock(self, ctx) -> ASTNode:
        """FUNCTION_BLOCK name ... END_FUNCTION_BLOCK"""
        name = ctx.IDENT().getText()
        var_sections = [self.visit(sec) for sec in ctx.varSection() if sec is not None]
        var_sections = [s for s in var_sections if s is not None]
        const_sections = [self.visit(sec) for sec in ctx.constantSection() if sec is not None]
        const_sections = [s for s in const_sections if s is not None]
        var_sections.extend(const_sections)
        body = self.visit(ctx.statementList()) if ctx.statementList() else None
        return FunctionBlockNode(
            line=ctx.start.line,
            col=ctx.start.column,
            name=name,
            var_sections=var_sections,
            body=body,
        )

    def visitConstantSection(self, ctx) -> ASTNode:
        """CONST ... END_CONST"""
        variables = []
        if ctx.constDecl():
            for decl in ctx.constDecl():
                v = self.visit(decl)
                if v is not None:
                    variables.append(v)
        return VarSectionNode(
            line=ctx.start.line,
            col=ctx.start.column,
            kind="VAR",
            variables=variables,
        )

    def visitConstDecl(self, ctx) -> ASTNode:
        """Name (COLON Typ)? := Initialwert;"""
        if not ctx.IDENT():
            return None
        name = ctx.IDENT().getText()
        type_name = self.visit(ctx.typeName()) if ctx.typeName() else ""
        initial_value = self.visit(ctx.expression()) if ctx.expression() else None
        return VariableNode(
            line=ctx.start.line,
            col=ctx.start.column,
            name=name,
            type_name=type_name,
            initial_value=initial_value,
        )

    def visitBlockHeader(self, ctx) -> None:
        """Ignoriere Header-Einträge wie TITLE, VERSION, etc."""
        return None

    def visitVarSection(self, ctx) -> ASTNode:
        """VAR / VAR_INPUT / VAR_OUTPUT / VAR_TEMP Abschnitt"""
        kind = ctx.varSectionHeader().getText().upper()
        # Fallback for VAR_CONSTANT to be treated as VAR
        if kind == "VAR_CONSTANT":
            kind = "VAR"
        variables = []
        if ctx.varDecl():
            for decl in ctx.varDecl():
                v = self.visit(decl)
                if v is not None:
                    variables.append(v)
        return VarSectionNode(
            line=ctx.start.line,
            col=ctx.start.column,
            kind=kind,
            variables=variables,
        )

    def visitVarDecl(self, ctx) -> ASTNode:
        """Name (AT Overlay)? : Typ := Initialwert;"""
        if not ctx.IDENT():
            return None
        name = ctx.IDENT(0).getText()
        type_name = self.visit(ctx.typeName()) if ctx.typeName() else ""
        initial_value = self.visit(ctx.expression()) if ctx.expression() else None
        return VariableNode(
            line=ctx.start.line,
            col=ctx.start.column,
            name=name,
            type_name=type_name,
            initial_value=initial_value,
        )

    def visitTypeName(self, ctx) -> str:
        """Typname"""
        if ctx.IDENT():
            return ctx.IDENT().getText()
        elif ctx.ARRAY():
            ranges = [self.visit(r) for r in ctx.indexRange() if r is not None]
            base_type = self.visit(ctx.typeName()) if ctx.typeName() else ""
            return f"ARRAY[{', '.join(ranges)}] OF {base_type}"
        elif ctx.STRUCT():
            return "STRUCT"
        return ""

    def visitIndexRange(self, ctx) -> str:
        """Index-Bereich (z. B. 0..3)"""
        left = ctx.expression(0).getText() if ctx.expression(0) else ""
        right = ctx.expression(1).getText() if ctx.expression(1) else ""
        return f"{left}..{right}"

    def visitStatementList(self, ctx) -> ASTNode:
        """Liste von Anweisungen"""
        statements = []
        for stmt_ctx in ctx.statement():
            stmt = self.visit(stmt_ctx)
            if stmt is not None:
                statements.append(stmt)
        return StatementListNode(
            line=ctx.start.line,
            col=ctx.start.column,
            statements=statements,
        )

    def visitStatement(self, ctx) -> ASTNode | None:
        """Einzelne Anweisung"""
        if ctx.assignment():
            return self.visit(ctx.assignment())
        elif ctx.ifStatement():
            return self.visit(ctx.ifStatement())
        elif ctx.forStatement():
            return self.visit(ctx.forStatement())
        elif ctx.whileStatement():
            return self.visit(ctx.whileStatement())
        elif ctx.repeatStatement():
            return self.visit(ctx.repeatStatement())
        elif ctx.caseStatement():
            return self.visit(ctx.caseStatement())
        elif ctx.callStatement():
            return self.visit(ctx.callStatement())
        elif ctx.returnStatement():
            return self.visit(ctx.returnStatement())
        elif ctx.exitStatement():
            return self.visit(ctx.exitStatement())
        return None  # Leeres Statement (Semikolon)

    def visitAssignment(self, ctx) -> ASTNode:
        """target := expression"""
        target = self.visit(ctx.expression(0))
        value = self.visit(ctx.expression(1))
        return AssignmentNode(
            line=ctx.start.line,
            col=ctx.start.column,
            target=target,
            value=value,
        )

    def visitIfStatement(self, ctx) -> ASTNode:
        """IF ... THEN ... ELSIF ... ELSE ... END_IF"""
        condition = self.visit(ctx.expression())
        then_body = self.visit(ctx.statementList())
        elsif_branches = []
        for branch in ctx.elsifBranch():
            elsif_branches.append(self.visit(branch))
        else_body = self.visit(ctx.elseBranch()) if ctx.elseBranch() else None
        return IfNode(
            line=ctx.start.line,
            col=ctx.start.column,
            condition=condition,
            then_body=then_body,
            elsif_branches=elsif_branches,
            else_body=else_body,
        )

    def visitElsifBranch(self, ctx) -> tuple[ASTNode, ASTNode]:
        """ELSIF ... THEN ..."""
        cond = self.visit(ctx.expression())
        body = self.visit(ctx.statementList())
        return (cond, body)

    def visitElseBranch(self, ctx) -> ASTNode:
        """ELSE ..."""
        return self.visit(ctx.statementList())

    def visitForStatement(self, ctx) -> ASTNode:
        """FOR ... TO ... BY ... DO ... END_FOR"""
        variable = ctx.IDENT().getText()
        start = self.visit(ctx.expression(0))
        end = self.visit(ctx.expression(1))
        step = self.visit(ctx.expression(2)) if len(ctx.expression()) > 2 else None
        body = self.visit(ctx.statementList())
        return ForNode(
            line=ctx.start.line,
            col=ctx.start.column,
            variable=variable,
            start=start,
            end=end,
            step=step,
            body=body,
        )

    def visitWhileStatement(self, ctx) -> ASTNode:
        """WHILE ... DO ... END_WHILE"""
        condition = self.visit(ctx.expression())
        body = self.visit(ctx.statementList())
        return WhileNode(
            line=ctx.start.line,
            col=ctx.start.column,
            condition=condition,
            body=body,
        )

    def visitRepeatStatement(self, ctx) -> ASTNode:
        """REPEAT ... UNTIL ... END_REPEAT"""
        body = self.visit(ctx.statementList())
        condition = self.visit(ctx.expression())
        return RepeatNode(
            line=ctx.start.line,
            col=ctx.start.column,
            body=body,
            condition=condition,
        )

    def visitCaseStatement(self, ctx) -> ASTNode:
        """CASE ... OF ... END_CASE"""
        expression = self.visit(ctx.expression())
        branches = []
        for branch in ctx.caseBranch():
            branches.append(self.visit(branch))
        else_body = self.visit(ctx.elseCaseBranch()) if ctx.elseCaseBranch() else None
        return CaseNode(
            line=ctx.start.line,
            col=ctx.start.column,
            expression=expression,
            branches=branches,
            else_body=else_body,
        )

    def visitCaseBranch(self, ctx) -> tuple[list[ASTNode], ASTNode]:
        """Wertebereich : Anweisungen"""
        values = self.visit(ctx.caseValueList())
        body = self.visit(ctx.statementList())
        return (values, body)

    def visitCaseValueList(self, ctx) -> list[ASTNode]:
        """Kommaseparierte Liste von Werten"""
        return [self.visit(val) for val in ctx.caseValue()]

    def visitCaseValue(self, ctx) -> ASTNode:
        """Einzelner Wert oder Bereich (a..b)"""
        if len(ctx.expression()) == 2:
            left = self.visit(ctx.expression(0))
            right = self.visit(ctx.expression(1))
            return BinaryOpNode(
                line=ctx.start.line,
                col=ctx.start.column,
                operator="..",
                left=left,
                right=right,
            )
        return self.visit(ctx.expression(0))

    def visitElseCaseBranch(self, ctx) -> ASTNode:
        """ELSE ... in CASE"""
        return self.visit(ctx.statementList())

    def visitCallStatement(self, ctx) -> ASTNode:
        """Aufruf"""
        name = ctx.IDENT().getText()
        arguments = self.visit(ctx.parameterList()) if ctx.parameterList() else []
        return CallNode(
            line=ctx.start.line,
            col=ctx.start.column,
            name=name,
            arguments=arguments,
        )

    def visitParameterList(self, ctx) -> list[tuple[str, ASTNode]]:
        """Parameterliste"""
        return [self.visit(p) for p in ctx.parameter()]

    def visitParameter(self, ctx) -> tuple[str, ASTNode]:
        """Einzelner Parameter"""
        ident = ctx.IDENT()
        if ident and (ctx.ASSIGN() or ctx.DARROW()):
            param_name = ident.getText()
        else:
            param_name = ""
        expr = self.visit(ctx.expression())
        return (param_name, expr)

    def visitReturnStatement(self, ctx) -> ASTNode:
        """RETURN"""
        return ReturnNode(
            line=ctx.start.line,
            col=ctx.start.column,
        )

    def visitExitStatement(self, ctx) -> ASTNode:
        """EXIT"""
        return ExitNode(
            line=ctx.start.line,
            col=ctx.start.column,
        )

    def visitExpressionList(self, ctx) -> list[ASTNode]:
        """Liste von Ausdrücken (z.B. bei Array-Indizierung)"""
        return [self.visit(expr) for expr in ctx.expression()]

    # ── Expressions ───────────────────────────────────────────────────────────

    def visitIndexExpr(self, ctx) -> ASTNode:
        array = self.visit(ctx.expression())
        indices = self.visit(ctx.expressionList())
        return IndexNode(
            line=ctx.start.line,
            col=ctx.start.column,
            array=array,
            indices=indices,
        )

    def visitMemberExpr(self, ctx) -> ASTNode:
        obj = self.visit(ctx.expression())
        member = ctx.IDENT().getText()
        return MemberNode(
            line=ctx.start.line,
            col=ctx.start.column,
            obj=obj,
            member=member,
        )

    def visitOrExpr(self, ctx) -> ASTNode:
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        op = "OR" if ctx.OR() else "XOR"
        return BinaryOpNode(
            line=ctx.start.line,
            col=ctx.start.column,
            operator=op,
            left=left,
            right=right,
        )

    def visitAndExpr(self, ctx) -> ASTNode:
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        return BinaryOpNode(
            line=ctx.start.line,
            col=ctx.start.column,
            operator="AND",
            left=left,
            right=right,
        )

    def visitCompExpr(self, ctx) -> ASTNode:
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        op = ctx.getChild(1).getText().upper()
        return BinaryOpNode(
            line=ctx.start.line,
            col=ctx.start.column,
            operator=op,
            left=left,
            right=right,
        )

    def visitAddSubExpr(self, ctx) -> ASTNode:
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        op = ctx.getChild(1).getText()
        return BinaryOpNode(
            line=ctx.start.line,
            col=ctx.start.column,
            operator=op,
            left=left,
            right=right,
        )

    def visitMulDivModExpr(self, ctx) -> ASTNode:
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        op = ctx.getChild(1).getText().upper()
        return BinaryOpNode(
            line=ctx.start.line,
            col=ctx.start.column,
            operator=op,
            left=left,
            right=right,
        )

    def visitNotExpr(self, ctx) -> ASTNode:
        operand = self.visit(ctx.expression())
        return UnaryOpNode(
            line=ctx.start.line,
            col=ctx.start.column,
            operator="NOT",
            operand=operand,
        )

    def visitNegExpr(self, ctx) -> ASTNode:
        operand = self.visit(ctx.expression())
        return UnaryOpNode(
            line=ctx.start.line,
            col=ctx.start.column,
            operator="-",
            operand=operand,
        )

    def visitPosExpr(self, ctx) -> ASTNode:
        operand = self.visit(ctx.expression())
        return UnaryOpNode(
            line=ctx.start.line,
            col=ctx.start.column,
            operator="+",
            operand=operand,
        )

    def visitParenExpr(self, ctx) -> ASTNode:
        return self.visit(ctx.expression())

    def visitLiteralExpr(self, ctx) -> ASTNode:
        return self.visit(ctx.literal())

    def visitIdentExpr(self, ctx) -> ASTNode:
        name = ctx.IDENT().getText()
        access_type = self._determine_access_type(name)
        return IdentifierNode(
            line=ctx.start.line,
            col=ctx.start.column,
            name=name,
            access_type=access_type,
        )

    def visitCallExpr(self, ctx) -> ASTNode:
        return self.visit(ctx.callStatement())

    def visitLiteral(self, ctx) -> ASTNode | None:
        text = ctx.getText()
        if ctx.INT_LIT():
            return LiteralNode(
                line=ctx.start.line,
                col=ctx.start.column,
                value=int(text),
                type_name="INT",
            )
        elif ctx.REAL_LIT():
            return LiteralNode(
                line=ctx.start.line,
                col=ctx.start.column,
                value=float(text),
                type_name="REAL",
            )
        elif ctx.BOOL_LIT():
            val = True if text.upper() == "TRUE" else False
            return LiteralNode(
                line=ctx.start.line,
                col=ctx.start.column,
                value=val,
                type_name="BOOL",
            )
        elif ctx.HEX_LIT():
            parts = text.split("#")
            base = int(parts[0])
            val_str = parts[1]
            val = int(val_str, base)
            return LiteralNode(
                line=ctx.start.line,
                col=ctx.start.column,
                value=val,
                type_name="INT",
            )
        elif ctx.TIME_LIT():
            return LiteralNode(
                line=ctx.start.line,
                col=ctx.start.column,
                value=text,
                type_name="TIME",
            )
        elif ctx.STRING_LIT():
            val = text[1:-1]
            return LiteralNode(
                line=ctx.start.line,
                col=ctx.start.column,
                value=val,
                type_name="STRING",
            )
        return None

    def _determine_access_type(self, name: str) -> str:
        name_upper = name.upper()
        # DB access: starts with DB followed by digit, or contains a dot and starts with DB
        if name_upper.startswith("DB") and ("." in name_upper or name_upper[2:].isdigit()):
            return "DB"
        if re.match(r"^M[BWD]?\d+(\.\d+)?$", name_upper):
            return "MERKER"
        if re.match(r"^[IE][BWD]?\d+(\.\d+)?$", name_upper):
            return "INPUT"
        if re.match(r"^[QA][BWD]?\d+(\.\d+)?$", name_upper):
            return "OUTPUT"
        return "LOCAL"

    def generic_visit(self, ctx) -> ASTNode:
        raise NotImplementedError(f"Kein Visitor für: {type(ctx).__name__}")
