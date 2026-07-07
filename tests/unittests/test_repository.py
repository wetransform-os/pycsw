# =================================================================
#
# Authors: Ricardo Garcia Silva <ricardo.garcia.silva@gmail.com>
#
# Copyright (c) 2017 Ricardo Garcia Silva
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================
"""Unit tests for pycsw.core.repository"""

import os
import shutil

import pytest
from sqlalchemy.sql import text

from pycsw.core import repository
from pycsw.core.config import StaticContext

pytestmark = pytest.mark.unit

CITE_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "functionaltests", "suites", "cite", "data", "cite.db",
)
DATASET_TYPE = "http://purl.org/dc/dcmitype/Dataset"


@pytest.fixture
def cite_repo_with_filter():
    context = StaticContext()
    return repository.Repository(
        "sqlite:///%s" % CITE_DB,
        context,
        table="records",
        repo_filter="type = '%s'" % DATASET_TYPE,
    )


@pytest.fixture
def cite_repo_with_filter_copy(tmp_path):
    """Repository backed by a disposable copy of cite.db.

    update()/delete() mutate data, so tests exercising them must not touch
    the shared cite.db fixture used by other test suites.
    """
    db_copy = tmp_path / "cite.db"
    shutil.copy(CITE_DB, db_copy)
    context = StaticContext()
    return repository.Repository(
        "sqlite:///%s" % db_copy,
        context,
        table="records",
        repo_filter="type = '%s'" % DATASET_TYPE,
    )


def test_query_with_constraint_respects_repo_filter(cite_repo_with_filter):
    """A POST constraint must not bypass the repo filter."""
    constraint = {"where": "anytext LIKE :pvalue0", "values": ["%"]}
    total, records = cite_repo_with_filter.query(constraint, maxrecords=20)

    assert int(total) > 0, "expected at least one Dataset record in cite.db"
    for record in records:
        assert record.type == DATASET_TYPE, (
            "repo filter not applied: record %s has type %s" % (record.identifier, record.type)
        )


def test_update_property_based_respects_repo_filter(cite_repo_with_filter_copy):
    """A property-based update with a constraint must not bypass the repo filter."""
    repo = cite_repo_with_filter_copy
    constraint = {"where": "anytext LIKE :pvalue0", "values": ["%"]}
    recprops = [{
        "rp": {"name": "apiso:Title", "xpath": "dc:title", "dbcol": "title"},
        "value": "updated-by-test",
    }]

    non_dataset_titles_before = {
        record.identifier: record.title
        for record in repo.session.query(repo.dataset).filter(repo.dataset.type != DATASET_TYPE).all()
    }
    assert non_dataset_titles_before, "expected non-Dataset records in cite.db to prove filter matters"

    dataset_matching_constraint = repo.session.query(repo.dataset).filter(
        text(constraint["where"])).params(repo._create_values(constraint["values"])
    ).filter(repo.dataset.type == DATASET_TYPE).count()
    assert dataset_matching_constraint > 0

    rows = repo.update(recprops=recprops, constraint=constraint)

    assert rows == dataset_matching_constraint
    updated_dataset_records = repo.session.query(repo.dataset).filter(
        repo.dataset.type == DATASET_TYPE, repo.dataset.title == "updated-by-test").count()
    assert updated_dataset_records == dataset_matching_constraint

    non_dataset_titles_after = {
        record.identifier: record.title
        for record in repo.session.query(repo.dataset).filter(repo.dataset.type != DATASET_TYPE).all()
    }
    assert non_dataset_titles_after == non_dataset_titles_before, (
        "repo filter bypassed: non-Dataset record(s) were updated"
    )


def test_delete_respects_repo_filter(cite_repo_with_filter_copy):
    """A delete with a constraint must not bypass the repo filter."""
    repo = cite_repo_with_filter_copy
    constraint = {"where": "anytext LIKE :pvalue0", "values": ["%"]}

    non_dataset_ids_before = {
        record.identifier
        for record in repo.session.query(repo.dataset).filter(repo.dataset.type != DATASET_TYPE).all()
    }
    assert non_dataset_ids_before, "expected non-Dataset records in cite.db to prove filter matters"

    dataset_matching_constraint = repo.session.query(repo.dataset).filter(
        text(constraint["where"])).params(repo._create_values(constraint["values"])
    ).filter(repo.dataset.type == DATASET_TYPE).count()
    assert dataset_matching_constraint > 0

    repo.delete(constraint)

    remaining_dataset_records = repo.session.query(repo.dataset).filter(
        repo.dataset.type == DATASET_TYPE).count()
    assert remaining_dataset_records == 0

    non_dataset_ids_after = {
        record.identifier
        for record in repo.session.query(repo.dataset).filter(repo.dataset.type != DATASET_TYPE).all()
    }
    assert non_dataset_ids_after == non_dataset_ids_before, (
        "repo filter bypassed: non-Dataset record(s) were deleted"
    )


@pytest.mark.parametrize("data, input_, predicate, distance, expected", [
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "bbox", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(2 2)", "bbox", 0, "false"),
    ("LINESTRING(0 0, 1 1)", "POINT(2 2)", "beyond", 1, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(2 2)", "beyond", 2, "false"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "beyond", "false", "false"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "contains", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(2 2)", "contains", 0, "false"),
    ("LINESTRING(0 0, 1 1)", "LINESTRING(1 0, 0 1)", "crosses", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "crosses", 0, "false"),
    ("POINT(1 1)", "POINT(1 1)", "equals", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "equals", 0, "false"),
    ("LINESTRING(0 0, 1 1)", "POINT(0 0)", "touches", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "touches", 0, "false"),
    ("POINT(0.5 0.5)", "LINESTRING(0 0, 1 1)", "within", 0, "true"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "within", 0, "false"),
    (None, "POINT(0.5 0.5)", "within", 0, "false"),
    ("POINT(0.5 0.5)", None, "within", 0, "false"),
    (None, None, "within", 0, "false"),
    ("LINESTRING(0 0, 1 1)", "POINT(0.5 0.5)", "dwithin", "false", "false"),
])
def test_query_spatial(data, input_, predicate, distance, expected):
    result = repository.query_spatial(
        bbox_data_wkt=data,
        bbox_input_wkt=input_,
        predicate=predicate,
        distance=distance
    )
    assert result == expected
