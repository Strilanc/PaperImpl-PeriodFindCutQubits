# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import projectq.ops
from projectq.ops import BasicGate, Command
from projectq.types import BasicQubit


class BasicGateEx(BasicGate):
    def __and__(self, controls):
        if isinstance(controls, BasicQubit):
            controls = [controls]
        controls = list(controls)
        return GateWithCurriedControls(self, controls)

    def generate_command(self, qubits):
        qubits = self.make_tuple_of_qureg(qubits)
        if sum(len(reg) for reg in qubits) == 0:
            return None
        engines = [q.engine for reg in qubits for q in reg]
        eng = engines[0]
        assert all(e is eng for e in engines)
        return Command(eng, self, qubits)

    def __or__(self, qubits):
        if sum(len(reg) for reg in self.make_tuple_of_qureg(qubits)) == 0:
            return
        BasicGate.__or__(self, qubits)


class GateWithCurriedControls(BasicGateEx):
    def __init__(self, gate, controls):
        BasicGateEx.__init__(self)
        self._gate = gate
        self._controls = controls
        if isinstance(gate, GateWithCurriedControls):
            self._gate = gate._gate
            self._controls = self._controls + gate._controls

    def get_inverse(self):
        return GateWithCurriedControls(self._gate.get_inverse(),
                                       self._controls)

    def generate_command(self, qubits):
        cmd = self._gate.generate_command(qubits)
        cmd.add_control_qubits(self._controls)
        return cmd

    def __or__(self, quregs):
        from projectq.meta import Control
        quregs = BasicGate.make_tuple_of_qureg(quregs)
        if sum(len(reg) for reg in quregs) == 0:
            return
        eng = [q for reg in quregs for q in reg][0].engine
        with Control(eng, self._controls):
            self._gate | quregs

    def __str__(self):
        return '{} & {}'.format(self._gate, [q.id for q in self._controls])

    def __eq__(self, other):
        return (isinstance(other, GateWithCurriedControls) and
                self._gate == other._gate and
                self._controls == other._controls)


class HGate(projectq.ops.HGate, BasicGateEx):
    def __eq__(self, other):
        return isinstance(other, HGate)

    def __hash__(self):
        return hash(HGate)


class SelfInverseGateEx(projectq.ops.SelfInverseGate, BasicGateEx):
    pass

H = HGate()
