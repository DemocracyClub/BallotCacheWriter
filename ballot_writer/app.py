import os

from get_ballots import update_ballots
from write_ballots import S3WriterBackend


def lambda_handler(event, context):
    curent_only = os.environ.get("CURRENT_ONLY", None)
    backend = S3WriterBackend()
    if curent_only:
        backend.current_only = 1
    seen_ballots = update_ballots(backend)
    if seen_ballots:
        print(f"Updated {seen_ballots}")
    else:
        print("No ballots updated")
