import datetime
from typing import Any

from pydantic import Field
from response_builder.v1.models.base import Ballot


class WCIVFBallot(Ballot):
    """
    Like a Ballot from the API response but slightly different.

    The logic to make them the same is in the aggregator_api stitcher
    class. This class is a nice way to see what the delta is between
    the two models!
    """

    def __init__(__pydantic_self__, **data: Any) -> None:
        # Take the post name form a nested object
        # Can change this in Pydantic V2
        # https://github.com/pydantic/pydantic/issues/717#issuecomment-1294904358
        data["post_name"] = data["post"]["post_name"]

        # A bit of a hack. Ideally we'd just use a shared base model
        # and add the different fields in sub-models.
        # However, this gets complex quickly, and it would be better
        # to just change the way WCIVF works!
        __pydantic_self__.__fields__.pop("ballot_locked", None)
        __pydantic_self__.__fields__.pop("ballot_title", None)
        __pydantic_self__.__fields__.pop("elected_role", None)
        # This is the URL for the ballot on the devs.DC API, so doesn't
        # make sense in isolation
        __pydantic_self__.__fields__.pop("ballot_url", None)
        super().__init__(**data)

    # use `alias=` to rename fields from the given JSON
    poll_open_date: datetime.date = Field(alias="election_date")
    candidates_verified: bool = Field(alias="ballot_locked")
    wcivf_url: str = Field(alias="absolute_url")


