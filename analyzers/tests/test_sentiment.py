import nose.tools as nt

from ..sentiment import calculate_sentiment

sentences=[{"sentence1": "I loved the scurvy pirate movie with llamas and flowers."},
           {"sentence2": "Good software practices and absence of hypocrisy help business objectives."},]
paragraphs=[{"paragraph1": "Since this is an anaconda recipe, argument 2 wins in my mind. If it were being submitted "
             "to conda-recipes, I think argument 1 wins. Anyway, nothing that needs further work right now."},
            {"paragraph2": "For a recipe to be generally useful to the most people, it's best to specify simply g++"
             " (no full path) and use whichever one the user has first on PATH. This is not optimal for our current "
             "build system, because, as you point out, g++ is the older version on our build machines."},]


def test_sentence_sentiment():
    # polarity score calculated manually with TextBlob(sentence).polarity
    nt.assert_almost_equals(calculate_sentiment(sentences["sentence1"]), 0.7)


def test_paragraph_sentiment():
    nt.assert_almost_equals(calculate_sentiment(paragraphs["paragraph1"]), 0.22142857142857142)


def test_separate_paragraphs():
    nt.assert_almost_equals(calculate_sentiment(paragraphs), 0.26612554112554115)
