# -*- coding: utf-8 -*-
"""Utilidades de procesamiento."""
from datetime import datetime


class TwitterPostSerializer:
    """Serializador para html de los posts de twitter."""

    def __init__(self, tweet, profile):
        tweet_info = self.parse_post(tweet, profile)
        for key, value in tweet_info.items():
            setattr(self, key, value)

    def parse_post(self, tweet, profile):

        text = tweet.find(".tweet-text")[0].full_text

        tweet_id = tweet.attrs["data-item-id"]

        tweet_url = profile.attrs["data-permalink-path"]

        username = profile.attrs["data-screen-name"]

        user_id = profile.attrs["data-user-id"]

        is_pinned = bool(tweet.find("div.pinned"))

        time = datetime.fromtimestamp(
            int(tweet.find("._timestamp")[0].attrs["data-time-ms"])
            / 1000.0
        )

        interactions = [
            x.text for x in tweet.find(".ProfileTweet-actionCount")
        ]

        replies = int(
            interactions[0]
            .split(" ")[0]
            .replace(",", "")
            .replace(".", "")
            or interactions[3]
        )

        retweets = int(
            interactions[1]
            .split(" ")[0]
            .replace(",", "")
            .replace(".", "")
            or interactions[4]
            or interactions[5]
        )

        likes = int(
            interactions[2]
            .split(" ")[0]
            .replace(",", "")
            .replace(".", "")
            or interactions[6]
            or interactions[7]
        )

        hashtags = [
            hashtag_node.full_text
            for hashtag_node in tweet.find(".twitter-hashtag")
        ]

        urls = [
            url_node.attrs["data-expanded-url"]
            for url_node in (
                tweet.find("a.twitter-timeline-link:not(.u-hidden)")
                + tweet.find(
                    "[class='js-tweet-text-container'] a[data-expanded-url]"
                )
            )
        ]
        urls = list(set(urls))  # delete duplicated elements

        photos = [
            photo_node.attrs["data-image-url"]
            for photo_node in tweet.find(
                ".AdaptiveMedia-photoContainer"
            )
        ]

        is_retweet = bool(
            tweet.find(".js-stream-tweet")[0].attrs.get(
                "data-retweet-id", None
            )
        )

        videos = []
        video_nodes = tweet.find(".PlayableMedia-player")
        for node in video_nodes:
            styles = node.attrs["style"].split()
            for style in styles:
                if style.startswith("background"):
                    tmp = style.split("/")[-1]
                    video_id = (
                        tmp[: tmp.index(".jpg")]
                        if ".jpg" in tmp
                        else tmp[: tmp.index(".png")]
                        if ".png" in tmp
                        else None
                    )
                    videos.append(video_id)


        tweet_info = {
            "tweet_id": tweet_id,
            "tweet_url": tweet_url,
            "username_owner": username,
            "user_id": user_id,
            "is_retweet": is_retweet,
            "is_pinned": is_pinned,
            "time": time,
            "text": text,
            "replies": replies,
            "retweets": retweets,
            "likes": likes,
            "entries": {
                "hashtags": hashtags,
                "urls": urls,
                "photos": photos,
                "videos": videos,
            },
        }
        return tweet_info
