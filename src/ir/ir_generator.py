"""
ir_generator.py – AST → Intermediate Representation

Traversiert den AST (Visitor-Pattern) und erzeugt eine geordnete Liste
von IRBlock-Objekten. Weist jedem Befehl die Latenz aus dem CPU-Profil zu.
"""
from __future__ import annotations
from ..parser.ast_nodes import (
    FunctionBlockNode, StatementListNode, AssignmentNode,
    IfNode, ForNode, WhileNode, RepeatNode, CaseNode, CallNode,
    BinaryOpNode, UnaryOpNode, LiteralNode, IdentifierNode,
    ReturnNode, ExitNode, IndexNode, MemberNode,
)
from .ir_nodes import IRBlock, IRInstruction, IROpcode


class IRGenerator:
    """
    Erzeugt die IR-Blockstruktur aus einem FunctionBlockNode.

    Verwendung::

        gen = IRGenerator(cpu_profile, symbol_table)
        blocks = gen.generate(fb_ast)
    """

    def __init__(self, cpu_profile, symbol_table) -> None:
        self._profile = cpu_profile
        self._symbols = symbol_table
        self._blocks: list[IRBlock] = []
        self._current: IRBlock | None = None
        self._label_counter = 0

    # ── Öffentliche API ───────────────────────────────────────────────────────

    def generate(self, fb_node: FunctionBlockNode) -> list[IRBlock]:
        """
        Generiert alle IR-Blöcke für einen Funktionsbaustein.

        :param fb_node: AST-Wurzelknoten
        :return: Geordnete Liste von IRBlock-Objekten
        """
        self._new_block("entry")
        if fb_node.body:
            self._visit_statement_list(fb_node.body)
        self._emit(IROpcode.RETURN, source_line=fb_node.line)
        return self._blocks

    # ── Interne Hilfsmethoden ─────────────────────────────────────────────────

    def _new_block(self, label: str | None = None) -> IRBlock:
        label = label or f"L{self._label_counter}"
        self._label_counter += 1
        block = IRBlock(block_id=label)
        self._blocks.append(block)
        self._current = block
        return block

    def _emit(self, opcode: IROpcode, operands: list[str] | None = None,
              result: str | None = None, source_line: int = 0) -> IRInstruction:
        latency = self._profile.get_instruction_latency(opcode)
        instr = IRInstruction(
            opcode=opcode,
            operands=operands or [],
            result=result,
            source_line=source_line,
            latency_ns=latency,
        )
        if self._current is not None:
            self._current.instructions.append(instr)
        return instr

    def _fresh_temp(self) -> str:
        name = f"_t{self._label_counter}"
        self._label_counter += 1
        return name

    # ── Visitor-Methoden ──────────────────────────────────────────────────────

    def _visit_statement_list(self, node: StatementListNode) -> None:
        for stmt in node.statements:
            self._visit(stmt)

    def _visit(self, node) -> str | None:
        """Dispatcht auf die passende _visit_*-Methode."""
        name = f"_visit_{type(node).__name__}"
        handler = getattr(self, name, None)
        if handler:
            return handler(node)
        # Unbekannte Knoten werden als NOP behandelt
        return None

    def _visit_AssignmentNode(self, node: AssignmentNode) -> None:
        val = self._visit(node.value)
        target = self._visit(node.target)
        self._emit(IROpcode.STORE, operands=[val, target], source_line=node.line)

    def _visit_IdentifierNode(self, node: IdentifierNode) -> str:
        sym = self._symbols.resolve(node.name)
        storage_tag = sym.storage.name if sym else "UNKNOWN"
        tmp = self._fresh_temp()
        self._emit(IROpcode.LOAD, operands=[node.name, storage_tag],
                   result=tmp, source_line=node.line)
        return tmp

    def _visit_LiteralNode(self, node: LiteralNode) -> str:
        tmp = self._fresh_temp()
        self._emit(IROpcode.LOAD, operands=[str(node.value)],
                   result=tmp, source_line=node.line)
        return tmp
    def _visit_IndexNode(self, node: IndexNode) -> str:
        for idx in node.indices:
            self._visit(idx)
        return self._visit(node.array)

    def _visit_MemberNode(self, node: MemberNode) -> str:
        return self._visit(node.obj)

    def _visit_BinaryOpNode(self, node: BinaryOpNode) -> str:
        left = self._visit(node.left)
        right = self._visit(node.right)
        opcode = _OP_MAP.get(node.operator, IROpcode.ADD)
        tmp = self._fresh_temp()
        self._emit(opcode, operands=[left, right], result=tmp, source_line=node.line)
        return tmp

    def _visit_UnaryOpNode(self, node: UnaryOpNode) -> str:
        operand = self._visit(node.operand)
        opcode = IROpcode.NOT if node.operator.upper() == "NOT" else IROpcode.SUB
        tmp = self._fresh_temp()
        self._emit(opcode, operands=[operand], result=tmp, source_line=node.line)
        return tmp

    def _visit_IfNode(self, node: IfNode) -> None:
        cond = self._visit(node.condition)
        then_label = f"then_{self._label_counter}"
        else_label = f"else_{self._label_counter}"
        end_label  = f"endif_{self._label_counter}"
        self._label_counter += 1

        self._emit(IROpcode.JUMP_UNLESS, operands=[cond, else_label], source_line=node.line)
        self._new_block(then_label)
        self._visit_statement_list(node.then_body)
        self._emit(IROpcode.JUMP, operands=[end_label])

        # ELSIF-Zweige
        for cond_node, body in node.elsif_branches:
            self._new_block(else_label)
            else_label = f"else_{self._label_counter}"
            elsif_body_label = f"elsif_body_{self._label_counter}"
            self._label_counter += 1
            c = self._visit(cond_node)
            self._emit(IROpcode.JUMP_UNLESS, operands=[c, else_label])
            self._new_block(elsif_body_label)
            self._visit_statement_list(body)
            self._emit(IROpcode.JUMP, operands=[end_label])

        self._new_block(else_label)
        if node.else_body:
            self._visit_statement_list(node.else_body)

        self._new_block(end_label)

    def _visit_ForNode(self, node: ForNode) -> None:
        loop_label  = f"for_{self._label_counter}"
        body_label  = f"for_body_{self._label_counter}"
        end_label   = f"endfor_{self._label_counter}"
        self._label_counter += 1

        # Initialisierung
        start = self._visit(node.start)
        self._emit(IROpcode.STORE, operands=[start, node.variable], source_line=node.line)

        self._new_block(loop_label)
        end_val = self._visit(node.end)
        ctr     = self._fresh_temp()
        self._emit(IROpcode.LOAD, operands=[node.variable], result=ctr)
        self._emit(IROpcode.CMP_GT, operands=[ctr, end_val], result="_cond")
        self._emit(IROpcode.JUMP_IF, operands=["_cond", end_label])

        self._new_block(body_label)
        self._visit_statement_list(node.body)

        step = self._visit(node.step) if node.step else "1"
        self._emit(IROpcode.ADD, operands=[node.variable, step], result=node.variable)
        self._emit(IROpcode.JUMP, operands=[loop_label])
        self._new_block(end_label)

    def _visit_WhileNode(self, node: WhileNode) -> None:
        loop_label = f"while_{self._label_counter}"
        body_label = f"while_body_{self._label_counter}"
        end_label  = f"endwhile_{self._label_counter}"
        self._label_counter += 1
        self._new_block(loop_label)
        cond = self._visit(node.condition)
        self._emit(IROpcode.JUMP_UNLESS, operands=[cond, end_label], source_line=node.line)
        self._new_block(body_label)
        self._visit_statement_list(node.body)
        self._emit(IROpcode.JUMP, operands=[loop_label])
        self._new_block(end_label)

    def _visit_RepeatNode(self, node: RepeatNode) -> None:
        loop_label = f"repeat_{self._label_counter}"
        end_label  = f"endrepeat_{self._label_counter}"
        self._label_counter += 1
        self._new_block(loop_label)
        self._visit_statement_list(node.body)
        cond = self._visit(node.condition)
        self._emit(IROpcode.JUMP_UNLESS, operands=[cond, loop_label], source_line=node.line)
        self._new_block(end_label)

    def _visit_CallNode(self, node: CallNode) -> str | None:
        args = [self._visit(val) for _, val in node.arguments]
        tmp = self._fresh_temp()
        self._emit(IROpcode.CALL, operands=[node.name] + args,
                   result=tmp, source_line=node.line)
        return tmp

    def _visit_ReturnNode(self, node: ReturnNode) -> None:
        self._emit(IROpcode.RETURN, source_line=node.line)


# Abbildung SCL-Operator → IR-Opcode
_OP_MAP: dict[str, IROpcode] = {
    "+": IROpcode.ADD, "-": IROpcode.SUB,
    "*": IROpcode.MUL, "/": IROpcode.DIV, "MOD": IROpcode.MOD,
    "=": IROpcode.CMP_EQ, "<>": IROpcode.CMP_NE,
    "<":  IROpcode.CMP_LT, "<=": IROpcode.CMP_LE,
    ">":  IROpcode.CMP_GT, ">=": IROpcode.CMP_GE,
    "AND": IROpcode.AND, "OR": IROpcode.OR,
    "XOR": IROpcode.XOR, "NOT": IROpcode.NOT,
    "SHL": IROpcode.SHL, "SHR": IROpcode.SHR,
}
