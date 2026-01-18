import pygame
import sys
import keyboard
import pygame
from openai import OpenAI
import json
import pygame_textinput
import requests
import os
import pdb
from io import BytesIO
import sounddevice as sd
from scipy.io.wavfile import write
import wavio as wv
# OpenAI API Setup
openai_client = OpenAI(api_key="Replace your API key here")


CHATGPT_QUIZ_MESSAGES = [
    {
        "role": "system",
        "content": "I am preparing an educational quiz. I will provide you a topic and you will give me questions. At first message, just wait for me to give you the topic. "
                   "I want you to give me one question at a time. I want a difficulty scale from 1 to 7 where 1 is the easiest and 7 is the hardest. "
                   "I want you to start with a question with difficulty level 3. Each time I give a correct answer, increase the difficulty by 1, and if difficulty is 7, do not change it. "
                   "Each time I give a wrong answer, decrease the difficulty by 1. If difficulty is 1, do not change it. "
                   "I will use these questions in an app, so I want you to give me the question as a Python dictionary. i want you to create an image prompt to generate an image related to the question by using dalle"
                   "The format is like this: {'Question': '', 'Options': [], 'Answer': '', 'ImagePrompt': ''}. "
                   "Do not include any comments, just give me the formatted question."
    }
]

def send_user_input_to_chatgpt(user_input):

    # Add user's last message to the chat array (context)
    CHATGPT_QUIZ_MESSAGES.append(
        {
            "role" : "user",
            "content" : user_input
        }
    )

    # Generate next 'Assistant' response by giving ChatGPT the entire history
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=CHATGPT_QUIZ_MESSAGES,
        max_tokens=1024
    )

    # Append newest response to the chat array (context)
    message = completion.choices[0].message
    CHATGPT_QUIZ_MESSAGES.append( message )

    # Return the message text to the game loop / user
    return message.content


# Initialize Pygame
pygame.init()

# Set up display
screen = pygame.display.set_mode((1000, 550))
pygame.display.set_caption("Quiz Game")

# Main game loop
running = True

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (100, 200, 255)
CORRECT_COLOR = (0, 255, 0)  # Green for correct answer
WRONG_COLOR = (255, 0, 0)    # Red for wrong answer

# Set up font
font = pygame.font.Font(None, 36)
option_font = pygame.font.Font(None, 28)





