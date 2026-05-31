"""
ir_generator.py – AST → Intermediate Representation

Traversiert den AST (Visitor-Pattern) und erzeugt eine geordnete Liste
von IRBlock-Objekten. Weist jedem Befehl die Latenz aus dem CPU-Profil zu.
"""

from __future__ import annotations

from ..parser.ast_nodes import (
    AssignmentNode,
    ASTNode,
    BinaryOpNode,
    CallNode,
    CaseNode,
    ExitNode,
    ForNode,
    FunctionBlockNode,
    IdentifierNode,
    IfNode,
    IndexNode,
    LiteralNode,
    MemberNode,
    RepeatNode,
    ReturnNode,
    StatementListNode,
    UnaryOpNode,
    WhileNode,
)
from ..semantic.symbol_table import StorageLocation
from .ir_nodes import IRBlock, IRInstruction, IROpcode

_BUILTIN_OPCODES: dict[str, IROpcode] = {
    "SQRT": IROpcode.SQRT,
    "ABS": IROpcode.ABS,
    "SIN": IROpcode.SIN,
    "COS": IROpcode.COS,
}

_ACCESS_TO_STORAGE: dict[str, StorageLocation] = {
    "DB": StorageLocation.SHARED_DB,
    "MERKER": StorageLocation.MERKER,
    "INPUT": StorageLocation.INPUT,
    "OUTPUT": StorageLocation.OUTPUT,
}

_REAL_TYPES = frozenset({"REAL", "LREAL"})
_DINT_TYPES = frozenset({"DINT", "UDINT", "DWORD", "TIME", "DATE", "DT", "TIME_OF_DAY"})
_BOOL_OPS = frozenset({"AND", "OR", "XOR", "NOT"})
_COMPARE_OPS = frozenset({"=", "<>", "<", "<=", ">", ">="})

