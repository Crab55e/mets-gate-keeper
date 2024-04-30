import ctypes
from datetime import datetime as dt
import sys
import re

ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 0x0007)
STRFTIME_ARG = "%Y-%m-%d %H:%M.%S"
PROGRAM_ARGS = sys.argv[1:]

class log:
    _initial_label = "Main"

    @staticmethod
    def _write(content: tuple, label=_initial_label, level="INFO"):
        level = level.upper()
        if not (level in ["INFO", "WARN", "ERROR", "DEBUG"]):
            raise ValueError(f"{level} is not a valid log level")
        if label == "" or label == None:
            raise ValueError(f"{label} is not a valid label")
        if not ("--debug" in PROGRAM_ARGS) and level == "DEBUG":
            return
        content = " ".join([str(item) for item in content])
        match level:
            case "INFO": log_color = "\033[092m"
            case "WARN": log_color = "\033[093m"
            case "ERROR": log_color = "\033[091m"
            case "DEBUG": log_color = "\033[094m"

        formatted_log = f"[{dt.now().strftime(STRFTIME_ARG)} / {level} - {label}] {content}"
        print(log_color+formatted_log+"\033[0m")
        if level != "DEBUG":
            with open("main.log", "a", encoding="utf-8") as log_file:
                log_file.write(formatted_log + "\n")

    def info(self, *content, label: str = _initial_label):
        self._write(content, label=label)

    def warn(self, *content, label: str = _initial_label):
        self._write(content, level="WARN", label=label)

    def error(self, *content, label: str = _initial_label):
        self._write(content, level="ERROR", label=label)

    def debug(self, *content, label: str = _initial_label):
        self._write(content, level="DEBUG", label=label)

logger = log()
logger.info("Loading...")

import flask as fl
import waitress

import json
import requests as req
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode

app = fl.Flask(__name__)
DISCORD_METS_SERVER_ID = 842320961033601044


class SimplyDiscordAPIWrapper:
    def __init__(
            self,
            token: str,
            api_version: int = 10
    ) -> None:
        self.token = token
        self.api_version = api_version

    def request(
            self,
            url: str,
            method: str = "GET",
            raise_for_status: bool = True,
            return_json: bool = True
    ) -> None | req.Response | dict[dict, list]:
        method = method.upper()
        url = f"https://discord.com/api/v{self.api_version}/" + url.removeprefix("/")
        if not (method in ["GET","POST","DELETE","PATCH","PUT"]):
            raise ValueError(f"invalid value of \"method\" argument: {method}")

        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }

        res = req.request(
            method=method,
            url=url,
            headers=headers
        )
        if raise_for_status: res.raise_for_status()

        return json.loads(res.text) if return_json and res.text != "" else res

    def get(
            self,
            url: str,
            raise_for_status: bool = True,
            return_json: bool = True
    ) -> None | req.Response | dict[dict, list]:
        return self.request(
            url=url,
            method="GET",
            raise_for_status=raise_for_status,
            return_json=return_json
        )
    def post(
            self,
            url: str,
            raise_for_status: bool = True,
            return_json: bool = True
    ) -> None | req.Response | dict[dict, list]:
        return self.request(
            url=url,
            method="POST",
            raise_for_status=raise_for_status,
            return_json=return_json
        )
    def DELETE(
            self,
            url: str,
            raise_for_status: bool = True,
            return_json: bool = True
    ) -> None | req.Response | dict[dict, list]:
        return self.request(
            url=url,
            method="DELETE",
            raise_for_status=raise_for_status,
            return_json=return_json
        )
    def PATCH(
            self,
            url: str,
            raise_for_status: bool = True,
            return_json: bool = True
    ) -> None | req.Response | dict[dict, list]:
        return self.request(
            url=url,
            method="PATCH",
            raise_for_status=raise_for_status,
            return_json=return_json
        )
    def PUT(
            self,
            url: str,
            raise_for_status: bool = True,
            return_json: bool = True
    ) -> None | req.Response | dict[dict, list]:
        return self.request(
            url=url,
            method="PUT",
            raise_for_status=raise_for_status,
            return_json=return_json
        )
    
    class urls:
        @staticmethod
        def make_image(url: str, size: int = 2048) -> str:
            return "https://cdn.discordapp.com/" + url.removeprefix("/") + f"?size={size}"

discord = SimplyDiscordAPIWrapper(
    os.environ.get("MiniMetToken")
)

USERS_DB_PATH = "C:/Users/Crab55e/Desktop/developing-codes/gate-keeper/users.json"
MEMBER_ROLE_ID = "1074249440132603975"

@app.before_request
def before_request():
    logger.info(f"{fl.request.method}: {fl.request.url}")

