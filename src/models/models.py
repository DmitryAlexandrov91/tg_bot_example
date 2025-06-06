from datetime import datetime
from random import sample
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import (
    BaseModel,
)
from .constants import (
    ACCEPTABLE_SYMBOLS,
    MAX_LEN_CONTACT_INFO_RESTAURANT,
    MAX_LEN_EMAIL,
    MAX_LEN_FIRST_NAME,
    MAX_LEN_LAST_NAME,
    MAX_LEN_PATRONYMIC,
    MAX_LEN_PHONE_NUMBER,
    MAX_LEN_RESTAURANT_NAME,
    MAX_LEN_SHORT_ADDRESS_RESTAURANT,
    MAX_LEN_TIMEZONE,
    MOSCOW_TIMEZONE,
    REMINDER_DAYS_BEFORE,
    TOKEN_LENGTH,
    UserRole,
)
from .mixins import (
    FeedbackRequestMixin,
    NotificationMixin,
    QuestionMixin,
    ReferencePointMixin,
    RoadMapMixin,
    TestMixin,
)

GET_UNIQUE_TOKEN_ERROR = 'Не удалось создать уникальный токен.'
UNIQUE_ERROR_MESSAGE = 'Предложенный вариант токена уже существует.'


class User(BaseModel):
    """Модель пользователя."""

    first_name: Mapped[str] = mapped_column(
        String(MAX_LEN_FIRST_NAME), nullable=False)
    last_name: Mapped[str] = mapped_column(
        String(MAX_LEN_LAST_NAME), nullable=False)
    patronymic: Mapped[str] = mapped_column(
        String(MAX_LEN_PATRONYMIC), nullable=False)
    role: Mapped[str] = mapped_column(default=UserRole.USER, nullable=False)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(
        String(MAX_LEN_EMAIL), nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(
        String(MAX_LEN_PHONE_NUMBER), nullable=False, unique=True)
    timezone: Mapped[str] = mapped_column(
        String(MAX_LEN_TIMEZONE), default=MOSCOW_TIMEZONE)
    additional_info: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    restaurant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('restaurant.id'),
    )
    restaurant: Mapped[Optional['Restaurant']] = relationship(
        back_populates='users',
    )

    manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))
    manager: Mapped[Optional['User']] = relationship(
        'User',
        remote_side='User.id',
        back_populates='interns',
    )
    interns: Mapped[List['User']] = relationship(
        'User',
        back_populates='manager',
        foreign_keys='User.manager_id',
    )

    roadmaps: Mapped[List['UserRoadMap']] = relationship(
        back_populates='user',
        cascade="all, delete-orphan",
    )

    invitation_links: Mapped[List['InvitationLink']] = relationship(
        back_populates='user', cascade="all, delete-orphan",
    )

    # dialogs: Mapped[List['Dialog']] = relationship(
    #     back_populates='manager',
    #     foreign_keys='Dialog.manager_id',
    # )
    is_education_complete: Mapped[bool] = mapped_column(Boolean, default=False)


class Restaurant(BaseModel):
    """Модель ресторана."""

    name: Mapped[str] = mapped_column(
        String(MAX_LEN_RESTAURANT_NAME), nullable=False)
    full_address: Mapped[str] = mapped_column(Text, nullable=False)
    short_address: Mapped[str] = mapped_column(
        String(MAX_LEN_SHORT_ADDRESS_RESTAURANT), nullable=False, unique=True)
    contact_information: Mapped[str] = mapped_column(
        String(MAX_LEN_CONTACT_INFO_RESTAURANT), nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    users: Mapped[List['User']] = relationship(back_populates='restaurant')

    template_roadmaps: Mapped[List['TemplateRoadMap']] = relationship(
        back_populates='restaurant',
        cascade="all, delete-orphan",
    )

    template_referencepoints: Mapped[
        List['TemplateReferencePoint']] = relationship(
            back_populates='restaurant',
            cascade="all, delete-orphan",
        )

    tests: Mapped[List['TemplateTest']] = relationship(
        back_populates='restaurant',
        cascade="all, delete-orphan",
    )


class TemplateRoadMap(RoadMapMixin, BaseModel):
    """Шаблон дорожной карты."""

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    restaurant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('restaurant.id'))
    restaurant: Mapped[Optional['Restaurant']] = relationship(
        back_populates='template_roadmaps')

    reference_points: Mapped[List['TemplateReferencePoint']] = relationship(
        back_populates='template_roadmap',
        cascade="all, delete-orphan",
    )


