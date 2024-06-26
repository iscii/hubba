from flask import Blueprint, jsonify, request
from domains.repositories.events_repository import EventsRepository
from domains.repositories.repo_exceptions import IdMissingException
from config import VERSION
from engine import engine
from sqlalchemy.orm import Session
from domains.repositories.repo_exceptions import *
from flask_cors import CORS
from routes.utils import ensure_UUID, require_json_params, require_query_params, ensure_authorized
from firebase_admin import auth
from uuid import UUID

events_blueprint = Blueprint('events_api', __name__, url_prefix="/")
CORS(events_blueprint)

@events_blueprint.route("/healthcheck")
def healthcheck():
    result = jsonify({
        "status": "success"
    })
    return result

@events_blueprint.route("/version")
def version():
    result = jsonify({
        "version": VERSION
    })
    return result

@events_blueprint.route("/", methods=["PUT"])
@ensure_authorized()
@require_json_params(["name", "host_org", "time_of"])
def add_event():
    context = request.get_json()

    name = context.get("name") if context.get("name") else None
    thumbnail = context.get("thumbnail") if context.get("thumbnail") else "https://via.placeholder.com/600x400"
    description = context.get("description") if context.get("description") else None
    url = context.get("url") if context.get("url") else None
    platform = context.get("platform") if context.get("platform") else None
    tags = list(map(str, context.get("tags"))) if context.get("tags") else []
    time_of = context.get("time_of") if context.get("time_of") else None
    host = context.get("host") if context.get("host") else None
    entry_fee = context.get("entry_fee") if context.get("entry_fee") else None
    host_id = context.get("host_org") if context.get("host_org") else None
    prizes = context.get("prizes") if context.get("prizes") else []

    with Session(engine) as session:
        events_repository = EventsRepository(session)
        try:
            event = events_repository.add_event(
                name=name,
                thumbnail=thumbnail,
                description=description,
                url=url,
                platform=platform,
                tags=tags,
                time_of=time_of,
                host=host,
                entry_fee=entry_fee,
                host_id=UUID(host_id),
                prizes=prizes
            )
            response = jsonify({
                "status": "success",
                "event": event.get_JSON()
            })
            return response
        except IdMissingException as e:
            response = jsonify({
                "status": "error",
                "message": str(e)
            })
            response.status_code = 404
            return response

@events_blueprint.route("/", methods=["GET"])
@require_query_params(["event_id"])
@ensure_UUID("event_id")
def get_event():
    event_id = request.args.get("event_id")
    if not event_id:
        response = jsonify({
            "status": "error",
            "message": "event_id is required"
        })
        response.status_code = 400
        return response

    with Session(engine) as session:
        events_repository = EventsRepository(session)
        try:
            event = events_repository.get_event(event_id=UUID(event_id))
            response = jsonify({
                "status": "success",
                "event": event.get_JSON()
            })
            return response
        except IdMissingException as e:
            response = jsonify({
                "status": "error",
                "message": str(e)
            })
            response.status_code = 404
            return response

@events_blueprint.route("/", methods=["DELETE"])
@ensure_authorized()
@require_query_params(["event_id"])
@ensure_UUID("event_id")
def delete_event():
    event_id = request.args.get("event_id")
    if not event_id:
        response = jsonify({
            "status": "error",
            "message": "event_id is required"
        })
        response.status_code = 400
        return response
    
    with Session(engine) as session:
        events_repository = EventsRepository(session)
        try:
            event_id = events_repository.delete_event(event_id=UUID(event_id))
            response = jsonify({
                "status": "success",
                "event_id": event_id
            })
            return response
        except IdMissingException as e:
            response = jsonify({
                "status": "error",
                "message": str(e)
            })
            response.status_code = 404
            return response

