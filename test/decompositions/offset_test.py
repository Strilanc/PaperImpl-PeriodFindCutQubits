# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import unicode_literals

import itertools
import random

from projectq.cengines import DecompositionRuleSet

from dirty_period_finding.decompositions import offset_rules, multi_not_rules
from dirty_period_finding.decompositions.offset_rules import (
    do_predict_carry_signals,
    do_predict_overflow,
    estimate_cost_of_bitrange_offset,
)
from dirty_period_finding.extensions import (
    LimitedCapabilityEngine,
    AutoReplacerEx,
)
from dirty_period_finding.gates import OffsetGate
from .._test_util import fuzz_permutation_circuit, check_permutation_circuit


def _carry_signals(x, y):
    return ((x + y) ^ x ^ y) >> 1


def test_carry_signals():
    assert _carry_signals(0b001, 0b001) == 0b001
    assert _carry_signals(0b010, 0b010) == 0b010
    assert _carry_signals(0b001, 0b111) == 0b111
    assert _carry_signals(0b111, 0b001) == 0b111
    assert _carry_signals(0b101, 0b101) == 0b101
    assert _carry_signals(0b101, 0b011) == 0b111
    assert _carry_signals(0b101, 0b001) == 0b001
    assert _carry_signals(0b1000000, 0b1000000) == 0b1000000
    assert _carry_signals(0b1001000, 0b1000001) == 0b1000000


def test_estimate_cost_of_bitrange_offset():
    assert estimate_cost_of_bitrange_offset(0b11111111, 8) == 1
    assert estimate_cost_of_bitrange_offset(0b01111111, 8) == 2
    assert estimate_cost_of_bitrange_offset(0b11110111, 8) == 3
    assert estimate_cost_of_bitrange_offset(0b11110000, 8) == 1
    assert estimate_cost_of_bitrange_offset(0b01110000, 8) == 2
    assert estimate_cost_of_bitrange_offset(0b11110001, 8) == 2
    assert estimate_cost_of_bitrange_offset(0b10101001, 8) == 4


def test_do_predict_carry_signals_small():
    for n in [0, 1, 2, 3, 4]:
        for offset in range(1 << n):
            offset_bits = [bool((offset >> i) & 1) for i in range(n)]

            check_permutation_circuit(
                register_sizes=[n, n],
                permutation=lambda _, (q, t):
                    (q, t ^ _carry_signals(q, offset)),
                engine_list=[
                    AutoReplacerEx(DecompositionRuleSet(modules=[
                        offset_rules,
                        multi_not_rules,
                    ])),
                    LimitedCapabilityEngine(allow_toffoli=True),
                ],
                actions=lambda eng, regs: do_predict_carry_signals(
                    offset_bits=offset_bits,
                    query_reg=regs[0],
                    target_reg=regs[1]))


def test_do_predict_overflow_signal_small():
    for n, nc in itertools.product([1, 2, 3],
                                   [0, 1, 2]):
        for offset in range(1 << n):
            check_permutation_circuit(
                register_sizes=[n, 1, nc, n-1],
                permutation=lambda _, (q, t, c, d):
                    (q,
                     t ^ (0 if c + 1 != 1 << nc or q + offset < 1 << n else 1),
                     c,
                     d),
                engine_list=[
                    AutoReplacerEx(DecompositionRuleSet(modules=[
                        offset_rules,
                        multi_not_rules,
                    ])),
                    LimitedCapabilityEngine(
                        allow_nots_with_many_controls=True,
                    ),
                ],
                actions=lambda eng, regs: do_predict_overflow(
                    offset=offset,
                    query_reg=regs[0],
                    target_bit=regs[1],
                    controls=regs[2],
                    dirty_reg=regs[3]))


def test_check_offset_permutations_small():
    for n, nc in itertools.product([1, 2, 3],
                                   [0, 1]):
        for offset in range(1 << n):
            dirty = 1
            check_permutation_circuit(
                register_sizes=[n, dirty, nc],
                permutation=lambda _, (t, d, c):
                    (t + (offset if c + 1 == 1 << nc else 0), d, c),
                engine_list=[
                    AutoReplacerEx(DecompositionRuleSet(modules=[
                        offset_rules,
                        multi_not_rules,
                    ])),
                    LimitedCapabilityEngine(
                        allow_all=True,
                        ban_classes=[OffsetGate],
                    ),
                ],
                actions=lambda eng, regs:
                    OffsetGate(offset) & regs[2] | regs[0])


def test_fuzz_offset_permutations_large():
    for _ in range(10):
        n = random.randint(0, 50)
        nc = random.randint(0, 2)
        offset = random.randint(0, 1 << n)
        dirty = 1
        fuzz_permutation_circuit(
            register_sizes=[n, dirty, nc],
            permutation=lambda _, (t, d, c):
                (t + (offset if c + 1 == 1 << nc else 0), d, c),
            engine_list=[
                AutoReplacerEx(DecompositionRuleSet(modules=[
                    offset_rules,
                    multi_not_rules,
                ])),
                LimitedCapabilityEngine(
                    allow_all=True,
                    ban_classes=[OffsetGate],
                ),
            ],
            actions=lambda eng, regs:
                OffsetGate(offset) & regs[2] | regs[0])
