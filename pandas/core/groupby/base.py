"""
Provide basic components for groupby. These definitions
hold the allowlist of methods that are exposed on the
SeriesGroupBy and the DataFrameGroupBy objects.
"""
import collections
from typing import List
import warnings

from pandas._typing import final

from pandas.core.dtypes.common import (
    is_list_like,
    is_scalar,
)

from pandas.core.base import PandasObject

OutputKey = collections.namedtuple("OutputKey", ["label", "position"])


class ShallowMixin(PandasObject):
    _attributes: List[str] = []

    @final
    def _shallow_copy(self, obj, **kwargs):
        """
        return a new object with the replacement attributes
        """
        if isinstance(obj, self._constructor):
            obj = obj.obj
        for attr in self._attributes:
            if attr not in kwargs:
                # TODO: Remove once win_type deprecation is enforced
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", "win_type", FutureWarning)
                    kwargs[attr] = getattr(self, attr)
        return self._constructor(obj, **kwargs)


class GotItemMixin(PandasObject):
    """
    Provide the groupby facilities to the mixed object.
    """

    _attributes: List[str]

    @final
    def _gotitem(self, key, ndim, subset=None):
        """
        Sub-classes to define. Return a sliced object.

        Parameters
        ----------
        key : string / list of selections
        ndim : {1, 2}
            requested ndim of result
        subset : object, default None
            subset to act on
        """
        # create a new object to prevent aliasing
        if subset is None:
            # error: "GotItemMixin" has no attribute "obj"
            subset = self.obj  # type: ignore[attr-defined]

        # we need to make a shallow copy of ourselves
        # with the same groupby
        # TODO: Remove once win_type deprecation is enforced
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", "win_type", FutureWarning)
            kwargs = {attr: getattr(self, attr) for attr in self._attributes}

        # Try to select from a DataFrame, falling back to a Series
        try:
            # error: "GotItemMixin" has no attribute "_groupby"
            groupby = self._groupby[key]  # type: ignore[attr-defined]
        except IndexError:
            # error: "GotItemMixin" has no attribute "_groupby"
            groupby = self._groupby  # type: ignore[attr-defined]

        # error: Too many arguments for "GotItemMixin"
        # error: Unexpected keyword argument "groupby" for "GotItemMixin"
        # error: Unexpected keyword argument "parent" for "GotItemMixin"
        self = type(self)(
            subset, groupby=groupby, parent=self, **kwargs  # type: ignore[call-arg]
        )
        self._reset_cache()
        if subset.ndim == 2 and (is_scalar(key) and key in subset or is_list_like(key)):
            self._selection = key
        return self


# special case to prevent duplicate plots when catching exceptions when
# forwarding methods from NDFrames
plotting_methods = frozenset(["plot", "hist"])

common_apply_allowlist = (
    frozenset(
        [
            "quantile",
            "fillna",
            "mad",
            "take",
            "idxmax",
            "idxmin",
            "tshift",
            "skew",
            "corr",
            "cov",
            "diff",
        ]
    )
    | plotting_methods
)

series_apply_allowlist = (
    common_apply_allowlist
    | {"nlargest", "nsmallest", "is_monotonic_increasing", "is_monotonic_decreasing"}
) | frozenset(["dtype", "unique"])

dataframe_apply_allowlist = common_apply_allowlist | frozenset(["dtypes", "corrwith"])

# cythonized transformations or canned "agg+broadcast", which do not
# require postprocessing of the result by transform.
cythonized_kernels = frozenset(["cumprod", "cumsum", "shift", "cummin", "cummax"])

cython_cast_blocklist = frozenset(["rank", "count", "size", "idxmin", "idxmax"])

# List of aggregation/reduction functions.
# These map each group to a single numeric value
reduction_kernels = frozenset(
    [
        "all",
        "any",
        "corrwith",
        "count",
        "first",
        "idxmax",
        "idxmin",
        "last",
        "mad",
        "max",
        "mean",
        "median",
        "min",
        "ngroup",
        "nth",
        "nunique",
        "prod",
        # as long as `quantile`'s signature accepts only
        # a single quantile value, it's a reduction.
        # GH#27526 might change that.
        "quantile",
        "sem",
        "size",
        "skew",
        "std",
        "sum",
        "var",
    ]
)

# List of transformation functions.
# a transformation is a function that, for each group,
# produces a result that has the same shape as the group.
transformation_kernels = frozenset(
    [
        "backfill",
        "bfill",
        "cumcount",
        "cummax",
        "cummin",
        "cumprod",
        "cumsum",
        "diff",
        "ffill",
        "fillna",
        "pad",
        "pct_change",
        "rank",
        "shift",
        "tshift",
    ]
)

# these are all the public methods on Grouper which don't belong
# in either of the above lists
groupby_other_methods = frozenset(
    [
        "agg",
        "aggregate",
        "apply",
        "boxplot",
        # corr and cov return ngroups*ncolumns rows, so they
        # are neither a transformation nor a reduction
        "corr",
        "cov",
        "describe",
        "dtypes",
        "expanding",
        "ewm",
        "filter",
        "get_group",
        "groups",
        "head",
        "hist",
        "indices",
        "ndim",
        "ngroups",
        "ohlc",
        "pipe",
        "plot",
        "resample",
        "rolling",
        "tail",
        "take",
        "transform",
        "sample",
    ]
)
# Valid values  of `name` for `groupby.transform(name)`
# NOTE: do NOT edit this directly. New additions should be inserted
# into the appropriate list above.
transform_kernel_allowlist = reduction_kernels | transformation_kernels
