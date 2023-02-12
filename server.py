import time
import os
import flask
from flask import g
from flask_cors import CORS
from flask_socketio import SocketIO, emit







from playwright.sync_api import sync_playwright

#PROFILE_DIR = "/tmp/playwright" if '--profile' not in sys.argv else sys.argv[sys.argv.index('--profile') + 1]
PORT = 5001 
#if '--port' not in sys.argv else int(sys.argv[sys.argv.index('--port') + 1])
APP = flask.Flask(__name__)
PLAY = sync_playwright().start()
BROWSER = PLAY.firefox.launch_persistent_context(
user_data_dir="c:/shashank/jain",
headless=False,
java_script_enabled=True,
)
PAGE = BROWSER.new_page()
CORS(APP)
#cors = CORS(APP, resources={r"/chat_socket": {"origins": "*"}})
#APP.config['CORS_ORIGINS'] = "http://localhost:*"
#APP.config['CORS_ORIGINS'] = "*"
#SocketIO(app,cors_allowed_origins="*")
#socketio = SocketIO(APP,cors_allowed_origins="*")


def get_input_box():
    """Get the child textarea of `PromptTextarea__TextareaWrapper`"""
    return PAGE.query_selector("textarea")

def is_logged_in():
    # See if we have a textarea with data-id="root"
    return get_input_box() is not None

def is_loading_response() -> bool:
    """See if the send button is diabled, if it does, we're not loading"""
    return not PAGE.query_selector("textarea ~ button").is_enabled()

def send_message(message):
    # Send the message
    box = get_input_box()
    box.click()
    box.fill(message)
    box.press("Enter")

def get_last_message_old():
    """Get the latest message"""
    while is_loading_response():
        time.sleep(0.25)
    page_elements = PAGE.query_selector_all("div[class*='markdown prose w-full break-words dark:prose-invert light']")
    #page_elements = PAGE.query_selector_all("div[class*='result-streamin markdown prose w-full break-words dark:prose-invert light']")
    last_element = page_elements.pop()
    return last_element.inner_text()

def get_last_message():
    """Get the latest message"""
    seen_messages = set()
    while True:
        if  is_loading_response():
            page_elements = PAGE.query_selector_all("div[class*='result-streaming markdown prose w-full break-words dark:prose-invert light']")
            
            last_element = page_elements.pop()
            message = last_element.inner_text()
            if message not in seen_messages:
                print(message)
                seen_messages.add(message)
        else :
            break;
        time.sleep(0.25)

#<div class="flex ml-1 mt-1.5 md:w-full md:m-auto md:mb-2 gap-0 md:gap-2 justify-center"><button class="btn flex justify-center gap-2 btn-neutral border-0 md:border"><svg stroke="currentColor" fill="none" stroke-width="1.5" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" class="h-3 w-3" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><polyline points="1 4 1 10 7 10"></polyline><polyline points="23 20 23 14 17 14"></polyline><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path></svg>Regenerate response</button></div>

def regenerate_response():
    """Clicks on the Try again button.
    Returns None if there is no button"""
    try_again_button = PAGE.query_selector("button:has-text('Try again')")
    if try_again_button is not None:
        try_again_button.click()
    return try_again_button

def get_reset_button():
    """Returns the reset thread button (it is an a tag not a button)"""
    return PAGE.query_selector("a:has-text('Reset thread')")


#@socketio.on('message')
#def handle_message(message):
#    print("recieved message")
#   send_message(message)
#   gen = get_last_message()
#    if gen is not None:
#        for text in gen:
#           emit('response', text)
#           time.sleep(1) # wait for 1 second before sending the next result



@APP.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if flask.request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": 3600
        }
        return ('', 204, headers)

    message = flask.request.form.get("q")
    print("Received message: ", message)
    send_message(message)
    
    gen = get_last_message()
    for text in gen:
        print(text)
        time.sleep(1) # wait for 1 second before printing the next result

    
    response = get_last_message()
    print("Response: ", response)
    return response







# create a route for regenerating the response
@APP.route("/regenerate", methods=["POST"])
def regenerate():
    print("Regenerating response")
    if regenerate_response() is None:
        return "No response to regenerate"
    response = get_last_message()
    print("Response: ", response)
    return response

@APP.route("/reset", methods=["POST"])
def reset():
    print("Resetting chat")
    get_reset_button().click()
    return "Chat thread reset"

@APP.route("/restart", methods=["POST"])
def restart():
    global PAGE,BROWSER,PLAY
    PAGE.close()
    BROWSER.close()
    PLAY.stop()
    time.sleep(0.25)
    PLAY = sync_playwright().start()
    BROWSER = PLAY.chromium.launch_persistent_context(
        user_data_dir="/tmp/playwright",
        headless=False,
    )
    PAGE = BROWSER.new_page()
    PAGE.goto("https://chat.openai.com/")
    return "API restart!"


def start_browser():
    PAGE.goto("https://chat.openai.com/")
    if not is_logged_in():
        print("Please log in to OpenAI Chat")
        print("Press enter when you're done")
        input()
    else:
        print("Logged in")
        APP.run(port=5001, threaded=False)

if __name__ == "__main__":
    start_browser()