@events_blueprint.route("/", methods=["PATCH"])
@ensure_authorized()
@require_query_params(["event_id"])
@ensure_UUID("event_id")
def patch_event():
    context = request.get_json()
    event_id = request.args.get("event_id")

    name = context.get("name") if context.get("name") else None
    thumbnail = context.get("thumbnail") if context.get("thumbnail") else None
    description = context.get("description") if context.get("description") else None
    url = context.get("url") if context.get("url") else None
    time_of = context.get("time_of") if context.get("time_of") else None
    platform = context.get("platform") if context.get("platform") else None
    tags = list(map(str, context.get("tags"))) if context.get("tags") else []
    time_of = context.get("time_of") if context.get("time_of") else None
    host = context.get("host") if context.get("host") else None
    entry_fee = context.get("entry_fee") if context.get("entry_fee") else None
    prizes = context.get("prizes") if context.get("prizes") else []
    status = context.get("status") if context.get("status") is not None else None

    with Session(engine) as session:
        events_repository = EventsRepository(session)
        try:
            event = events_repository.update_event(
                event_id=UUID(event_id),
                name=name,
                thumbnail=thumbnail,
                description=description,
                url=url,
                platform=platform,
                tags=tags,
                time_of=time_of,
                host=host,
                entry_fee=entry_fee,
                prizes=prizes,
                status=status
            )
            response = jsonify({
                "status": "success",
                "event": event.get_JSON()
            })
            return response
        except IdMissingException as e:
            response = jsonify({
                "status": "error",
                "message": str(e)
            })
            response.status_code = 404
            return response

@events_blueprint.route("/add_user", methods=["PATCH"])
@ensure_authorized()
@require_query_params(["event_id"])
@ensure_UUID("event_id")
def add_user():
    event_id = request.args.get("event_id")
    user_id = auth.verify_id_token(request.headers.get("id_token"))["uid"]

    with Session(engine) as session:
        events_repository = EventsRepository(session)
        try:
            event = events_repository.add_user(
                event_id=event_id,
                user_id=user_id
            )
            response = jsonify({
                "status": "success",
                "event": event.get_JSON()
            })
            return response
        except IdMissingException as e:
            response = jsonify({
                "status": "error",
                "message": str(e)
            })
            response.status_code = 404
            return response

@events_blueprint.route("/delete_user", methods=["PATCH"])
@ensure_authorized()
@require_query_params(["event_id"])
@ensure_UUID("event_id")
def delete_user():
    event_id = request.args.get("event_id")
    user_id = auth.verify_id_token(request.headers.get("id_token"))["uid"]

    with Session(engine) as session:
        events_repository = EventsRepository(session)
        try:
            event = events_repository.delete_user(
                event_id=event_id,
                user_id=user_id
            )
            response = jsonify({
                "status": "success",
                "event": event.get_JSON()
            })
            return response
        except IdMissingException as e:
            response = jsonify({
                "status": "error",
                "message": str(e)
            })
            response.status_code = 404
            return response

@events_blueprint.route("/get_random_events", methods=["GET"])
def get_random_events():
    with Session(engine) as session:
        events_repository = EventsRepository(session)
        events = events_repository.get_random_events()
        response = jsonify({
            "status": "success",
            "events": [event.get_JSON() for event in events]
        })
        return response

@events_blueprint.route("/get_upcoming_events", methods=["GET"])
def get_upcoming_events():
    with Session(engine) as session:
        events_repository = EventsRepository(session)
        events = events_repository.get_upcoming_events()
        response = jsonify({
            "status": "success",
            "events": [event.get_JSON() for event in events]
        })
        return response

@events_blueprint.route("/get_current_events", methods=["GET"])
def get_current_events():
    with Session(engine) as session:
        events_repository = EventsRepository(session)
        events = events_repository.get_current_events()
        response = jsonify({
            "status": "success",
            "events": [event.get_JSON() for event in events]
        })
        return response

@events_blueprint.route("/get_user_events", methods=["GET"])
@ensure_authorized()
def get_user_events():
    user_id = auth.verify_id_token(request.headers.get("id_token"))["uid"]
    
    with Session(engine) as session:
        events_repository = EventsRepository(session)
        events = events_repository.get_user_events(user_id=user_id)
        response = jsonify({
            "status": "success",
            "events": [event.get_JSON() for event in events]
        })
        return response

@events_blueprint.route("/get_organization_events", methods=["GET"])
@require_query_params(["organization_id"])
@ensure_UUID("organization_id")
def get_organization_events():
    organization_id = request.args.get("organization_id")

    with Session(engine) as session:
        events_repository = EventsRepository(session)
        events = events_repository.get_organization_events(organization_id=UUID(organization_id))
        response = jsonify({
            "status": "success",
            "events": [event.get_JSON() for event in events]
        })
        return response

