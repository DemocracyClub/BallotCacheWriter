import abc
import os
from pathlib import Path

import boto3
from models import WCIVFBallot


class BaseWriterBackend(abc.ABC):
    current_only = False
    last_updated_file = None

    def get_latest_write_date(self):
        return "1832-06-07"

    def save_ballot(self, ballot: WCIVFBallot):
        path: Path = self.get_path(ballot)
        self.write(path, ballot)

    @abc.abstractmethod
    def write(self, path: str, ballot: WCIVFBallot):
        ...

    @abc.abstractmethod
    def write_last_updated(self, ballot_dict: dict):
        ...

    @abc.abstractmethod
    def get_path(self, ballot: WCIVFBallot):
        ...

    def _path_from_ballot(self, ballot: WCIVFBallot):
        parts = ballot.ballot_paper_id.split(".")
        return "/".join(
            (parts[-1], parts[0], parts[1], f"{ballot.ballot_paper_id}.json")
        )

    @property
    def last_updated_path(self):
        last_updated_file = self.last_updated_file
        if self.current_only:
            last_updated_file = self.last_updated_file.with_suffix(".current")
        return last_updated_file


class LocalFileBackend(BaseWriterBackend):
    base_path = Path(__file__).parent.parent / "ballot_data"
    last_updated_file = base_path / "last_updated"

    def get_latest_write_date(self):
        last_updated_file = self.last_updated_path

        if not last_updated_file.exists():
            return super().get_latest_write_date()
        return last_updated_file.read_text()

    def write_last_updated(self, ballot_dict: dict):
        self.last_updated_path.write_text(ballot_dict["last_updated"])

    def get_path(self, ballot: WCIVFBallot):
        self.base_path.mkdir(exist_ok=True, parents=True)
        return self.base_path / self._path_from_ballot(ballot)

    def write(self, path: str, ballot: WCIVFBallot):
        path = self.get_path(ballot)
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open("w") as file:
            file.write(ballot.json(indent=4))


class S3WriterBackend(BaseWriterBackend):
    base_path = "ballot_data"
    last_updated_file = f"{base_path}/last_updated"

    def __init__(self) -> None:
        self.s3 = boto3.resource(
            "s3", region_name=os.environ.get("AWS_REGION", "eu-west-2")
        )
        self.bucket = self.s3.Bucket(os.environ.get("S3_BUCKET"))

    def write(self, path: str, ballot: WCIVFBallot):
        self.bucket.put_object(
            Key=path, Body=ballot.json(indent=4), ContentType="application/json"
        )

    def get_path(self, ballot: WCIVFBallot):
        return f"{self.base_path}/{self._path_from_ballot(ballot)}"

    def write_last_updated(self, ballot_dict: dict):
        print(f"WRITING {self.last_updated_path=} with {ballot_dict['last_updated']=}")
        self.bucket.put_object(
            Key=self.last_updated_path,
            Body=ballot_dict["last_updated"],
            ContentType="text/html",
        )

    def get_latest_write_date(self):
        last_updated_file = self.last_updated_path()
        try:
            return (
                self.bucket.Object(last_updated_file).get()["Body"].read().decode()
            )
        except self.bucket.meta.client.exceptions.NoSuchKey:
            return super().get_latest_write_date()
