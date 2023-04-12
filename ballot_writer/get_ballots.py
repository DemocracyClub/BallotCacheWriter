import os
from typing import Optional

import requests
from pydantic import ValidationError

from write_ballots import LocalFileBackend, S3WriterBackend
from models import WCIVFBallot

BUCKET_NAME = os.environ.get("BUCKET_NAME")


def get_results_since(since: Optional[str] = None, current: Optional[bool] = False):
    if not since:
        since = "1832-06-07"
    params = {"modified_gt": since}
    if current:
        params["current"] = 1
    url = "https://whocanivotefor.co.uk/api/candidates_for_ballots/"
    req = requests.get(url, params=params)
    print(req.url)
    ret = req.json()
    return ret


def get_latest_from_results(results: dict):
    return results.get("results", [])[-1]["last_updated"]


def get_backend(backend=None):
    backend = os.environ.get("BACKEND", "local")
    if backend == "s3":
        return S3WriterBackend()
    return LocalFileBackend()


def update_ballots(backend):
    since = backend.get_latest_write_date()
    results = get_results_since(since, current=backend.current_only)
    seen_ballots = set()
    for ii, ballot in enumerate(results):
        if ":" in ballot["ballot_paper_id"]:
            continue
        try:
            ballot_model = WCIVFBallot.parse_obj(ballot)
        except ValidationError:
            continue
        backend.save_ballot(ballot_model)
        seen_ballots.add(ballot_model.ballot_paper_id)
    if results:
        backend.write_last_updated(ballot)
    return seen_ballots


if __name__ == "__main__":
    for i in range(200):
        backend = get_backend()
        backend.current_only = True
        update_ballots(backend)
