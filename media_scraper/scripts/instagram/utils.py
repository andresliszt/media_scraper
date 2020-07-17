# -*- coding: utf-8 -*-
"""Utilidades de procesamiento."""

import datetime
import json
import textwrap


class InstagramPostsSerializer:
    """Clase para manejar la respuesta de la API de instagram."""

    def __init__(self, node: dict):
        for key, value in node.items():
            setattr(self, key, value)

    @property
    def serialize(self):
        """Simple serialización."""
        return self.__dict__

    @staticmethod
    def process_common_edge_node(node: dict):
        """Parser del node en json respuesta API instagram."""
        # TODO: INVESTIGAR EL JSON RESPUESTA DE API INSTAGRAM
        user_id = int(node["owner"]["id"])

        post_id = int(node["id"])

        try:
            text = node["edge_media_to_caption"]["edges"][0]["node"][
                "text"
            ]
        except IndexError:
            # Si no hay texto, habrá index error
            text = ""

        display_url = node["display_url"]

        likes = node["edge_media_preview_like"]["count"]

        # caption = node["accessibility_caption"]

        timestamp = datetime.date.fromtimestamp(
            node["taken_at_timestamp"]
        )

        is_video = node["is_video"]

        thumbnail_src = node["thumbnail_src"]

        processed_node = {
            "user_id": user_id,
            "post_id": post_id,
            "text": text,
            "likes": likes,
            "display_url": display_url,
            "thumbnail_src": thumbnail_src,
            "time": timestamp,
            "is_video": is_video,
        }

        return processed_node

    @staticmethod
    def get_code_from_id(post_id):
        parts = str(post_id).partition("_")
        id = int(parts[0])
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        code = ""

        while id > 0:
            remainder = int(id) % 64
            id = (id - remainder) // 64
            code = alphabet[remainder] + code

        return code


class UserTimeLinePost(InstagramPostsSerializer):
    """Serializador para posts de un usuario."""

    def __init__(self, node):

        processed_node = super().process_common_edge_node(node)

        super().__init__(processed_node)


class OpenUserPost(InstagramPostsSerializer):
    """Serializador para posts abiertos."""

    def __init__(self, node):

        processed_node = super().process_common_edge_node(node)

        processed_node["accessibility_caption"] = node[
            "accessibility_caption"
        ]

        super().__init__(processed_node)


class PostComment:
    """Serializador para comentarios de un post."""

    def __init__(self, comment_node):

        processed_comment_node = self.process_comment_node(comment_node)

        for key, value in processed_comment_node.items():

            setattr(self, key, value)

    @property
    def serialize(self):
        """Simple serialización."""
        return self.__dict__

    @staticmethod
    def process_comment_node(comment_node):

        post_id = comment_node["id"]

        text = comment_node["text"]

        timestamp = datetime.date.fromtimestamp(
            comment_node["created_at"]
        )

        reported_as_spam = comment_node["did_report_as_spam"]  # bool

        comment_user = comment_node["owner"]

        comment_user_id = comment_user["id"]

        comment_user_profile_pic = comment_user["profile_pic_url"]

        comment_username = comment_user["username"]

        likes = comment_node["edge_liked_by"]["count"]

        processed_comment_node = {
            "post_id": post_id,
            "text": text,
            "time": timestamp,
            "reported_as_spam": reported_as_spam,
            "comment_user": comment_user,
            "comment_user_id": comment_user_id,
            "comment_user_profile_pic": comment_user_profile_pic,
            "comment_username": comment_username,
            "likes": likes,
        }

        return processed_comment_node
