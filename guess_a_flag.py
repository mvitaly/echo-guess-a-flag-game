import logging
import random
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
from enum import Enum
import json

with open('data.json', 'r') as f:
    FLAGS_DATA = json.load(f)

FLAGS_DATA2 = {
    'BR': {
        'country_names': ['Brazil'],
        'flag_design': 'A green field with the large yellow diamond (rhombus) '
                       'in the center bearing the blue disk, '
                       'which is formed the celestial globe, '
                       'depicted the starry sky of twenty-seven '
                       'small white five-pointed stars spanned '
                       'by the white equatorial curved band '
                       'with the National Motto: "ORDEM E PROGRESSO" '
                       '(Portuguese for "ORDER AND PROGRESS"), written in green.'
    },
    'US': {
        'country_names': ['United States of America', 'United States', 'USA', 'US'],
        'flag_design': 'Thirteen horizontal stripes alternating red and white; '
                       'in the canton, 50 white stars of alternating numbers '
                       'of six and five per row on a blue field'
    },
    'RU': {
        'country_names': ['Russia', 'Russian Federation'],
        'flag_design': 'A horizontal tricolour of white, blue and red'
    },
    'IL': {
        'country_names': ['Israel'],
        'flag_design': 'A blue Star of David between two horizontal blue stripes on a white field.'
    },
    'JP': {
        'country_names': ['Japan'],
        'flag_design': 'A red sun-disc centered on a white rectangular field'
    }
}


START_GAME_STATEMENTS = ['lets_start']
WIN_STATEMENTS = ['win']
LOSE_STATEMENTS = ['lose']
AGAIN_STATEMENTS = ['lets_start']


app = Flask(__name__)
#app.config['ASK_VERIFY_REQUESTS'] = False

ask = Ask(app, "/")
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

logger = logging.getLogger("guess_a_flag")
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

logger.addHandler(ch)

logger.info("Init")


class GameType(Enum):
    CHOICES = (2, 'flag_choices')

    def __init__(self, number_of_flags, flag_template):
        self.number_of_flags = number_of_flags
        self.flag_template = flag_template


@ask.launch
def launch():
    logger.info("New game")
    welcome_msg = render_template('welcome')
    help_msg = render_template('help')
    return question('{} {}'.format(welcome_msg, help_msg))


@ask.intent('AMAZON.HelpIntent')
def help():
	help_msg = render_template('help')
	return question(help_msg)


@ask.intent('AMAZON.CancelIntent')
@ask.intent('AMAZON.StopIntent')
def cancel():
	return statement('')


@ask.intent('FlagDescriptionIntent')
def flag_description(country):
	logger.info("Flag for country: " + str(country))
	
	if country is not None:
		found_country = next(
			(country_code for country_code, flag_data in FLAGS_DATA.items()
				if any(country_name.lower() == country.lower() for country_name in flag_data['country_names'])),
			None
			)
	else:
		found_country = None
		country = ''

	if found_country is None:
		country_not_found_msg = render_template('country_not_found', country=country)
		return question(country_not_found_msg)
	
	flag_design = FLAGS_DATA[found_country]['flag_design']
	flag_country_description_msg = render_template('flag_country_description', country=country, flag_design=flag_design)
	return statement(flag_country_description_msg)


@ask.intent("StartChoicesGameIntent")
def start_choices_game():
    return start_game(GameType.CHOICES)


def start_game(game_type, initial_statements=START_GAME_STATEMENTS):
    session.attributes['game_type'] = game_type.name

    # get a random flag
    country_code = random.choice(list(FLAGS_DATA.keys()))
    session.attributes['country'] = country_code

    choices = get_flag_choices(country_code)
    session.attributes['choices'] = choices

    return ask_for_answer(initial_statements, country_code, choices)


def ask_for_answer(initial_statements, chosen_country_code, choices):
    initial_statement = random.choice(initial_statements)
    initial_statement_msg = render_template(initial_statement)
    flag_design = FLAGS_DATA[chosen_country_code]['flag_design']
    flag_description_msg = render_template('flag_description', flag_design=flag_design)
    flag_msg = render_template('flag_choices', choices=choices)
    return question('{} {} {}'.format(initial_statement_msg, flag_description_msg, flag_msg))


def get_flag_choices(country_code):
    country_name = FLAGS_DATA[country_code]['country_names'][0]
    other_countries = list(FLAGS_DATA.keys())
    other_countries.remove(country_code)
    other_country_code = random.choice(other_countries)
    other_country_name = FLAGS_DATA[other_country_code]['country_names'][0]
    choices = [country_name, other_country_name]
    random.shuffle(choices)
    return choices


@ask.intent("MakeAGuessIntent")
def answer(guess):
    logger.info("Guess: " + str(guess))

    country_code = session.attributes.get('country')
    if country_code is None:
        not_started_msg = render_template('not_started')
        return question(not_started_msg)

	if guess is None:
		return repeat()
	
    country_names = FLAGS_DATA[country_code]['country_names']
    correct_guess = any(country_name.lower() == guess.lower() for country_name in country_names)

    if correct_guess:
        initial_statements = WIN_STATEMENTS
    else:
        initial_statements = LOSE_STATEMENTS

    return start_game(GameType[session.attributes['game_type']], initial_statements)


@ask.intent("RepeatIntent")
def repeat():
    country_code = session.attributes.get('country')
    if country_code is None:
        not_started_msg = render_template('not_started')
        return question(not_started_msg)

    choices = session.attributes['choices']
    return ask_for_answer(AGAIN_STATEMENTS, country_code, choices)


if __name__ == '__main__':
    app.run(debug=True)
