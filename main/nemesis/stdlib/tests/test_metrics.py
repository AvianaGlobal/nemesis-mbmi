from __future__ import absolute_import

import unittest

from ..controls import FactorControl
from ..metrics import ValueMetric, EntropyMetric, RatioMetric, DistributionMetric
from ...r.ast import Constant, Name, Call, Raw


class TestMetrics(unittest.TestCase):

    def test_value_metric(self):
        control = FactorControl(name='bar')
        metric = ValueMetric(name='has_foo',
                             expression='foo > 0',
                             control_for=[control])
        ast = Call(Name('def_metric'),
                   (Name('has_foo'), Raw('foo > 0')),
                   (Name('control_for'), Constant('bar')))
        self.assertEqual(metric.ast(), ast)


def test_entropy_metric(self):
    control = FactorControl(name='bar')
    metric = EntropyMetric(name='has_foo',
                           expression='foo > 0',
                           control_for=[control])
    ast = Call(Name('def_metric'),
               (Name('has_foo'), Raw('foo > 0')),
               (Name('control_for'), Constant('bar')))
    self.assertEqual(metric.ast(), ast)


def test_ratio_metric(self):
    metric = RatioMetric(name='foo_to_bar',
                         numerator='foo', denominator='bar')
    ast = Call(Name('def_metric'),
               (Name('foo_to_bar'),
                Call(Name('ratio'), Raw('foo'), Raw('bar'))))
    self.assertEqual(metric.ast(), ast)

    metric.log_transform = True
    ast = Call(Name('def_metric'),
               (Name('foo_to_bar'),
                Call(Name('safe_log1p'),
                     Call(Name('ratio'), Raw('foo'), Raw('bar')))))
    self.assertEqual(metric.ast(), ast)

    metric.trait_set(
        log_transform=False,
        cap_below=True, cap_below_at=0.0,
        cap_above=True, cap_above_at=1.0,
        replace_na=True, replace_na_with=0.0)
    ast = Call(Name('def_metric'),
               (Name('foo_to_bar'),
                Call(Name('ratio'), Raw('foo'), Raw('bar'),
                     (Name('min'), Constant(0.0)),
                     (Name('max'), Constant(1.0)),
                     (Name('na_to'), Constant(0.0)))))
    self.assertEqual(metric.ast(), ast)


def test_distribution_metric(self):
    metric = DistributionMetric(name='foo_chi', expression='foo',
                                kind='chi_square')
    ast = Call(Name('def_group_metric'),
               Constant('foo_chi'), Raw('foo'), Name('chisq_test'))
    self.assertEqual(metric.ast(), ast)

    metric.trait_set(kind='custom', custom_function='foo_stat')
    ast = Call(Name('def_group_metric'),
               Constant('foo_chi'), Raw('foo'), Name('foo_stat'))
    self.assertEqual(metric.ast(), ast)


if __name__ == '__main__':
    unittest.main()
