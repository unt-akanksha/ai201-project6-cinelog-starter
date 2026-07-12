"""
services/watchlist_service.py — CineLog (feature/watchlist branch)

Business logic for the watchlist feature.
"""

from app import db
from models import Film, WatchlistEntry
from services.collection_service import FilmNotFoundError


class AlreadyInWatchlistError(Exception):
    """Raised when a user tries to add a film that's already on their watchlist."""
    pass


class NotInWatchlistError(Exception):
    """Raised when a user tries to remove a film that isn't on their watchlist."""
    pass


def add_to_watchlist(user_id, film_id, public=True):
    """
    Add a film to a user's watchlist.

    Args:
        user_id (str): UUID of the user.
        film_id (str): UUID of the film.
        public (bool, optional): Visibility of this entry. Defaults to True.
            See pr-response.md Comment 4 for the reasoning behind this default.

    Returns:
        WatchlistEntry: The newly created entry.

    Raises:
        FilmNotFoundError: If film_id does not exist.
        AlreadyInWatchlistError: If the film is already on the user's watchlist.
    """
    film = db.session.get(Film, film_id)
    if film is None:
        raise FilmNotFoundError(f"No film found with id '{film_id}'")

    existing = WatchlistEntry.query.filter_by(
        user_id=user_id, film_id=film_id
    ).first()
    if existing:
        raise AlreadyInWatchlistError(
            f"Film '{film_id}' is already on this user's watchlist"
        )

    entry = WatchlistEntry(user_id=user_id, film_id=film_id, public=public)
    db.session.add(entry)
    db.session.commit()
    return entry


def remove_from_watchlist(user_id, film_id):
    """
    Remove a film from a user's watchlist.

    Args:
        user_id (str): UUID of the user.
        film_id (str): UUID of the film.

    Raises:
        NotInWatchlistError: If the film is not currently on the user's watchlist.
    """
    entry = WatchlistEntry.query.filter_by(
        user_id=user_id, film_id=film_id
    ).first()
    if entry is None:
        raise NotInWatchlistError(
            f"Film '{film_id}' is not on this user's watchlist"
        )

    db.session.delete(entry)
    db.session.commit()


def get_watchlist(user_id):
    """
    Return all films on a user's watchlist.

    Sorted alphabetically by title (see pr-response.md Comment 5 for reasoning).

    Args:
        user_id (str): UUID of the user.

    Returns:
        list[dict]: List of film dicts with watchlist metadata attached.
    """
    entries = (
        WatchlistEntry.query
        .filter_by(user_id=user_id)
        .join(Film)
        .order_by(Film.title.asc())
        .all()
    )

    result = []
    for entry in entries:
        film_dict = entry.film.to_dict()
        film_dict["date_added"] = entry.date_added.isoformat()
        film_dict["public"] = entry.public
        result.append(film_dict)

    return result