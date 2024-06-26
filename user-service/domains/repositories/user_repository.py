from functools import reduce
from sqlalchemy.orm import Session
from domains.models.user import User
from domains.repositories.repo_exceptions import *
from domains.repositories.utils import check_id_exists, check_id_not_exists, check_unique
from events.publisher_factory import PublisherFactory
from logger import LoggerFactory
from firebase_admin import auth
from sqlalchemy.sql import func


class UserRepository:
    session: Session

    def __init__(self, db_session: Session):
        self.session = db_session
        logger_factory = LoggerFactory()
        self.logger = logger_factory.get_logger()

        publisher_factory = PublisherFactory()
        self.publisher = publisher_factory.get_publisher()

    """
    Adds new User object to be persisted using User object

    :param new_user: User representing user to be added
    :return: User of added user
    """
    def _add_user(self, 
                  new_user: User):
        self.session.add(new_user)
        self.session.commit()
        self.publisher.publish(action=True, 
                               uuid=str(new_user.user_id))
        return new_user

    """
    Adds new User object to be persisted using User field parameters

    :param username: str of username
    :optional param user_id: str of uuid (must be able to be parsed to uuidv4)
    :optional param streaming_status: str of streaming status
    :return: User of added user
    """
    @check_id_not_exists(User, ["user_id"])
    def add_user(self, 
                 username=None, 
                 user_id=None, 
                 streaming_status=None,
                 profile_picture=None,
                 channel=None,
                 video_urls=None,
                 bio=None):

        new_user = User(username=username, 
                        user_id=user_id, 
                        streaming_status=streaming_status,
                        profile_picture=profile_picture,
                        channel=channel,
                        video_urls=video_urls,
                        bio=bio)
        return self._add_user(new_user)

    """
    Gets all User objects

    :return: list of User objects obtained from persisted data
    """
    def get_all_users(self):
        users = self.session.query(User).all()
        return users
    
    """
    Gets an existing User

    :param user_id: uuid of User
    :return: User object obtained from persisted data
    """
    @check_id_exists(User, ["user_id"])
    def get_user(self, user_id):
        user = self.session.get(User, user_id)
        return user

    """
    Deletes an existing User

    :param user_id: uuid of User
    :return: uuid of deleted User
    """
    @check_id_exists(User, ["user_id"])
    def delete_user(self, user_id):
        user = self.session.get(User, user_id)
        self.session.delete(user)
        self.session.commit()
        self.session.publish(action=False, uuid=str(user.user_id))
        return user_id

    """
    Adds following users to existing user

    :param user_id: uuid of User
    :param new_following: list of uuid of new following users
    :return: User
    """
    @check_id_exists(User, ["user_id", "following"])
    def add_following(self, user_id, following=None):
        user = self.session.get(User, user_id)
        new_following = self.session.get(User, following)
        if new_following in user.following:
            raise DuplicateFollowException(user.user_id, new_following.user_id)

        if user == new_following:
            raise SelfReferentialFollowException(user.user_id)

        user.following.extend([new_following])
        self.session.merge(user)
        self.session.commit()
        return user

    @check_id_exists(User, ["user_id", "following"])
    def remove_following(self, user_id, following=None):
        user = self.session.get(User, user_id)
        following = self.session.get(User, following)

        user.following.remove(following)
        self.session.merge(user)
        self.session.commit()
        return user

    """
    Updates a User object

    :param user: User object to be updated
    :return: User of updated user
    """
    def _update_user(self, user):
        self.session.merge(user)
        self.session.commit()
        return user

    """
    Updates a User object in backend and Firebase

    :optional param username: str of username
    :optional param streaming_status: str of streaming status
    :return: User of updated user
    """
    @check_id_exists(User, ["user_id"])
    def update_user(self, 
                    username=None, 
                    user_id=None, 
                    streaming_status=None,
                    profile_picture=None,
                    channel=None,
                    video_urls=None,
                    bio=None):
        user = self.session.get(User, user_id)
        if self.session.query(User).filter(User.username == username).first() is not None:
            raise NonUniqueException(User, "username")

        auth.update_user(user.user_id, display_name=username)
        
        user.username = username if username is not None else user.username
        user.streaming_status = streaming_status if streaming_status is not None else user.streaming_status
        user.profile_picture = profile_picture if profile_picture is not None else user.profile_picture
        user.channel = channel if channel is not None else user.channel
        user.video_urls = video_urls if video_urls is not None else user.video_urls
        user.bio = bio if bio is not None else user.bio
        return self._update_user(user)

    def get_live_users(self):
        users = self.session.query(User).filter(User.streaming_status == 1).order_by(func.random()).limit(5).all()
        return users

    @check_id_exists(User, ["user_id"])
    def add_video(self, user_id, video_url):
        user = self.session.get(User, user_id)
        user.video_urls = user.video_urls + [video_url]
        self._update_user(user)
        return user
