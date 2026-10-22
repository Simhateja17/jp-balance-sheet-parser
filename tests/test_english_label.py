from bsparser.labels import english_label


def test_japanese_label_gets_its_reviewed_translation():
    assert english_label("現金及び預金") == ("Cash and deposits", "translation_reviewed")
    assert english_label("建物及び構築物（純額）") == ("Buildings and structures, net", "translation_reviewed")
