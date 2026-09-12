"""ContentPolishPipeline: the presentation half of the post-refactor split.

Mechanically identical to :class:`ztgkt.pipeline.ContentValidationPipeline`.
The difference is where it sits. The original ZTGKT was mandatory and stood in
front of every generation. After the split it became optional and applies only
on the path to external, operator-facing output. Content bound for a domain
consumer goes through :mod:`ztgkt.domain` instead.

Keeping both names is deliberate: the same regexes are correct policy in one
position and wrong policy in the other. See ``docs/LINEAGE.md``.
"""

from __future__ import annotations

from .pipeline import ContentValidationPipeline

__all__ = ["ContentPolishPipeline"]


class ContentPolishPipeline(ContentValidationPipeline):
    """Optional linguistic polish for external communication."""

    mandatory = False
