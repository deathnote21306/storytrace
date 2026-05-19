from pydantic import BaseModel, model_validator
from typing import Optional, List


class AnalyzeRequest(BaseModel):
    url:   Optional[str] = None
    topic: Optional[str] = None

    @model_validator(mode='after')
    def require_url_or_topic(self):
        if not self.url and not self.topic:
            raise ValueError('at least one of url or topic must be provided')
        return self


class AnalyzeResponse(BaseModel):
    job_id:   str
    status:   str
    poll_url: str


class DNASchema(BaseModel):
    facts_kept:     List[str]
    facts_dropped:  List[str]
    tone:           str
    framing:        str
    political_lean: str


class TreeNode(BaseModel):
    id:          str
    outlet:      str
    country:     str
    url:         Optional[str]
    headline:    str
    drift_score: int
    parent_id:   Optional[str]
    dna:         Optional[DNASchema]
    children:    Optional[List['TreeNode']] = []


class StoryResponse(BaseModel):
    job_id:      str
    status:      str
    root:        Optional[dict]
    scored_list: Optional[list]
    tree:        Optional[dict]
