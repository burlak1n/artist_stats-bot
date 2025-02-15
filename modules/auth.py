import os
from dotenv import load_dotenv
import vk_api

from modules.logger import logger

load_dotenv()
LOGIN = os.environ.get("login")
PASSWORD = os.environ.get("password")

def two_factor():
    code = input('Code? ')
    return code, True

def get_access_token(login=LOGIN, password=PASSWORD):
    token = os.environ.get("vk_user_token")
    if token:
        return token
    vk = vk_api.VkApi(login, password, auth_handler=two_factor)

    try:
        vk.auth(token_only=True)
    except vk_api.AuthorizeError as error_msg:
        logger.error(error_msg)
        return

    logger.info("Access token получен успешно")
    return vk.token['access_token']

