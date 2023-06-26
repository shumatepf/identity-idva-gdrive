import logging
import re
import opensearchpy
import json

from . import settings

log = logging.getLogger(__name__)


def export(interactionId):
    es = opensearchpy.OpenSearch(
        hosts=[{"host": settings.ES_HOST, "port": settings.ES_PORT}], timeout=300
    )

    subflowquery = {
        "size": 500,
        "query": {
            "bool": {
                "should": [
                    {
                        "bool": {
                            "must": [
                                {
                                    "match_phrase": {
                                        "parentInteractionProps.parentInteractionId": interactionId
                                    }
                                },
                                {"exists": {"field": "interactionId"}},
                            ]
                        }
                    },
                    {
                        "bool": {
                            "must": [
                                {
                                    "match_phrase": {
                                        "properties.outcomeDescription.value": interactionId
                                    }
                                },
                                {
                                    "match_phrase": {
                                        "properties.outcomeType.value": "parent_id"
                                    }
                                },
                            ]
                        }
                    },
                ]
            }
        },
        "_source": ["interactionId"],
    }

    query = {
        "size": 1000,
        "query": {
            "bool": {"should": [{"match_phrase": {"interactionId": interactionId}}]}
        },
        "sort": {"tsEms": {"order": "asc"}},
    }

    # get subflow ids
    subs = es.search(body=json.dumps(subflowquery), index="_all")
    for sub in subs["hits"]["hits"]:
        clause = {"match_phrase": {"interactionId": sub["_source"]["interactionId"]}}
        query["query"]["bool"]["should"].append(clause)

    qstring = json.dumps(query)
    r = es.search(body=qstring, index="dev-eventsoutcome-*")

    output = []

    for hit in r["hits"]["hits"]:
        if hit["_source"].get("capabilityName") == "logOutcome":
            output.append(hit["_source"])

    return output


def codename(data: str):
    codenames = settings.CODE_NAMES

    for service, codename in codenames.items():
        data = re.sub(service, codename, data, flags=re.IGNORECASE)

    return data
