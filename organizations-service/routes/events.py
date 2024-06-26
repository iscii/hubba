from flask import Blueprint, jsonify, request
from domains.repositories.events_repository import EventsRepository
from domains.repositories.repo_exceptions import IdMissingException
from config import VERSION
from engine import engine
from sqlalchemy.orm import Session
from domains.repositories.repo_exceptions import *
from flask_cors import CORS
from routes.utils import ensure_authorized, ensure_UUID, require_json_params, require_query_params 

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
@require_json_params(["title", "description", "owner"])
@ensure_UUID("owner")
def add_event():
    context = request.get_json()

    title = str(context.get("title")) if context.get("title") else None
    thumbnail = str(context.get("thumbnail")) if context.get("thumbnail") else None
    description = str(context.get("description")) if context.get("description") else None
    url = str(context.get("url")) if context.get("url") else None
    platform = str(context.get("platform")) if context.get("platform") else None
    tags = list(map(str, context.get("tags"))) if context.get("tags") else []
    time_of_event = context.get("time_of_event") if context.get("time_of_event") else None
    host = str(context.get("host")) if context.get("host") else None
    entry_fee = str(context.get("entry_fee")) if context.get("entry_fee") else None
    owner = context.get("owner")

    with Session(engine) as session:
        events_repository = EventsRepository(session)
        try:
            event = events_repository.add_event(
                title=title,
                thumbnail=thumbnail,
                description=description,
                url=url,
                platform=platform,
                tags=tags,
                time_of_event=time_of_event,
                host=host,
                entry_fee=entry_fee,
                owner=owner
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
            event = events_repository.get_event(event_id=event_id)
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
            event_id = events_repository.delete_event(event_id=event_id)
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
