import time
from utilities import LETTERS, MIN_WEIGHT, WORDLEPREVANSWERS_FILENAME, Domains, getGuessResultFunc, getNormalizedWordFreqs, getWords, WordleLetter, WordleGuessResult, isValidGuess, updateDomains
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor

import json

DEBUGGING = False


def log(*str):
    if (DEBUGGING):
        print('\t', *str)


starterWord = "lares"  # hardcoded, found from process6.py


def getWordWeight(word: str, wordFreqs: dict[str, float]):
    return wordFreqs.get(word, MIN_WEIGHT/2)


def getAvgNoValidGuesses(args) -> float:

    guessWord, _domains, _mustHavesCount, currentWords, wordFreqs = args
    validGuessesCache = {}

    def process(wordleWord: str):

        guessResult = getGuessResultFunc(
            wordleWord)(guessWord)

        guessResultStr = "".join('_' if l == WordleLetter.GREY else 'o' if l ==
                                 WordleLetter.ORANGE else 'x' for l in guessResult)

        if guessResultStr not in validGuessesCache:

            domains: Domains = [set(d) for d in _domains]
            mustHavesCount: dict[str, int] = {**_mustHavesCount}

            updateDomains(guessWord, guessResult,
                          domains, mustHavesCount)

            noGuess = 0
            for word in currentWords:

                if isValidGuess(word, domains, mustHavesCount):

                    noGuess += 1

            if noGuess == 0:
                raise Exception(
                    f'no guesses | domains - old: {_domains}, new: {domains} | mustHavesCount - old: {_mustHavesCount}, new: {mustHavesCount}')

            validGuessesCache[guessResultStr] = noGuess

        return validGuessesCache[guessResultStr], guessResultStr

    weightedTotal = 0
    isUselessWord = True
    guessStr = ""

    for i in range(len(currentWords)):
        wordleWord = currentWords[i]
        noValidGuesses, guessResultStr = process(wordleWord)
        weightedTotal += noValidGuesses * getWordWeight(wordleWord, wordFreqs)
        isUselessWord = isUselessWord and (noValidGuesses == len(currentWords))
        guessStr += guessResultStr

    return (weightedTotal / len(currentWords), isUselessWord, guessStr)


def getNextGuess(_domains: list[set[str]], _mustHavesCount: dict[str, int], currentWords: list[str], allWords: list[str], wordFreqs) -> float:

    log(f'all words length: {len(allWords)} | current words length: {len(currentWords)}')
    avgGuesses: dict[str, int] = {}

    uselessWordIndices = []

    checkedGuessStrs = set()

    for i in range(len(allWords)):
        guessWord = allWords[i]

        avgGuess, isUseless, guessStr = getAvgNoValidGuesses(
            (guessWord, _domains, _mustHavesCount, currentWords, wordFreqs))

        if isUseless or guessStr in checkedGuessStrs:
            # we gained no new information by trying this word
            uselessWordIndices.append(i)

        checkedGuessStrs.add(guessStr)

        avgGuesses[guessWord] = avgGuess

    for uselessWordIndex in reversed(uselessWordIndices):
        allWords.pop(uselessWordIndex)
        # this is a copy of allWords and won't affect any other wordle attempts

    currentWordsSet = set(currentWords)
    return min(
        avgGuesses,
        key=lambda w: (
            avgGuesses[w],
            0 if w in currentWordsSet else 1,
            -wordFreqs.get(w, 0)
        )
    )


def wordleBot(getGuessResult: Callable[[str], WordleGuessResult], allWords, wordFreqs, debugging=False) -> int:
    global DEBUGGING
    DEBUGGING = debugging

    mustHavesCount: dict[str, int] = {}
    domains: Domains = [set(LETTERS) for _ in range(5)]

    guessNo = 0
    correct = False
    prevGuesses: list[str] = []

    prevWords: list[str] = []

    currentWords = allWords
    allUsefulWords = [*allWords]

    while True:
        prevWords = currentWords
        guessNo += 1

        word: str
        if len(currentWords) == 1:
            word = currentWords[0]
        else:
            word = getNextGuess(domains, mustHavesCount,
                                currentWords, allUsefulWords, wordFreqs) if 1 < guessNo else starterWord

        log(f"{guessNo}. guessing: {word}")
        prevGuesses.append(word)

        guessResult = getGuessResult(word)
        if all(wordleLetter == WordleLetter.GREEN for wordleLetter in guessResult):
            correct = True
            break

        updateDomains(word, guessResult, domains, mustHavesCount)

        currentWords = tuple(w for w in prevWords if isValidGuess(
            w, domains, mustHavesCount))

        log(f"\tmustHavesCount: {mustHavesCount}")
        for i in range(5):
            log(f"\t{i}. domain: {''.join(domains[i])}")

        log(f"\tcurrentWords: {currentWords}")

        if not currentWords:
            break

    if correct:
        log("guessed word:", word)

    return guessNo if correct else None


def testWord(args, shouldLog=False) -> int or None:
    wordle, i, allWords, wordFreqs = args
    if i % 100 == 0:
        print("done:", i)
    log("\ntrue ans:", wordle)
    noGuesses = wordleBot(getGuessResultFunc(
        wordle, shouldLog), allWords, wordFreqs, shouldLog)
    if noGuesses == None:
        print("!!! failed to guess:", wordle)
    else:
        if 6 < noGuesses:
            print("lost to word:", wordle, noGuesses,
                  "freq:", f"{wordFreqs.get(wordle,0):.2f}")
    return noGuesses


def testPrevWordles():
    allWords = getWords()
    wordFreqs = getNormalizedWordFreqs(allWords)

    with open(WORDLEPREVANSWERS_FILENAME, 'r') as rf:

        wordles = json.load(rf)

        noGuessesLst = []
        totalStart = time.perf_counter()
        step = 6*3
        for i in range(0, len(wordles), step):
            with ProcessPoolExecutor() as ex:
                start = time.perf_counter()

                noGuessesSubLst = [noGuesses for noGuesses in ex.map(
                    testWord,
                    [(wordles[i], i, allWords, wordFreqs)
                     for i in range(i, min(i+step, len(wordles)))]
                ) if noGuesses is not None]

            noGuessesLst.extend(noGuessesSubLst)

            end = time.perf_counter()
            print(
                f"\t{i+step}/{len(wordles)} | time: {end-totalStart:.1f} secs | since last: {end-start:.1f}")

        guessesDist = {}
        for noGuesses in noGuessesLst:
            guessesDist[noGuesses] = guessesDist.get(noGuesses, 0) + 1
        print(
            f"avg guesses: {sum(noGuessesLst)/len(noGuessesLst)} | min guesses: {min(noGuessesLst)} | max guesses: {max(noGuessesLst)} | times failed: {sum(count for noGuesses,count in guessesDist.items() if 6 < noGuesses)} | times succeeded: {sum(guessesDist.values())}")
        print("guesses dist:", guessesDist)
        print("...done")


if __name__ == "__main__":
    allWords = getWords()
    testWord(('stair', 0, allWords, getNormalizedWordFreqs(allWords)), True)
    # testPrevWordles()
