from app.services.reply_parser import ReplyParser


def test_complete_command_and_note():
    parser = ReplyParser()
    result = parser.parse("Re: Reminder", "done submitted at 9:15")
    assert result.command == "complete"
    assert result.note == "submitted at 9:15"


def test_ambiguous_text():
    parser = ReplyParser()
    result = parser.parse("Re", "will do later")
    assert result.ambiguous is True


def test_ignore_oof():
    parser = ReplyParser()
    result = parser.parse("Automatic Reply", "I am out of office")
    assert result.ignored is True
