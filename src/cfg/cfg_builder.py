"""
cfg_builder.py – IR-Blöcke → Kontrollflussgraph

Analysiert Sprungbefehle in den IR-Blöcken und verdrahtet
die Kanten des CFG entsprechend.
"""
from __future__ import annotations
from ..ir.ir_nodes import IRBlock, IROpcode
from .cfg_graph import CFGGraph


class CFGBuilder:
    """
    Baut den CFG aus einer geordneten Liste von IRBlock-Objekten.

    Verwendung::

        builder = CFGBuilder()
        cfg = builder.build(ir_blocks)
    """

    def build(self, blocks: list[IRBlock]) -> CFGGraph:
        """
        Erstellt den CFG und verbindet Blöcke über Sprungkanten.

        :param blocks: Ausgabe des IRGenerators
        :return: Befüllter CFGGraph
        """
        cfg = CFGGraph()
        block_index: dict[str, int] = {b.block_id: i for i, b in enumerate(blocks)}

        for block in blocks:
            cfg.add_block(block)

        for i, block in enumerate(blocks):
            last = block.instructions[-1] if block.instructions else None
            if last is None:
                # Leerer Block: fällt zum nächsten durch
                if i + 1 < len(blocks):
                    cfg.add_edge(block.block_id, blocks[i + 1].block_id)
                continue

            if last.opcode == IROpcode.JUMP:
                target_label = last.operands[0]
                if target_label in block_index:
                    cfg.add_edge(block.block_id, target_label)

            elif last.opcode in (IROpcode.JUMP_IF, IROpcode.JUMP_UNLESS):
                # Zwei Ausgangskanten: genommen / nicht genommen
                target_label = last.operands[-1]
                if target_label in block_index:
                    cfg.add_edge(block.block_id, target_label)
                if i + 1 < len(blocks):
                    cfg.add_edge(block.block_id, blocks[i + 1].block_id)

            elif last.opcode == IROpcode.RETURN:
                # Kein Nachfolger
                pass

            else:
                # Sequenziell zum nächsten Block
                if i + 1 < len(blocks):
                    cfg.add_edge(block.block_id, blocks[i + 1].block_id)

        return cfg
