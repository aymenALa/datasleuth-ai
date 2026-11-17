"""Shared domain models for DataSleuth AI."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class DatasetContext:
    """Validated input dataset and metadata used by later pipeline stages."""

    dataset_id: str
    filename: str
    dataframe: pd.DataFrame
    row_count: int
    column_count: int
    column_names: list[str]
    warnings: list[str] = field(default_factory=list)