# Function to draw image
def draw_image(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        # Convert the response content into a Pygame-compatible surface
        image_data = BytesIO(response.content)
        image = pygame.image.load(image_data)
        # Resize the image
        image = pygame.transform.scale(image, (400, 200))
        
        
        screen.blit(image, (100, 100))  # Draw image at position (100, 100)
    except pygame.error:
        print(f"Error loading image {image_url}")

#function to generate image
def generate_image(image_prompt):
    response = openai_client.images.generate(
    model="dall-e-2",
    prompt=image_prompt,
    size="256x256",
    quality="standard",
    n=1,
    )
    return response.data[0].url
    #pygame.time.delay(10000)
    


# Function to display the question and image
def draw_question(QuestionData):
    question_text = QuestionData["Question"]
    max_width = 800  # Maximum width for the question box
    y_offset = 50  # Starting y position for the question

    # Split the text into words
    words = question_text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        # Check the width of the current line with the new word
        test_line = current_line + " " + word if current_line else word
        text_width, _ = font.size(test_line)

        if text_width <= max_width:
            current_line = test_line  # Add the word to the current line
        else:
            lines.append(current_line)  # Save the current line
            current_line = word  # Start a new line with the current word

    if current_line:
        lines.append(current_line)  # Add the last line

    # Render each line of the wrapped text
    for line in lines:
        question_line = font.render(line, True, BLACK)
        screen.blit(question_line, (150, y_offset))
        y_offset += question_line.get_height()
    '''
    image_url = generate_image(QuestionData["ImagePrompt"])
    draw_image(image_url)
    '''

# Function to display options and return their rects
optionsrects = []  # This will hold rectangles for each option
def draw_options(QuestionData, highlighted_rect=None):
    y_position = 310
    optionsrects.clear()  # Clear previous rectangles
    for idx, option in enumerate(QuestionData["Options"]):
        option_text = option_font.render(option, True, BLACK)
        rect = pygame.Rect(100, y_position, 400, 40)

        # Highlight button if needed
        if highlighted_rect == rect:
            color = CORRECT_COLOR if clicked_result == QuestionData["Answer"] else WRONG_COLOR
            pygame.draw.rect(screen, color, rect)
        else:
            pygame.draw.rect(screen, BUTTON_COLOR, rect)

        optionsrects.append(rect)
        screen.blit(option_text, (120, y_position + 10))
        y_position += 50  # Move down for the next option
    return optionsrects

clicked_result = "None"
highlighted_option = None  # To store which option was clicked
question_changed = False  # Flag to control when to update the question

# Flag to track whether an option was clicked
option_clicked = False



#voice record function starts

def voicerecord():
    # Sampling frequency
    freq = 44100

    # Recording duration
    duration = 3

    # Start recorder with the given values of 
    # duration and sample frequency
    recording = sd.rec(int(duration * freq), 
                    samplerate=freq, channels=1)

    # Record audio for the given number of seconds
    sd.wait()

    wv.write("recording1.wav", recording, freq, sampwidth=2)

    sd.play(recording, freq)
    sd.wait()

#voice record function ends

# function for transcription starts

def mytranscription():
    audio_file= open("recording1.wav", "rb")
    transcription = openai_client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file
    )
    print(transcription.text)
    return transcription.text

#function for transcription ends




print("Press 'z' to start voice recording")

key = input().strip().lower()

if key == 'z':


    print("Recording started...")

    voicerecord()

print("Recording completed!")







topic = mytranscription()
QuestionData = eval(send_user_input_to_chatgpt(topic))   

#initial question drawn
screen.fill(WHITE)
draw_question(QuestionData)
draw_options(QuestionData)
url = generate_image(QuestionData["ImagePrompt"] + " " + "If there is text in the image, I want it to be in English")
draw_image(url)

while running:
    
    # Make background white before beginning
    
    screen.fill(WHITE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and not option_clicked:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            # Check if the click is within the bounds of any option
            for idx, rect in enumerate(optionrects):
                if rect.collidepoint(mouse_x, mouse_y):
                    clicked_result = QuestionData["Options"][idx]
                    if clicked_result == QuestionData["Answer"]:
                        highlighted_option = rect  # Highlight the correct answer
                       
                    else:
                        highlighted_option = rect  # Highlight the wrong answer
                    option_clicked = True  # Set flag to indicate an option was clicked
                    
                    
                    NextQuestion = eval(send_user_input_to_chatgpt(clicked_result)) 
                    print(f"Clicked result: {clicked_result}")  # Output clicked result for debugging
        #print("tip")
        #print(type(QuestionData))
        #print(QuestionData)
    # Draw the question and image
    draw_question(QuestionData) 
    draw_image(url)
    # Draw the options and highlight if necessary
    optionrects = draw_options(QuestionData, highlighted_option)
    
    # Update the display
    pygame.display.update()

    # Handle post-click delay and question change
    if option_clicked:
        #pygame.time.delay(1000)  # Delay of 1 second (1000 milliseconds)
        # Move to the next question
        QuestionData = NextQuestion 
        print(QuestionData)
        highlighted_option = None  # Reset highlighted option
        option_clicked = False  # Reset the flag for the next question
        question_changed = False
        url = generate_image(QuestionData["ImagePrompt"]+ " " + "If there is text in the image, I want it to be in English")

    # Update the display
    pygame.display.update()

# Quit Pygame
pygame.quit()
sys.exit()