class TemplateReferencePoint(ReferencePointMixin, BaseModel):
    """Шаблон контрольной точки."""

    restaurant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('restaurant.id'))
    restaurant: Mapped[Optional['Restaurant']] = relationship(
        back_populates='template_referencepoints')

    templateroadmap_id: Mapped[int] = mapped_column(
        ForeignKey('templateroadmap.id'))
    template_roadmap: Mapped['TemplateRoadMap'] = relationship(
        back_populates='reference_points')

    notification: Mapped[Optional['TemplateNotification']] = relationship(
        back_populates='reference_point',
        cascade="all, delete",
        single_parent=True,
        lazy='selectin',
    )

    test_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('templatetest.id', ondelete="SET NULL"),
    )
    test: Mapped[Optional['TemplateTest']] = relationship(
        back_populates='reference_points',
        lazy='selectin',
    )

    feedback_request: Mapped[
        Optional['TemplateFeedbackRequest']] = relationship(
            back_populates='reference_point',
            cascade="all, delete",
            single_parent=True,
            lazy='selectin',
        )


class RoadMap(RoadMapMixin, BaseModel):
    """Дорожная карта пользователя (выполняемая)."""

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    reason_termination: Mapped[Optional[str]] = mapped_column(Text)

    reference_points: Mapped[List['ReferencePoint']] = relationship(
        back_populates='roadmap',
        cascade="all, delete-orphan",
        lazy='selectin',
    )

    user_associations: Mapped[List['UserRoadMap']] = relationship(
        back_populates='roadmap',
        cascade="all, delete-orphan",
    )

    @property
    def get_all_points(self) -> List['ReferencePoint']:
        """Возвращает список контрольных точек дорожной карты."""
        return sorted(self.reference_points, key=lambda x: x.order_execution)

    @property
    def get_active_points(self) -> List['ReferencePoint']:
        """Возвращает только активные контрольные точки."""
        return sorted(
            [pt for pt in self.reference_points if not pt.is_completed],
            key=lambda x: x.order_execution,
        )


class ReferencePoint(ReferencePointMixin, BaseModel):
    """Контрольная точка пользователя (выполняемая)."""

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    trigger_datetime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False)
    check_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reminder_days_before: Mapped[int] = mapped_column(
        Integer, default=REMINDER_DAYS_BEFORE)
    completion_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=False)

    roadmap_id: Mapped[int] = mapped_column(ForeignKey('roadmap.id'))
    roadmap: Mapped['RoadMap'] = relationship(
        back_populates='reference_points')

    notification: Mapped[Optional['Notification']] = relationship(
        back_populates='reference_point',
        cascade="all, delete",
        single_parent=True,
        lazy='selectin',
    )

    test: Mapped[Optional['Test']] = relationship(
        back_populates='reference_point',
        cascade="all, delete",
        single_parent=True,
        lazy='selectin',
    )

    feedback_request: Mapped[Optional['FeedbackRequest']] = relationship(
        back_populates='reference_point',
        cascade="all, delete",
        single_parent=True,
        lazy='selectin',
    )


class UserRoadMap(BaseModel):
    """Связь пользователя и дорожной карты."""

    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped['User'] = relationship(back_populates='roadmaps')

    roadmap_id: Mapped[int] = mapped_column(
        ForeignKey('roadmap.id', ondelete="CASCADE"),
        nullable=False,
    )
    roadmap: Mapped['RoadMap'] = relationship(
        back_populates='user_associations')


