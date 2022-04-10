import json
from enum import Enum
from typing import Callable
import math
import numpy as np
import matplotlib.pyplot as plt
WORDLEWORDS_FILENAME = "wordleWords.json"
WORDLEPREVANSWERS_FILENAME = "wordleAnswers.json"
WORDPOPULARITY_FILENAME = "unigram_freq.csv"
CHROME_WEBDRIVER_PATH = "./chromedriver"

LETTERS = {chr(i) for i in range(ord('a'), ord('z')+1)}


def getWordFreqs() -> dict[str, int]:
    wordFreq = {}

    with open(WORDPOPULARITY_FILENAME, 'r') as wordPop_rf:
        wordPop_i = 0

        row = wordPop_rf.readline()  # skip header
        while True:
            row = wordPop_rf.readline().strip()
            if not row:
                break
            wordPop_i += 1
            if (wordPop_i % 50000 == 0):
                print(f'\t{wordPop_i} word popularities read so far')
            word, freq = row.split(',')
            if len(word) == 5:
                wordFreq[word] = int(freq)

    return wordFreq


MIN_WEIGHT = 0.1


def getNormalizedWordFreqs(words: list[str]) -> dict[str, float]:
    wordFreq = {k: v for k, v in getWordFreqs().items() if k in words}
    minWordFreq = min(wordFreq.values())

    for word, freq in wordFreq.items():
        wordFreq[word] = freq - minWordFreq + 1

    maxWordFreq = max(wordFreq.values())

    '''plt.hist(wordFreq.values(), 100, density=True, facecolor='g', alpha=0.75)
    plt.title('Freq dist')
    plt.show()'''
    # plot word freq dist before log normalized

    base = 10
    logMaxWordFreq = math.log(maxWordFreq, base)
    for word, freq in wordFreq.items():
        logFreq = math.log(freq, base)
        normalizedLogFreq = logFreq/logMaxWordFreq
        normalizedLogFreqWithMin = normalizedLogFreq * \
            (1-MIN_WEIGHT) + MIN_WEIGHT
        wordFreq[word] = normalizedLogFreqWithMin

    '''plt.hist(wordFreq.values(), 50, density=True, facecolor='r', alpha=0.75)
    plt.title('Log freq dist')
    plt.show()'''
    # plot word freq dist after log normalized

    return wordFreq


def getWords() -> list[str]:
    with open(WORDLEWORDS_FILENAME, 'r') as rf:
        words = json.load(rf)
        return words


class WordleLetter(Enum):
    GREEN = 1
    ORANGE = 2
    GREY = 3


WordleGuessResult = list[WordleLetter]


def getGuessResultFunc(wordle: str, log=False) -> Callable[[str], WordleGuessResult]:
    def getGuessResult(guess: str) -> WordleGuessResult:
        guessResult = [WordleLetter.GREY] * 5

        greenIndices = set()
        orangeIndices = set()
        for i in range(5):
            guessLetter = guess[i]
            wordleLetter = wordle[i]
            if guessLetter == wordleLetter:
                guessResult[i] = WordleLetter.GREEN
                greenIndices.add(i)

        for i in range(5):
            if i in greenIndices:
                continue

            guessLetter = guess[i]
            for j in range(5):
                if guessLetter == wordle[j] and j not in greenIndices.union(orangeIndices):
                    guessResult[i] = WordleLetter.ORANGE
                    orangeIndices.add(j)
        if log:
            print('\t', ['_' if l == WordleLetter.GREY else 'o' if l ==
                         WordleLetter.ORANGE else 'x' for l in guessResult])
        return guessResult

    return getGuessResult


Domains = list[set[str]]


def updateDomains(word: str, guessResult: WordleGuessResult, domains: Domains, mustHavesCount:  dict[str, int]):

    def isGreen(index: int) -> bool:
        return 1 == len(domains[index])

    def tryRemove(aSet: set, key: any):
        if key in aSet:
            aSet.remove(key)

    resultMustHavesCount = {}
    resultOranges = set()

    for i in range(5):
        guessResultLetter = guessResult[i]
        guessLetter = word[i]

        if (guessResultLetter != WordleLetter.GREY):
            resultMustHavesCount[guessLetter] = resultMustHavesCount.get(
                guessLetter, 0
            ) + 1

        if guessResultLetter == WordleLetter.GREEN:
            domains[i] = set(guessLetter)

        elif guessResultLetter == WordleLetter.ORANGE:
            resultOranges.add(guessLetter)

    for i in range(5):
        guessResultLetter = guessResult[i]
        guessLetter = word[i]

        if (guessResultLetter != WordleLetter.GREEN):
            tryRemove(domains[i], guessLetter)

        if guessResultLetter == WordleLetter.GREY:
            if guessLetter not in resultOranges:
                for j in range(5):
                    if not isGreen(j):
                        tryRemove(domains[j], guessLetter)

    for letter in set(list(mustHavesCount) + list(resultMustHavesCount)):
        mustHavesCount[letter] = max([d.get(letter, 0) for d in (
            mustHavesCount,
            resultMustHavesCount
        )])


def isValidGuess(word: str, domains: Domains, mustHavesCount: dict[str, int]):
    if mustHavesCount:
        return (
            all(letter in domain for letter, domain in zip(word, domains)) and
            all(count <= word.count(mustHave) for (
                mustHave, count) in mustHavesCount.items())
        )
    return all(letter in domain for letter, domain in zip(word, domains))
