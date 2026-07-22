"""Data models for Xiaohongshu API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InteractInfo:
    """Interaction counts for a note."""
    liked_count: int = 0
    collected_count: int = 0
    comment_count: int = 0
    share_count: int = 0


@dataclass
class UserBrief:
    """Brief user info embedded in note cards."""
    user_id: str = ""
    nickname: str = ""
    avatar: str = ""


@dataclass
class NoteCard:
    """A note card from search results or feeds."""
    note_id: str = ""
    title: str = ""
    desc: str = ""
    type: str = ""  # "normal" or "video"
    xsec_token: str = ""
    user: Optional[UserBrief] = None
    interact_info: Optional[InteractInfo] = None
    tag_list: list[str] = field(default_factory=list)
    image_list: list[str] = field(default_factory=list)
    cover_url: str = ""
    time: int = 0
    ip_location: str = ""


@dataclass
class NoteDetail:
    """Full note detail from feed API."""
    note_id: str = ""
    title: str = ""
    desc: str = ""
    type: str = ""
    user: Optional[UserBrief] = None
    interact_info: Optional[InteractInfo] = None
    tag_list: list[str] = field(default_factory=list)
    image_list: list[str] = field(default_factory=list)
    time: int = 0
    ip_location: str = ""
    update_time: int = 0


@dataclass
class UserInfo:
    """Full user profile information."""
    user_id: str = ""
    nickname: str = ""
    avatar: str = ""
    red_id: str = ""
    desc: str = ""
    gender: int = 0
    follows: int = 0
    fans: int = 0
    interaction: int = 0
    ip_location: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class Comment:
    """A single comment."""
    comment_id: str = ""
    content: str = ""
    user_id: str = ""
    user_nickname: str = ""
    user_avatar: str = ""
    like_count: int = 0
    sub_comment_count: int = 0
    create_time: int = 0
    ip_location: str = ""


@dataclass
class SearchResult:
    """Search notes result with pagination."""
    items: list[NoteCard] = field(default_factory=list)
    has_more: bool = False
    cursor: str = ""


@dataclass
class UserNotesResult:
    """User posted notes result with pagination."""
    notes: list[NoteCard] = field(default_factory=list)
    has_more: bool = False
    cursor: str = ""


@dataclass
class CommentResult:
    """Comments result with pagination."""
    comments: list[Comment] = field(default_factory=list)
    has_more: bool = False
    cursor: str = ""


@dataclass
class HomefeedResult:
    """Homefeed/recommend result with pagination."""
    items: list[NoteCard] = field(default_factory=list)
    has_more: bool = False
    cursor_score: str = ""