_OP_MAP: dict[str, IROpcode] = {
    "+": IROpcode.ADD,
    "-": IROpcode.SUB,
    "*": IROpcode.MUL,
    "/": IROpcode.DIV,
    "MOD": IROpcode.MOD,
    "=": IROpcode.CMP_EQ,
    "<>": IROpcode.CMP_NE,
    "<": IROpcode.CMP_LT,
    "<=": IROpcode.CMP_LE,
    ">": IROpcode.CMP_GT,
    ">=": IROpcode.CMP_GE,
    "AND": IROpcode.AND,
    "OR": IROpcode.OR,
    "XOR": IROpcode.XOR,
    "NOT": IROpcode.NOT,
    "SHL": IROpcode.SHL,
    "SHR": IROpcode.SHR,
}


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
        self._loop_exit_stack: list[str] = []

    def generate(self, fb_node: FunctionBlockNode) -> list[IRBlock]:
        """Generiert alle IR-Blöcke für einen Funktionsbaustein."""
        self._blocks = []
        self._loop_exit_stack = []
        self._new_block("entry")
        if fb_node.body:
            self._visit_statement_list(fb_node.body)
        self._emit(IROpcode.RETURN, source_line=fb_node.line)
        return self._blocks

    def _new_block(self, label: str | None = None) -> IRBlock:
        label = label or f"L{self._label_counter}"
        self._label_counter += 1
        block = IRBlock(block_id=label)
        self._blocks.append(block)
        self._current = block
        return block

    def _latency_ns(
        self,
        opcode: IROpcode,
        storage: StorageLocation | None = None,
        *,
        is_write: bool = False,
        scl_type: str | None = None,
    ) -> float:
        base = self._profile.get_instruction_latency(opcode, scl_type)
        if storage is None:
            return base
        read_ns, write_ns = self._profile.get_access_times(storage)
        return base + (write_ns if is_write else read_ns)

    def _emit(
        self,
        opcode: IROpcode,
        operands: list[str] | None = None,
        result: str | None = None,
        source_line: int = 0,
        storage: StorageLocation | None = None,
        *,
        is_write: bool = False,
        scl_type: str | None = None,
    ) -> IRInstruction:
        storage_tag = storage.name if storage else ""
        ops = list(operands or [])
        if storage_tag and storage_tag not in ops:
            ops.append(storage_tag)

        instr = IRInstruction(
            opcode=opcode,
            operands=ops,
            result=result,
            source_line=source_line,
            latency_ns=self._latency_ns(
                opcode, storage, is_write=is_write, scl_type=scl_type
            ),
        )
        if self._current is not None:
            self._current.instructions.append(instr)
        return instr

    def _block_ends_with_transfer(self) -> bool:
        if not self._current or not self._current.instructions:
            return False
        last = self._current.instructions[-1].opcode
        return last in (IROpcode.JUMP, IROpcode.RETURN)

    def _emit_jump(self, target: str, source_line: int = 0) -> None:
        if not self._block_ends_with_transfer():
            self._emit(IROpcode.JUMP, operands=[target], source_line=source_line)

    def _expr_type(self, node: ASTNode | None) -> str:
        if node is None:
            return "INT"
        if isinstance(node, IdentifierNode):
            sym = self._symbols.resolve(node.name)
            return sym.type_name.upper() if sym and sym.type_name else "INT"
        if isinstance(node, LiteralNode):
            if isinstance(node.value, float):
                return "REAL"
            if isinstance(node.value, bool):
                return "BOOL"
            return "INT"
        if isinstance(node, BinaryOpNode):
            op = node.operator.upper()
            if op in _BOOL_OPS or op in _COMPARE_OPS:
                return "BOOL"
            left_t = self._expr_type(node.left)
            right_t = self._expr_type(node.right)
            if left_t in _REAL_TYPES or right_t in _REAL_TYPES:
                return "REAL"
            if left_t in _DINT_TYPES or right_t in _DINT_TYPES:
                return "DINT"
            return "INT"
        if isinstance(node, UnaryOpNode):
            if node.operator.upper() == "NOT":
                return "BOOL"
            return self._expr_type(node.operand)
        if isinstance(node, CallNode):
            name = node.name.upper()
            if name in ("SQRT", "SIN", "COS", "ABS"):
                return "REAL"
        return "INT"

    def _opcode_scl_type(self, opcode: IROpcode, node: ASTNode) -> str | None:
        if opcode in (
            IROpcode.ADD,
            IROpcode.SUB,
            IROpcode.MUL,
            IROpcode.DIV,
            IROpcode.MOD,
            IROpcode.CMP_EQ,
            IROpcode.CMP_NE,
            IROpcode.CMP_LT,
            IROpcode.CMP_LE,
            IROpcode.CMP_GT,
            IROpcode.CMP_GE,
        ):
            if isinstance(node, BinaryOpNode):
                left_t = self._expr_type(node.left)
                right_t = self._expr_type(node.right)
                if left_t in _REAL_TYPES or right_t in _REAL_TYPES:
                    return "REAL"
                if left_t in _DINT_TYPES or right_t in _DINT_TYPES:
                    return "DINT"
            elif isinstance(node, IdentifierNode):
                t = self._expr_type(node)
                return t if t in _REAL_TYPES | _DINT_TYPES else None
        return None

    def _storage_for_name(self, name: str, access_type: str = "LOCAL") -> StorageLocation:
        if access_type in _ACCESS_TO_STORAGE:
            return _ACCESS_TO_STORAGE[access_type]
        sym = self._symbols.resolve(name)
        if sym:
            return sym.storage
        return StorageLocation.INSTANCE_DB

    def _storage_for_expr(self, node: ASTNode | None) -> StorageLocation | None:
        if node is None:
            return None
        if isinstance(node, IdentifierNode):
            return self._storage_for_name(node.name, node.access_type)
        if isinstance(node, (IndexNode, MemberNode)):
            return self._storage_for_expr(
                node.array if isinstance(node, IndexNode) else node.obj
            )
        return None

    def _fresh_temp(self) -> str:
        name = f"_t{self._label_counter}"
        self._label_counter += 1
        return name

    def _visit_statement_list(self, node: StatementListNode) -> None:
        for stmt in node.statements:
            self._visit(stmt)

    def _visit(self, node) -> str | None:
        name = f"_visit_{type(node).__name__}"
        handler = getattr(self, name, None)
        if handler:
            return handler(node)
        return None

    def _visit_AssignmentNode(self, node: AssignmentNode) -> None:
        val = self._visit(node.value)
        storage = self._storage_for_expr(node.target)
        target_name = self._expr_name(node.target) or "?"
        self._emit(
            IROpcode.STORE,
            operands=[val, target_name],
            source_line=node.line,
            storage=storage,
            is_write=True,
        )

    @staticmethod
    def _expr_name(node: ASTNode | None) -> str | None:
        if isinstance(node, IdentifierNode):
            return node.name
        if isinstance(node, (IndexNode, MemberNode)):
            return IRGenerator._expr_name(
                node.array if isinstance(node, IndexNode) else node.obj
            )
        return None

    def _visit_IdentifierNode(self, node: IdentifierNode) -> str:
        storage = self._storage_for_name(node.name, node.access_type)
        tmp = self._fresh_temp()
        self._emit(
            IROpcode.LOAD,
            operands=[node.name],
            result=tmp,
            source_line=node.line,
            storage=storage,
        )
        return tmp

    def _visit_LiteralNode(self, node: LiteralNode) -> str:
        tmp = self._fresh_temp()
        self._emit(
            IROpcode.LOAD, operands=[str(node.value)], result=tmp, source_line=node.line
        )
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
        scl_type = self._opcode_scl_type(opcode, node)
        tmp = self._fresh_temp()
        self._emit(
            opcode,
            operands=[left, right],
            result=tmp,
            source_line=node.line,
            scl_type=scl_type,
        )
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
        end_label = f"endif_{self._label_counter}"
        self._label_counter += 1

        self._emit(
            IROpcode.JUMP_UNLESS, operands=[cond, else_label], source_line=node.line
        )
        self._new_block(then_label)
        self._visit_statement_list(node.then_body)
        self._emit_jump(end_label)

        for cond_node, body in node.elsif_branches:
            self._new_block(else_label)
            else_label = f"else_{self._label_counter}"
            elsif_body_label = f"elsif_body_{self._label_counter}"
            self._label_counter += 1
            c = self._visit(cond_node)
            self._emit(IROpcode.JUMP_UNLESS, operands=[c, else_label])
            self._new_block(elsif_body_label)
            self._visit_statement_list(body)
            self._emit_jump(end_label)

        self._new_block(else_label)
        if node.else_body:
            self._visit_statement_list(node.else_body)

        self._new_block(end_label)

    def _visit_ForNode(self, node: ForNode) -> None:
        loop_label = f"for_{self._label_counter}"
        body_label = f"for_body_{self._label_counter}"
        end_label = f"endfor_{self._label_counter}"
        self._label_counter += 1

        start = self._visit(node.start)
        var_storage = self._storage_for_name(node.variable)
        self._emit(
            IROpcode.STORE,
            operands=[start, node.variable],
            source_line=node.line,
            storage=var_storage,
            is_write=True,
        )

        self._new_block(loop_label)
        self._loop_exit_stack.append(end_label)
        end_val = self._visit(node.end)
        ctr = self._fresh_temp()
        var_type = self._expr_type(IdentifierNode(name=node.variable))
        self._emit(
            IROpcode.LOAD,
            operands=[node.variable],
            result=ctr,
            storage=var_storage,
        )
        self._emit(
            IROpcode.CMP_GT,
            operands=[ctr, end_val],
            result="_cond",
            scl_type=var_type if var_type in _REAL_TYPES | _DINT_TYPES else None,
        )
        self._emit(IROpcode.JUMP_IF, operands=["_cond", end_label])

        self._new_block(body_label)
        self._visit_statement_list(node.body)

        step = self._visit(node.step) if node.step else "1"
        self._emit(
            IROpcode.ADD,
            operands=[node.variable, step],
            result=node.variable,
            scl_type=var_type if var_type in _REAL_TYPES | _DINT_TYPES else None,
        )
        self._emit_jump(loop_label)
        self._loop_exit_stack.pop()
        self._new_block(end_label)

    def _visit_WhileNode(self, node: WhileNode) -> None:
        loop_label = f"while_{self._label_counter}"
        body_label = f"while_body_{self._label_counter}"
        end_label = f"endwhile_{self._label_counter}"
        self._label_counter += 1
        self._new_block(loop_label)
        self._loop_exit_stack.append(end_label)
        cond = self._visit(node.condition)
        self._emit(
            IROpcode.JUMP_UNLESS, operands=[cond, end_label], source_line=node.line
        )
        self._new_block(body_label)
        self._visit_statement_list(node.body)
        self._emit_jump(loop_label)
        self._loop_exit_stack.pop()
        self._new_block(end_label)

    def _visit_RepeatNode(self, node: RepeatNode) -> None:
        loop_label = f"repeat_{self._label_counter}"
        end_label = f"endrepeat_{self._label_counter}"
        self._label_counter += 1
        self._new_block(loop_label)
        self._loop_exit_stack.append(end_label)
        self._visit_statement_list(node.body)
        cond = self._visit(node.condition)
        self._emit(
            IROpcode.JUMP_UNLESS, operands=[cond, loop_label], source_line=node.line
        )
        self._loop_exit_stack.pop()
        self._new_block(end_label)

    def _visit_CaseNode(self, node: CaseNode) -> None:
        case_end = f"endcase_{self._label_counter}"
        self._label_counter += 1
        expression = self._visit(node.expression)

        for values, body in node.branches:
            branch_label = f"case_branch_{self._label_counter}"
            next_label = f"case_next_{self._label_counter}"
            self._label_counter += 1

            for val in values:
                val_temp = self._visit(val)
                cond_temp = self._fresh_temp()
                self._emit(
                    IROpcode.CMP_EQ,
                    operands=[expression, val_temp],
                    result=cond_temp,
                    source_line=node.line,
                )
                self._emit(IROpcode.JUMP_IF, operands=[cond_temp, branch_label])

            self._emit(IROpcode.JUMP, operands=[next_label])
            self._new_block(branch_label)
            self._visit_statement_list(body)
            self._emit_jump(case_end)
            self._new_block(next_label)

        if node.else_body:
            self._visit_statement_list(node.else_body)

        self._new_block(case_end)

    def _visit_ExitNode(self, node: ExitNode) -> None:
        if not self._loop_exit_stack:
            return
        self._emit(
            IROpcode.JUMP,
            operands=[self._loop_exit_stack[-1]],
            source_line=node.line,
        )

    def _visit_CallNode(self, node: CallNode) -> str | None:
        name_upper = node.name.upper()
        builtin = _BUILTIN_OPCODES.get(name_upper)

        if builtin is not None:
            for _, val in node.arguments:
                self._visit(val)
            tmp = self._fresh_temp()
            self._emit(
                builtin,
                operands=[name_upper],
                result=tmp,
                source_line=node.line,
            )
            return tmp

        args = [self._visit(val) for _, val in node.arguments]
        tmp = self._fresh_temp()
        self._emit(
            IROpcode.CALL,
            operands=[node.name] + args,
            result=tmp,
            source_line=node.line,
        )
        return tmp

    def _visit_ReturnNode(self, node: ReturnNode) -> None:
        self._emit(IROpcode.RETURN, source_line=node.line)
