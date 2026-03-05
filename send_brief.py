from brief import build_brief, render_brief_md
from services.telegram import send_message


def main():
    brief = build_brief()
    message = render_brief_md(brief)

    send_message(message)


if __name__ == "__main__":
    main()