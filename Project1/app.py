from __future__ import annotations

import html
import re
import threading
from pathlib import Path
from typing import List, Mapping, MutableMapping, Union

from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
CHAT_LOG = BASE_DIR / "chat.txt"
CHAT_LOG.touch(exist_ok=True)

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

_lock = threading.Lock()
_url_pattern = re.compile(
    r"(http|https|ftp|ftps)\:\/\/[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,3}(\/\S*)?"
)


def _read_lines_unlocked() -> List[str]:
    with CHAT_LOG.open("r", encoding="utf-8") as fp:
        return [line.rstrip("\n") for line in fp]


def _get_payload() -> MutableMapping[str, Union[str, int]]:
    data: MutableMapping[str, Union[str, int]] = {}
    json_payload = request.get_json(silent=True)
    if isinstance(json_payload, Mapping):
        data.update(
            {key: value for key, value in json_payload.items() if isinstance(value, str)}
        )

    for key, value in request.form.items():
        data[key] = value

    return data


def _sanitize_message(message: str) -> str:
    escaped = html.escape(message, quote=True)

    def repl(match: re.Match[str]) -> str:
        url = match.group(0)
        return f'<a href="{url}" target="_blank">{url}</a>'

    return _url_pattern.sub(repl, escaped)


def _sanitize_nickname(nickname: str) -> str:
    return html.escape(nickname, quote=True)


@app.route("/", methods=["GET"])
def root() -> "flask.wrappers.Response":
    return send_from_directory(app.static_folder, "index.html")


@app.post("/process")
def process() -> "flask.wrappers.Response":
    data = _get_payload()
    function = str(data.get("function", "")).strip().lower()

    if function == "getstate":
        with _lock:
            lines = _read_lines_unlocked()
            return jsonify({"state": len(lines)})

    if function == "update":
        try:
            state = int(data.get("state", 0))
        except (TypeError, ValueError):
            state = 0

        with _lock:
            lines = _read_lines_unlocked()
            count = len(lines)
            if state >= count:
                return jsonify({"state": count, "text": False})

            delta = lines[state:]

        return jsonify({"state": count, "text": delta})

    if function == "send":
        nickname_raw = str(data.get("nickname", ""))
        message_raw = str(data.get("message", ""))

        message_body = " ".join(message_raw.replace("\r\n", "\n").splitlines()).strip()

        with _lock:
            lines = _read_lines_unlocked()
            if not message_body:
                return jsonify({"state": len(lines), "text": False})

            nickname = _sanitize_nickname(nickname_raw or "Anonymous")
            message = _sanitize_message(message_body)
            line = f"<span>{nickname}</span>{message}"

            with CHAT_LOG.open("a", encoding="utf-8") as fp:
                fp.write(line + "\n")

            new_state = len(lines) + 1

        return jsonify({"state": new_state, "text": False})

    return jsonify({"error": "Unknown function"}), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
