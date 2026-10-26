from slack_bolt import App

from .add_to_runbook import handle_add_to_runbook
from .feedback_buttons import handle_feedback_button


def register(app: App):
    app.action("add_to_runbook")(handle_add_to_runbook)
    app.action("feedback")(handle_feedback_button)
