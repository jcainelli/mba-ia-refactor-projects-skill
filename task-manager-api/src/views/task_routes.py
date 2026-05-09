from flask import Blueprint, jsonify, request

from src.controllers import task_controller
from src.schemas.task_schema import TaskCreateSchema, TaskUpdateSchema
from src.views._helpers import load_or_400

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
def list_tasks():
    return jsonify(task_controller.list_tasks()), 200


@task_bp.route("/tasks/search", methods=["GET"])
def search_tasks():
    return (
        jsonify(
            task_controller.search_tasks(
                request.args.get("q"),
                request.args.get("status"),
                request.args.get("priority"),
                request.args.get("user_id"),
            )
        ),
        200,
    )


@task_bp.route("/tasks/stats", methods=["GET"])
def task_stats():
    return jsonify(task_controller.task_stats()), 200


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    return jsonify(task_controller.get_task(task_id)), 200


@task_bp.route("/tasks", methods=["POST"])
def create_task():
    payload = load_or_400(TaskCreateSchema(), request.get_json(silent=True))
    return jsonify(task_controller.create_task(payload)), 201


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    payload = load_or_400(TaskUpdateSchema(partial=True), request.get_json(silent=True))
    return jsonify(task_controller.update_task(task_id, payload)), 200


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task_controller.delete_task(task_id)
    return jsonify({"message": "Task deletada com sucesso"}), 200
