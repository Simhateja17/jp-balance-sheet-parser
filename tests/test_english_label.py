from bsparser.labels import english_label


def test_japanese_label_gets_its_reviewed_translation():
    assert english_label("現金及び預金") == ("Cash and deposits", "translation_reviewed")
    assert english_label("建物及び構築物（純額）") == ("Buildings and structures, net", "translation_reviewed")


def test_japanese_label_not_in_the_dictionary_is_missing_never_guessed():
    assert english_label("謎の科目") == (None, "missing")


def test_english_label_is_its_own_english_label_marked_original():
    assert english_label("Cash and deposits") == ("Cash and deposits", "original")
