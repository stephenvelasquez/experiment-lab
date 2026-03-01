#!/usr/bin/env python3
"""Experiment Lab — A/B test design and analysis with statistical rigor."""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


def _norm_cdf(x: float) -> float:
    """Approximate standard normal CDF using Abramowitz & Stegun."""
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x) / math.sqrt(2)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return 0.5 * (1.0 + sign * y)


def _norm_ppf(p: float) -> float:
    """Approximate inverse normal CDF (percent point function)."""
    if p <= 0:
        return -10
    if p >= 1:
        return 10
    if p < 0.5:
        return -_norm_ppf(1 - p)
    t = math.sqrt(-2.0 * math.log(1 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return t - (c0 + c1 * t + c2 * t * t) / (1 + d1 * t + d2 * t * t + d3 * t * t * t)


@dataclass
class ExperimentDesign:
    baseline_rate: float
    mde_relative: float
    significance_level: float
    power: float
    sample_size_per_variant: int = 0
    total_sample_size: int = 0

    def __post_init__(self):
        self.sample_size_per_variant = self._required_sample_size()
        self.total_sample_size = self.sample_size_per_variant * 2

    def _required_sample_size(self) -> int:
        p1 = self.baseline_rate
        p2 = p1 * (1 + self.mde_relative)
        p_bar = (p1 + p2) / 2
        z_alpha = _norm_ppf(1 - self.significance_level / 2)
        z_beta = _norm_ppf(self.power)
        n = ((z_alpha * math.sqrt(2 * p_bar * (1 - p_bar)) +
              z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (p2 - p1) ** 2
        return math.ceil(n)

    def days_to_significance(self, daily_traffic: int) -> float:
        return self.total_sample_size / daily_traffic


@dataclass
class ExperimentResult:
    control_users: int
    control_conversions: int
    treatment_users: int
    treatment_conversions: int
    significance_level: float = 0.05

    @property
    def control_rate(self) -> float:
        return self.control_conversions / self.control_users

    @property
    def treatment_rate(self) -> float:
        return self.treatment_conversions / self.treatment_users

    @property
    def relative_lift(self) -> float:
        return (self.treatment_rate - self.control_rate) / self.control_rate

    @property
    def absolute_lift(self) -> float:
        return self.treatment_rate - self.control_rate

    def _z_stat(self) -> float:
        p1 = self.control_rate
        p2 = self.treatment_rate
        n1 = self.control_users
        n2 = self.treatment_users
        p_pool = (self.control_conversions + self.treatment_conversions) / (n1 + n2)
        se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
        if se == 0:
            return 0
        return (p2 - p1) / se

    @property
    def p_value(self) -> float:
        z = abs(self._z_stat())
        return 2 * (1 - _norm_cdf(z))

    @property
    def is_significant(self) -> bool:
        return self.p_value < self.significance_level

    def confidence_interval(self) -> Tuple[float, float]:
        p1 = self.control_rate
        p2 = self.treatment_rate
        n1 = self.control_users
        n2 = self.treatment_users
        se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
        z = _norm_ppf(1 - self.significance_level / 2)
        diff = p2 - p1
        lower = diff - z * se
        upper = diff + z * se
        # Convert to relative lift CI
        if p1 > 0:
            return (lower / p1, upper / p1)
        return (0, 0)

    @property
    def recommendation(self) -> str:
        if self.is_significant and self.relative_lift > 0:
            return "Ship treatment"
        elif self.is_significant and self.relative_lift < 0:
            return "Revert — treatment is worse"
        else:
            return "No significant difference — gather more data or move on"


@dataclass
class Experiment:
    name: str
    design: Optional[ExperimentDesign] = None
    result: Optional[ExperimentResult] = None

    def design_experiment(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        significance_level: float = 0.05,
        power: float = 0.80,
    ) -> ExperimentDesign:
        self.design = ExperimentDesign(
            baseline_rate=baseline_rate,
            mde_relative=minimum_detectable_effect,
            significance_level=significance_level,
            power=power,
        )
        return self.design

    def analyze(
        self,
        control_users: int,
        control_conversions: int,
        treatment_users: int,
        treatment_conversions: int,
    ) -> ExperimentResult:
        alpha = self.design.significance_level if self.design else 0.05
        self.result = ExperimentResult(
            control_users=control_users,
            control_conversions=control_conversions,
            treatment_users=treatment_users,
            treatment_conversions=treatment_conversions,
            significance_level=alpha,
        )
        return self.result

    def print_design(self, daily_traffic: int = 0):
        if not self.design:
            print("No design yet. Call design_experiment() first.")
            return
        d = self.design
        target = d.baseline_rate * (1 + d.mde_relative)
        print(f"\n  Experiment: {self.name}")
        print(f"  {'=' * 48}")
        print(f"  Baseline:    {d.baseline_rate:.2%}")
        print(f"  MDE:         {d.mde_relative:.0%} relative ({target:.2%} absolute)")
        print(f"  Required:    {d.sample_size_per_variant:,} users per variant")
        print(f"  Total:       {d.total_sample_size:,} users")
        if daily_traffic:
            days = d.days_to_significance(daily_traffic)
            print(f"  At {daily_traffic:,}/day:  ~{days:.0f} days to reach significance")
        print()

    def print_results(self):
        if not self.result:
            print("No results yet. Call analyze() first.")
            return
        r = self.result
        ci = r.confidence_interval()
        print(f"\n  Results: {self.name}")
        print(f"  {'=' * 48}")
        print(f"  Control:     {r.control_rate:.2%} ({r.control_conversions:,} / {r.control_users:,})")
        print(f"  Treatment:   {r.treatment_rate:.2%} ({r.treatment_conversions:,} / {r.treatment_users:,})")
        print(f"  Lift:        {r.relative_lift:+.1%} relative")
        print(f"  p-value:     {r.p_value:.4f}")
        print(f"  Significant: {'YES' if r.is_significant else 'NO'} at \u03b1={r.significance_level}")
        print(f"  95% CI:      [{ci[0]:+.1%}, {ci[1]:+.1%}] relative lift")
        print(f"  {'─' * 48}")
        print(f"  RECOMMENDATION: {r.recommendation}")
        print()


def demo():
    exp = Experiment("Checkout Flow Redesign")

    exp.design_experiment(
        baseline_rate=0.032,
        minimum_detectable_effect=0.10,
        significance_level=0.05,
        power=0.80,
    )
    exp.print_design(daily_traffic=5000)

    exp.analyze(
        control_users=38_200,
        control_conversions=1_222,
        treatment_users=38_100,
        treatment_conversions=1_371,
    )
    exp.print_results()


if __name__ == "__main__":
    demo()
