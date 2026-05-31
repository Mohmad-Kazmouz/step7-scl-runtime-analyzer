# Generated from /home/karimodora/Documents/GitHub/step7-scl-runtime-analyzer/grammar/SCL.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .SCLParser import SCLParser
else:
    from SCLParser import SCLParser

# This class defines a complete generic visitor for a parse tree produced by SCLParser.

class SCLVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by SCLParser#functionBlock.
    def visitFunctionBlock(self, ctx:SCLParser.FunctionBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#blockHeader.
    def visitBlockHeader(self, ctx:SCLParser.BlockHeaderContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#constantSection.
    def visitConstantSection(self, ctx:SCLParser.ConstantSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#constDecl.
    def visitConstDecl(self, ctx:SCLParser.ConstDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#varSection.
    def visitVarSection(self, ctx:SCLParser.VarSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#varSectionHeader.
    def visitVarSectionHeader(self, ctx:SCLParser.VarSectionHeaderContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#varDecl.
    def visitVarDecl(self, ctx:SCLParser.VarDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#identList.
    def visitIdentList(self, ctx:SCLParser.IdentListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#typeName.
    def visitTypeName(self, ctx:SCLParser.TypeNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#indexRange.
    def visitIndexRange(self, ctx:SCLParser.IndexRangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#statementList.
    def visitStatementList(self, ctx:SCLParser.StatementListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#statement.
    def visitStatement(self, ctx:SCLParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#assignment.
    def visitAssignment(self, ctx:SCLParser.AssignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#ifStatement.
    def visitIfStatement(self, ctx:SCLParser.IfStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#elsifBranch.
    def visitElsifBranch(self, ctx:SCLParser.ElsifBranchContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#elseBranch.
    def visitElseBranch(self, ctx:SCLParser.ElseBranchContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#forStatement.
    def visitForStatement(self, ctx:SCLParser.ForStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#whileStatement.
    def visitWhileStatement(self, ctx:SCLParser.WhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#repeatStatement.
    def visitRepeatStatement(self, ctx:SCLParser.RepeatStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#caseStatement.
    def visitCaseStatement(self, ctx:SCLParser.CaseStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#caseBranch.
    def visitCaseBranch(self, ctx:SCLParser.CaseBranchContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#caseValueList.
    def visitCaseValueList(self, ctx:SCLParser.CaseValueListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#caseValue.
    def visitCaseValue(self, ctx:SCLParser.CaseValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#elseCaseBranch.
    def visitElseCaseBranch(self, ctx:SCLParser.ElseCaseBranchContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#callStatement.
    def visitCallStatement(self, ctx:SCLParser.CallStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#parameterList.
    def visitParameterList(self, ctx:SCLParser.ParameterListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#parameter.
    def visitParameter(self, ctx:SCLParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#returnStatement.
    def visitReturnStatement(self, ctx:SCLParser.ReturnStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#exitStatement.
    def visitExitStatement(self, ctx:SCLParser.ExitStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#expressionList.
    def visitExpressionList(self, ctx:SCLParser.ExpressionListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#AndExpr.
    def visitAndExpr(self, ctx:SCLParser.AndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#IdentExpr.
    def visitIdentExpr(self, ctx:SCLParser.IdentExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#NegExpr.
    def visitNegExpr(self, ctx:SCLParser.NegExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#CompExpr.
    def visitCompExpr(self, ctx:SCLParser.CompExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#OrExpr.
    def visitOrExpr(self, ctx:SCLParser.OrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#IndexExpr.
    def visitIndexExpr(self, ctx:SCLParser.IndexExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#MulDivModExpr.
    def visitMulDivModExpr(self, ctx:SCLParser.MulDivModExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#MemberExpr.
    def visitMemberExpr(self, ctx:SCLParser.MemberExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#LiteralExpr.
    def visitLiteralExpr(self, ctx:SCLParser.LiteralExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#CallExpr.
    def visitCallExpr(self, ctx:SCLParser.CallExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#NotExpr.
    def visitNotExpr(self, ctx:SCLParser.NotExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#PosExpr.
    def visitPosExpr(self, ctx:SCLParser.PosExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#ParenExpr.
    def visitParenExpr(self, ctx:SCLParser.ParenExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#AddSubExpr.
    def visitAddSubExpr(self, ctx:SCLParser.AddSubExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SCLParser#literal.
    def visitLiteral(self, ctx:SCLParser.LiteralContext):
        return self.visitChildren(ctx)



del SCLParser