@app.route("/<string:token>")
def index(token: str):
    # NOTE: こめたんが新メンバーの参加を検知して、tokenを生成
    # users.jsonにtokenとidが紐づくように書き込んでくれる
    # TODO: 認証tokenおよびURLを再生成する機能をこめたんに追加
    LOG_LABEL = "Index"
    if token == "favicon.ico":
        response = fl.Response(
            response=f"favicon is unset",
            status=400
        )
        return response

    internal_discord_user_token = token
    if internal_discord_user_token == None:
        response = fl.Response(
            response=f"token IS REQUIRED",
            status=400
        )
        return response

    with open(USERS_DB_PATH, "r", encoding="utf-8") as f:
        users_db = json.loads(f.read())

    target_discord_member_id = users_db[internal_discord_user_token]
    target_discord_member = discord.get(
        url=f"/guilds/{DISCORD_METS_SERVER_ID}/members/{target_discord_member_id}"
    )
    member_display_name = target_discord_member["user"].get("global_name")
    member_display_name = target_discord_member["user"]["username"] if member_display_name == None else member_display_name
    logger.info(f"get member from token: {member_display_name}({target_discord_member['user']['id']})", label=LOG_LABEL)

    member_avatar_hash = target_discord_member["user"].get("avatar")
    if member_avatar_hash != None:
        member_avatar_url = discord.urls.make_image(f"avatars/{target_discord_member['user']['id']}/{target_discord_member['user']['avatar']}.png",size=64
    )
    else:
        member_avatar_url = discord.urls.make_image(f"embed/avatars/{(int(target_discord_member['user']['id']) >> 22) % 6}.png",size=64)

    member_is_already_authenticated = MEMBER_ROLE_ID in target_discord_member["roles"]
    if member_is_already_authenticated: logger.warn("Member is already authenticated")

    return fl.render_template(
        "index.html",
        color_theme="dark",
        member_display_name=member_display_name,
        member_avatar_url=member_avatar_url,
        member_is_already_authenticated=member_is_already_authenticated
    )

@app.route("/auth/", methods=["POST"])
def auth():
    LOG_LABEL = "Auth"
    if fl.request.content_type != "application/json":
        response = fl.Response(
            response=f"INVALID CONTENT-TYPE: {fl.request.content_type}",
            status=400
        )
        return response

    data: dict = fl.request.json
    if data == None:
        response = fl.Response(
            response=f"JSON PAYLOAD IS REQUIRED.",
            status=400
        )
        return response

    logger.info(f"Get post data: {data}", label=LOG_LABEL)
    discord_token = data.get("dsc_token")
    recaptcha_token = data.get("rcp_token")

    if discord_token == None:
        response = fl.Response(
            response=f"\"dsc_token\" PARAM IS REQUIRED: \"{fl.request.json}\"",
            status=400
        )
        return response
    if recaptcha_token == None:
        response = fl.Response(
            response=f"\"rcp_token\" PARAM IS REQUIRED: \"{fl.request.json}\"",
            status=400
        )
        return response

    recaptcha_secret = os.environ.get("GRecaptchaSecret")
    recaptcha_api_url = f"https://www.google.com/recaptcha/api/siteverify?secret={recaptcha_secret}&response={recaptcha_token}"

    recaptcha_verification = req.post(recaptcha_api_url)
    recaptcha_verification_json: dict = json.loads(recaptcha_verification.text)

    if recaptcha_verification.status_code != 200:
        response = fl.Response(
            response=f"FAILED TO SITE-VERIFY RECAPTCHA: \"{recaptcha_verification_json.get("error-codes")}\"",
            status=500
        )
        return response

    recaptcha_success: bool = recaptcha_verification_json.get("success")
    if not (recaptcha_success):
        response = fl.Response(
            response="false",
            content_type="text/plain",
            status=200
        )
        return response

    with open(USERS_DB_PATH, "r", encoding="utf-8") as f:
        users_db = json.loads(f.read())

    target_discord_member_id = users_db[discord_token]
    target_discord_member = discord.get(
        url=f"/guilds/{DISCORD_METS_SERVER_ID}/members/{target_discord_member_id}",
    )
    discord.PUT(url=f"/guilds/{DISCORD_METS_SERVER_ID}/members/{target_discord_member_id}/roles/{MEMBER_ROLE_ID}")

    member_display_name = target_discord_member["user"].get("global_name")
    member_display_name = target_discord_member["user"]["username"] if member_display_name == None else member_display_name
    logger.info(f"Successfully authenticated: {member_display_name}({target_discord_member['user']['id']})",label=LOG_LABEL)

    with open(USERS_DB_PATH, "w", encoding="utf-8") as f:
        del users_db[discord_token]
        f.write(json.dumps(users_db))

    success_response = fl.Response(
            response="true",
            content_type="text/plain",
            status=200
        )
    return success_response

@app.after_request
def after_request(res: fl.Response):
    logger.info(f"Responded: {res.status_code}")
    return res

if __name__ == "__main__":
    PORT = 51001
    logger.info(f"Serving on {PORT}")

    # app.run(port=PORT, debug=True)
    waitress.serve(app,port=PORT)
