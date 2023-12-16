"""
MyDate.

An app to keep track of two dates.
It also provides information about how much time has passed since the dates
were recorded.

Classes:

    UI
    MainApp

"""
import math
import re
import os
from datetime import datetime
from pathlib import Path
import datetime

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.popup import Popup

Config.set('graphics', 'width', '405')
Config.set('graphics', 'height', '900')
Config.set('graphics', 'resizable', '0')

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker, relationship
from sqlalchemy.exc import IntegrityError, OperationalError

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    func,
    create_engine,
    ForeignKey,
    select,
)


os.environ['KIVY_ORIENTATION'] = 'Portrait'

kivy.require('2.2.1')
__version__ = '1.1'

# For Windows


# DATABASE

DB_URL = 'sqlite:///data/sqlite.db'
USER_LIMIT = 2
RECORDS_LIMIT = 30

engine = create_engine(DB_URL, echo=True)
session: sessionmaker[Session] = sessionmaker(engine)

dates = {}

class Base(DeclarativeBase):
    """Declarative base."""


class Activity(Base):
    """Activity model."""

    __tablename__ = 'activity_table'
    __table_args__ = (
        CheckConstraint(r"name REGEXP '^([a-zA-Z]|\s|\d){1,50}$'"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    records: Mapped[list['Record'] | None] = relationship(
        back_populates='activity',
        cascade='all, delete',
    )

    def __repr__(self) -> str:
        """To representation."""
        return self.name


class Record(Base):
    """Record model."""

    __tablename__ = 'record_table'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    date: Mapped[datetime.datetime] = mapped_column(
        DateTime(),
        server_default=func.now(),
    )
    activity_id: Mapped[int] = mapped_column(ForeignKey('activity_table.id'))
    activity: Mapped[Activity] = relationship(
        back_populates='records',
        single_parent=True,
    )

    def __repr__(self) -> str:
        """To representation."""
        return self.date.strftime('%H:%M:%S %a %d.%m.%Y')


def create_tables() -> None:
    """Create all tables."""
    Base.metadata.create_all(engine)


def delete_tables() -> None:
    """Create all tables."""
    Base.metadata.drop_all(engine)


def create_activity(name: str) -> int | None:
    """
    Create an activity in the database.

    Returns:
        The user's record info, None otherwise.
    """
    with session() as s:
        try:
            with s.begin():
                activity = Activity(name=name)
                s.add(activity)
            return activity.id
        except (IntegrityError, OperationalError):
            return None


def get_activities():
    with session() as s:
        activities: list[Activity] = s.scalars(select(Activity))
        if activities:
            data = []
            for activity in activities:
                record = s.scalars(
                        select(Record).where(Record.activity_id == activity.id).order_by(Record.id.desc())).first()
                record_date = record.date if record else None
                data.append((activity.name, record_date))
            return data
        return None


def delete_activity(name: str) -> bool:
    """
    Create an activity in the database.

    Returns:
        The user's record info, None otherwise.
    """
    with session() as s:
        with s.begin():
            activity = s.scalar(select(Activity).where(Activity.name == name))
            if activity:
                s.delete(activity)
                return True
    return False


def create_record(activity_id: int, date: str) -> datetime.datetime | None:
    """
    Create a record in the database.

    Returns:
        The user's record info, None otherwise.
    """
    with session() as s:
        try:
            with s.begin():
                activity = s.get(Activity, activity_id)
                if not activity:
                    return None
                dt = datetime.datetime.now()
                if date:
                    dt = datetime.datetime.strptime(date, '%H:%M %d.%m.%Y')
                record = Record(
                    activity=activity,
                    date=dt,
                )
                s.add(record)
                return record.date
        except (ValueError, IntegrityError, OperationalError):
            return None


def calculate_diff(dt: datetime) -> str:
    """Calculate time difference."""
    diff_dt = datetime.datetime.today() - dt
    hours_diff = (
        math.floor(diff_dt.total_seconds() / 60 / 60) - diff_dt.days * 24
    )
    min_diff = math.floor(diff_dt.total_seconds() / 60) - hours_diff * 60
    sec_diff = round(diff_dt.total_seconds()) - min_diff * 60

    days_case = 'day' if diff_dt.days == 1 else 'days'
    hours_case = 'hour' if hours_diff == 1 else 'hours'
    if diff_dt.days:
        return f'{diff_dt.days} {days_case} {hours_diff} {hours_case} ago'
    if hours_diff:
        return f'{hours_diff} {hours_case} {min_diff} min ago'
    if min_diff:
        return f'{min_diff} min {sec_diff} sec ago'
    if sec_diff:
        return f'{sec_diff} sec ago'
    return '0 sec ago'

# UI
class UI(BoxLayout):
    """Main UI widget class."""


class InfoPopup(Popup):
    """Info popup class."""


class ActivityWidget(BoxLayout):
    """Activity widget class."""

    @staticmethod
    def delete_activity(root):
        deleted = delete_activity(root.ids.activity_name.text)
        if not deleted:
            return None
        ui = App.get_running_app().ui
        ui.ids.scroll_group.remove_widget(root)
        try:
            dates.pop(root.ids.activity_name.text)
        except KeyError:
            pass

    @staticmethod
    def toggle_date_diff(root):
        cached_date = dates.get(root.ids.activity_name.text)
        if cached_date:
            root.ids.activity_data.text = cached_date
            dates.pop(root.ids.activity_name.text)
            return
        cur_date = root.ids.activity_data.text
        if cur_date:
            dates.update({root.ids.activity_name.text: cur_date})
            dt = datetime.datetime.strptime(root.ids.activity_data.text, '%H:%M:%S %a %d.%m.%Y')
            root.ids.activity_data.text = calculate_diff(dt)



class NameInput(TextInput):
    """Activity name input class."""

    def insert_text(self, substring, from_undo=False):
        s = re.sub(r'[^a-zA-Z\d\s]', '', substring)
        return super().insert_text(s, from_undo=from_undo)

    def on_text_validate(self):
        self.text = re.sub(r'\s{2,}', ' ', self.text)


class DataInput(TextInput):
    """Activity data input class."""

    def insert_text(self, substring, from_undo=False):
        s = re.sub(r'[^\d\s.:]', '', substring)
        return super().insert_text(s, from_undo=from_undo)

    def on_text_validate(self):
        self.text = re.sub(r'\s{2,}', ' ', self.text)


# App

class MyDate(App):
    """Main app class."""

    data_mode = 'diff'
    data_1 = ''
    data_2 = ''

    def init_activities(self):
        """Select activities from DB and create ActivityWidget for each of them."""
        create_tables()
        for name, record in get_activities():
            self.place_activity(name, record)

    def ui_update(self, dt: float) -> None:
        """Update labels."""
        if self.data_mode == 'diff':
            self.ui.ids.date_1_label.text = self.calculate_diff(self.data_1)
            self.ui.ids.date_2_label.text = self.calculate_diff(self.data_2)
        else:
            self.ui.ids.date_1_label.text = self.data_1.strftime(
                '%H:%M %A %d.%m.%Y',
            )
            self.ui.ids.date_2_label.text = self.data_2.strftime(
                '%H:%M %A %d.%m.%Y',
            )

    def add_activity(self, activity_name: str, activity_data: str, add_record: bool):
        """Add new activity row."""
        activity_id = create_activity(activity_name)
        if not activity_id:
            return None

        record = None
        if add_record:
            record = create_record(activity_id, activity_data)
        if add_record and not record:
            return None

        activity = ActivityWidget()
        activity.ids.activity_name.text = activity_name
        self.place_activity(activity_name, record)

    def place_activity(self, name: str, record: datetime.datetime | None):
        activity = ActivityWidget()
        activity.ids.activity_name.text = name
        if record:
            activity.ids.activity_data.text = record.strftime('%H:%M:%S %a %d.%m.%Y')
        index = len(self.ui.ids.scroll_group.children)
        self.ui.ids.scroll_group.add_widget(activity, index=index - index)

    def reset_data(self):
        delete_tables()
        create_tables()
        self.root.ids.scroll_group.clear_widgets()
        dates.clear()

    def build(self) -> UI:
        """Application startup."""
        self.ui = UI()
        self.init_activities()
        # self.ui_update(1)
        # Clock.schedule_interval(self.ui_update, 1)
        return self.ui


if __name__ == '__main__':
    MyDate().run()
