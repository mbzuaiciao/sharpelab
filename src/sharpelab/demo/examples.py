"""Fixed-seed examples for mock agent demonstrations."""

from pydantic import BaseModel, ConfigDict

from sharpelab.simulation.garch import simulate_garch
from sharpelab.simulation.iid_gaussian import simulate_iid_gaussian
from sharpelab.simulation.structural_break import simulate_structural_break


class DemoExample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    example_id: str
    title: str
    description: str
    returns: tuple[float, ...]
    provenance_text: str = ""


def _iid() -> DemoExample:
    simulation = simulate_iid_gaussian(
        sample_size=300,
        seed=4101,
        parameters={"mean": 0.006, "volatility": 0.05},
    )
    return DemoExample(
        example_id="iid",
        title="IID-like sample",
        description="Gaussian fixed-seed sample with no designed temporal dependence.",
        returns=tuple(float(value) for value in simulation.returns),
        provenance_text=(
            "We evaluated 3 strategies; other search details are incomplete."
        ),
    )


def _garch() -> DemoExample:
    simulation = simulate_garch(
        sample_size=300,
        seed=4202,
        parameters={
            "mean": 0.004,
            "omega": 0.00005,
            "alpha": 0.15,
            "beta": 0.80,
            "burn_in": 500,
        },
    )
    return DemoExample(
        example_id="garch",
        title="Volatility clustering",
        description=(
            "GARCH fixed-seed sample with weak linear autocorrelation and material "
            "squared-return dependence."
        ),
        returns=tuple(float(value) for value in simulation.returns),
    )


def _structural_break() -> DemoExample:
    simulation = simulate_structural_break(
        sample_size=300,
        seed=4303,
        parameters={
            "variant": "mean",
            "break_fraction": 0.5,
            "mean_1": -0.01,
            "mean_2": 0.03,
            "volatility_1": 0.04,
            "volatility_2": 0.04,
        },
    )
    return DemoExample(
        example_id="break",
        title="Structural break",
        description="Two-segment mean break with no stable full-sample Sharpe target.",
        returns=tuple(float(value) for value in simulation.returns),
    )


def _incomplete_provenance() -> DemoExample:
    base = _iid()
    return base.model_copy(
        update={
            "example_id": "provenance",
            "title": "Incomplete research provenance",
            "provenance_text": (
                "We tried many variations across a few markets, but the exact count "
                "and failed-trial log are unavailable."
            ),
        }
    )


DEMO_BUILDERS = {
    "iid": _iid,
    "garch": _garch,
    "break": _structural_break,
    "provenance": _incomplete_provenance,
}


def get_demo_example(example_id: str) -> DemoExample:
    try:
        return DEMO_BUILDERS[example_id]()
    except KeyError as error:
        raise KeyError(f"unknown demo example: {example_id}") from error
