from slack_sdk.models.blocks import (
    ActionsBlock,
    Block,
    ButtonElement,
    ContextBlock,
    MarkdownTextObject,
    SectionBlock,
)


def build_runbook_suggestion_blocks(topic: str) -> list[Block]:
    """Build the offer to save a thread to a runbook."""
    return [
        SectionBlock(
            text=MarkdownTextObject(
                text=f":books: This thread looks like it belongs in a runbook: *{topic}*"
            )
        ),
        ActionsBlock(
            elements=[
                ButtonElement(
                    text="Add to runbook",
                    action_id="add_to_runbook",
                    value=topic,
                    style="primary",
                )
            ]
        ),
    ]


def build_runbook_saving_blocks(topic: str, user_id: str) -> list[Block]:
    """Build the note shown while a thread is being saved to a runbook."""
    return [
        SectionBlock(
            text=MarkdownTextObject(
                text=f":books: This thread looks like it belongs in a runbook: *{topic}*"
            )
        ),
        ContextBlock(
            elements=[
                MarkdownTextObject(text=f"<@{user_id}> is adding it to a runbook…")
            ]
        ),
    ]
