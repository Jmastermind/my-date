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
import os
from datetime import datetime
from pathlib import Path

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout

os.environ['KIVY_ORIENTATION'] = 'Portrait'

kivy.require('2.2.1')
__version__ = '1.1'


class UI(BoxLayout):
    """Main UI widget class."""

    def on_touch_move(self, touch) -> None:
        """Handle slide gestures."""
        app = App.get_running_app()
        if (touch.ox - touch.x) > 100:
            app.data_mode = 'diff'
            app.ui_update(1)
        elif (touch.ox - touch.x) < -100:
            app.data_mode = 'norm'
            app.ui_update(1)


class MyDate(App):
    """Main app class."""

    data_mode = 'diff'
    data_1 = ''
    data_2 = ''

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

    def calculate_diff(self, dt: datetime) -> str:
        """Calculate time difference."""
        if not isinstance(dt, datetime):
            return 'Invalid data'
        diff_dt = datetime.today() - dt
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

    def read_file_date(self, date_number: int) -> None:
        """Read dates from files and set variables."""
        try:
            with open(f'data/data_{date_number}.txt', 'r') as file:
                file_dt = datetime.strptime(file.read(), '%H:%M:%S %d.%m.%Y')
                if date_number == 1:
                    self.data_1 = file_dt
                elif date_number == 2:
                    self.data_2 = file_dt
        except OSError:
            self.ui.ids.status_label.text = (
                f'Could not open file: data/data_{date_number}.txt'
            )

    def write_file_date(self, date_number: int, button) -> None:
        """Write dates to files and update UI."""
        if button.text == f'UPDATE DATE {date_number}':
            if Path(f'data/data_{date_number}.txt').exists():
                (
                    Path(f'data/data_{date_number}.txt').replace(
                        f'data/data_{date_number}_bk.txt',
                    )
                )
            try:
                with open(f'data/data_{date_number}.txt', 'w') as file:
                    file.write(datetime.today().strftime('%H:%M:%S %d.%m.%Y'))
                    self.ui.ids.status_label.text = (
                        f'Date {date_number} has been updated'
                    )
                    button.text = 'UNDO'
            except OSError:
                self.ui.ids.status_label.text = (
                    f'Could not write to file: data/data_{date_number}.txt'
                )
        else:
            (
                Path(f'data/data_{date_number}_bk.txt').replace(
                    f'data/data_{date_number}.txt',
                )
            )
            self.ui.ids.status_label.text = (
                f'Date {date_number} has been restored'
            )
            button.text = f'UPDATE DATE {date_number}'
        self.read_file_date(date_number)
        self.ui_update(1)

    def build(self) -> UI:
        """Application startup."""
        self.ui = UI()
        self.read_file_date(1)
        self.read_file_date(2)
        self.ui_update(1)
        Clock.schedule_interval(self.ui_update, 1)
        return self.ui


if __name__ == '__main__':
    MyDate().run()
    Path('data/data_1_bk.txt').unlink(missing_ok=True)
    Path('data/data_1_tmp.txt').unlink(missing_ok=True)
    Path('data/data_2_bk.txt').unlink(missing_ok=True)
    Path('data/data_2_tmp.txt').unlink(missing_ok=True)
