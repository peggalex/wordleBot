from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from utilities import CHROME_WEBDRIVER_PATH, WordleGuessResult, WordleLetter, getNormalizedWordFreqs, getWords
from wordleBot6 import wordleBot


def removeModal(driver):
    driver.execute_script(
        "document.querySelector('game-app').shadowRoot.querySelector('game-modal').remove()")


def makeGuess(driver, guess: str):
    body = driver.find_element(by=By.TAG_NAME, value='body')
    for k in guess:
        body.send_keys(k)
        sleep(0.1)
    body.send_keys(Keys.RETURN)
    sleep(2)  # let the letters do their flippy thing


# YOU NEED TO DOWNLOAD A CHROMEDRIVER THAT MATCHES YOUR CHROME BROWSER VERSION
driver = webdriver.Chrome(executable_path=CHROME_WEBDRIVER_PATH)
# you may tweak this to use firefox if you wish

driver.get("https://www.nytimes.com/games/wordle/index.html")
assert "wordle" in driver.title.lower()

# sleep(0.5)

removeModal(driver)


def testWord() -> int or None:
    currentGuessNo = 0

    def getGuessResult(guess: str) -> WordleGuessResult:
        nonlocal currentGuessNo
        currentGuessNo += 1

        if 6 < currentGuessNo:
            raise Exception('lost game')

        makeGuess(driver, guess)

        guessRow = driver.execute_script(
            '''return Array.from(document.querySelector('game-app').shadowRoot.querySelectorAll('#board > game-row:not([letters=""]')).at(-1).shadowRoot''')

        guessResult = []
        for guessCol in guessRow.find_elements(by=By.CSS_SELECTOR, value='game-tile'):
            evaluation = guessCol.get_attribute('evaluation')
            wordleLetter = WordleLetter.GREY
            if evaluation == "correct":
                wordleLetter = WordleLetter.GREEN
            elif evaluation == "present":
                wordleLetter = WordleLetter.ORANGE
            else:
                assert evaluation == "absent"
            guessResult.append(wordleLetter)

        return guessResult

    allWords = getWords()
    wordFreqs = getNormalizedWordFreqs(allWords)
    noGuesses = wordleBot(getGuessResult, allWords, wordFreqs, True)
    return noGuesses


testWord()
sleep(5)
driver.close()
