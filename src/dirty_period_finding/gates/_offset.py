# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from projectq.ops import NotMergeable

from dirty_period_finding.extensions import BasicMathGateEx


class OffsetGate(BasicMathGateEx):
    def __init__(self, offset):
        BasicMathGateEx.__init__(self)
        self.offset = offset

    def do_operation(self, x):
        return x + self.offset,

    def get_inverse(self):
        return OffsetGate(-self.offset)

    def get_merged(self, other):
        if not isinstance(other, OffsetGate):
            raise NotMergeable()
        return OffsetGate(self.offset + other.offset)

    def __repr__(self):
        return 'OffsetGate({})'.format(self.offset)

    def __str__(self):
        return '{}{}'.format('+' if self.offset >= 0 else '', self.offset)

    def __eq__(self, other):
        return (isinstance(other, OffsetGate) and
                self.offset == other.offset)

    def __hash__(self):
        return hash((OffsetGate, self.offset))
