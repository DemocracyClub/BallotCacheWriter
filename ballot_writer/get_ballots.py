import os
from typing import List, Optional

import requests
from models import WCIVFBallot
from write_ballots import LocalFileBackend, S3WriterBackend

BUCKET_NAME = os.environ.get("BUCKET_NAME")

IGNORE = [
    "local.uttlesford.2023-05-04",
    "local.derby.2023-05-04",
    "local.slough.2023-05-04",
    "local.southampton.2023-05-04",
    "local.south-derbyshire.2017-05-11",
]


def get_results_since(
    since: Optional[str] = None, current: Optional[bool] = False
):
    if not since:
        since = "1832-06-07"
    params = {"modified_gt": since}
    if current:
        params["current"] = 2
    url = "https://whocanivotefor.co.uk/api/candidates_for_ballots/"
    req = requests.get(url, params=params)
    print(req.url)
    return req.json()


def get_latest_from_results(results: dict):
    return results.get("results", [])[-1]["last_updated"]


def get_backend(backend=None):
    backend = os.environ.get("BACKEND", "local")
    if backend == "s3":
        return S3WriterBackend()
    return LocalFileBackend()


def update_ballot_ids(backend, ballot_ids: List):
    url = "https://whocanivotefor.co.uk/api/candidates_for_ballots/"
    params = {"ballot_ids": ballot_ids}
    req = requests.get(url, params=params)
    results = req.json()
    for ii, ballot in enumerate(results):
        print(ballot["ballot_paper_id"])
        ballot_model = WCIVFBallot.parse_obj(ballot)
        backend.save_ballot(ballot_model)


def update_ballots(backend):
    since = backend.get_latest_write_date()
    results = get_results_since(since, current=backend.current_only)
    seen_ballots = set()
    for ii, ballot in enumerate(results):
        if ":" in ballot["ballot_paper_id"]:
            continue
        if ballot["ballot_paper_id"] in IGNORE:
            continue
        print(ballot["ballot_paper_id"])
        ballot_model = WCIVFBallot.parse_obj(ballot)
        backend.save_ballot(ballot_model)
        seen_ballots.add(ballot_model.ballot_paper_id)
    if results:
        backend.write_last_updated(ballot)
    return seen_ballots


if __name__ == "__main__":
    backend = get_backend()
    # update_ballot_ids(backend, ["local.east-devon.woodbury-lympstone.2023-05-04"])
    for i in range(2000):
        backend = get_backend()
        # backend.current_only = True
        update_ballots(backend)