class InvitationLink(BaseModel):
    """Модель пригласительной ссылки."""

    is_used: Mapped[bool] = mapped_column(Boolean, default=True)
    link_token: Mapped[str] = mapped_column(
        String(TOKEN_LENGTH),
        unique=True,
        default=''.join(sample(ACCEPTABLE_SYMBOLS, TOKEN_LENGTH)),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    user: Mapped['User'] = relationship(back_populates='invitation_links')


class Test(TestMixin, BaseModel):
    """Модель теста."""

    questions: Mapped[List['Question']] = relationship(
        back_populates='test',
        cascade="all, delete-orphan",
    )

    referencepoint_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('referencepoint.id', ondelete="CASCADE"),
        unique=True,
    )

    reference_point: Mapped[
        Optional['ReferencePoint']] = relationship(
        back_populates='test',
        uselist=False,
    )


class Question(QuestionMixin, BaseModel):
    """Модель вопросов теста."""

    user_answer: Mapped[Optional[int]] = mapped_column(Integer)

    test_id: Mapped[Optional[int]] = mapped_column(ForeignKey('test.id'))
    test: Mapped[Optional['Test']] = relationship(
        back_populates='questions',
    )


class Notification(NotificationMixin, BaseModel):
    """Модель уведомлений."""

    user_feedback: Mapped[Optional[str]] = mapped_column(String)

    referencepoint_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('referencepoint.id', ondelete="CASCADE"),
        unique=True,
    )

    reference_point: Mapped[
        Optional['ReferencePoint']] = relationship(
            back_populates='notification',
            uselist=False,
        )


class FeedbackRequest(FeedbackRequestMixin, BaseModel):
    """Модель запроса обратной связи."""

    user_answer: Mapped[Optional[str]] = mapped_column(Text)

    reference_point_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('referencepoint.id', ondelete="CASCADE"),
        unique=True,
    )

    reference_point: Mapped[
        Optional['ReferencePoint']] = relationship(
            back_populates='feedback_request',
            uselist=False,
        )


class TemplateTest(TestMixin, BaseModel):
    """Модель теста (шаблон)."""

    questions: Mapped[List['TemplateQuestion']] = relationship(
        back_populates='test',
        cascade="all, delete-orphan",
    )

    reference_points: Mapped[List['TemplateReferencePoint']] = relationship(
        back_populates='test',
    )

    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey('restaurant.id', ondelete="CASCADE"),
        nullable=False,
    )
    restaurant: Mapped['Restaurant'] = relationship(
        back_populates='tests',
    )


class TemplateQuestion(QuestionMixin, BaseModel):
    """Модель вопросов теста (шаблон)."""

    templatetest_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('templatetest.id'))
    test: Mapped[Optional['TemplateTest']] = relationship(
        back_populates='questions')


class TemplateNotification(NotificationMixin, BaseModel):
    """Модель уведомлений (шаблон)."""

    referencepoint_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('templatereferencepoint.id', ondelete="CASCADE"),
        unique=True,
    )
    reference_point: Mapped[Optional['TemplateReferencePoint']] = relationship(
        back_populates='notification',
        uselist=False,
    )


class TemplateFeedbackRequest(FeedbackRequestMixin, BaseModel):
    """Модель запроса обратной связи (шаблон)."""

    reference_point_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('templatereferencepoint.id', ondelete="CASCADE"),
        unique=True,
    )
    reference_point: Mapped[Optional['TemplateReferencePoint']] = relationship(
        back_populates='feedback_request',
        uselist=False,
    )


class Dialog(BaseModel):
    """Модель диалогов между менеджером и интерном."""

    message: Mapped[str] = mapped_column(Text, nullable=False)
    message_datetime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False)

    sender_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('user.id', ondelete="SET NULL"),
        nullable=True,
    )

    recipient_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('user.id', ondelete="SET NULL"),
        nullable=True,
    )
