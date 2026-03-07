from brief import build_brief, render_brief_html
from services.telegram import send_message


def run_brief():
    brief = build_brief()
    message = render_brief_html(brief)
    send_message(message)

def main():
    run_brief()

if __name__ == "__main__":
    main()