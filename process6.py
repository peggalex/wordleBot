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
        if i % (batchSize * 5) == 0 and 0 < len(validGuesses):
            _start = time.perf_counter()
            _wordToNoGuesses = {allWords[i]: validGuesses[i]
                                for i in range(len(validGuesses))}
            _end = time.perf_counter()
            print(
                f'best word: {min(_wordToNoGuesses, key=lambda w: _wordToNoGuesses[w])} | time: {_end-_start:.1f}')
        batchWords = allWords[i:i+batchSize]
        with ProcessPoolExecutor() as ex:
            start = time.perf_counter()

            batchValidGuesses = list(x[0] for x in ex.map(
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
    print(f'best words: {({w:wordToNoGuesses[w] for w in sortedWords[:5]})}')


if __name__ == "__main__":
    getBestWordleWords()
