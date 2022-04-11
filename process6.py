import time
from utilities import LETTERS, Domains, getNormalizedWordFreqs, getWords
from concurrent.futures import ProcessPoolExecutor

from wordleBot6 import getAvgNoValidGuesses


def getBestWordleWords():
    allWords = getWords()
    wordFreqs = getNormalizedWordFreqs(allWords)

    mustHavesCount: dict[str, int] = {}
    domains: Domains = [set(LETTERS) for _ in range(5)]

    totalStart = time.perf_counter()

    batchSize = 100

    validGuesses = []
    for i in range(0, len(allWords), batchSize):
        batchWords = allWords[i:i+batchSize]
        with ProcessPoolExecutor() as ex:
            start = time.perf_counter()

            batchValidGuesses = list(ex.map(
                getAvgNoValidGuesses,
                [(guessWord, domains, mustHavesCount, allWords, wordFreqs)
                    for guessWord in batchWords]
            ))

            validGuesses.extend(batchValidGuesses)

            end = time.perf_counter()
            print(
                f"\t{i+batchSize}/{len(allWords)} | time: {end-totalStart:.1f} secs | since last: {end-start:.1f}")

    wordToNoGuesses = {allWords[i]: validGuesses[i]
                       for i in range(len(allWords))}
    sortedWords = sorted(wordToNoGuesses, key=lambda w: wordToNoGuesses[w])
    print(f'best words: {sortedWords[:5]}')


if __name__ == "__main__":
    getBestWordleWords()
