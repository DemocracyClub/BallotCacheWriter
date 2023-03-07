from get_ballots import update_ballots
from write_ballots import S3WriterBackend


def lambda_handler(event, context):
    backend = S3WriterBackend()
    seen_ballots = update_ballots(backend)
    if seen_ballots:
        print(f"Updated {seen_ballots}")
    else:
        print("No ballots updated")
