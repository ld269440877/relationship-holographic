from backend.api.training import _attribute_errors, _build_mastery_model
from backend.core.comparison_engine import comparison_engine
from backend.core.emotion_engine import emotion_engine
from backend.models.sample import InteractionSample


def test_emotion_engine_recognizes_intensity_deduplicates_and_labels():
    emotions = emotion_engine.recognize_emotion("我非常兴奋！！但也有点焦虑，真的非常焦虑！！")

    assert {item["word"] for item in emotions} == {"兴奋", "焦虑"}
    assert all(1 <= item["intensity"] <= 10 for item in emotions)
    assert emotion_engine.get_intensity_label(1) == "几乎察觉不到"
    assert emotion_engine.get_intensity_label(4) == "轻微"
    assert emotion_engine.get_intensity_label(6) == "中等"
    assert emotion_engine.get_intensity_label(8) == "强烈"
    assert emotion_engine.get_intensity_label(10) == "极度"
    assert emotion_engine.get_behavioral_anchor("喜", 6) == "语速变化，表情明显"


def test_emotion_engine_mixed_emotion_and_empty_paths():
    mixed = emotion_engine.analyze_mixed_emotion([
        {"spectrum": "爱", "word": "想要", "intensity": 7},
        {"spectrum": "惧", "word": "害怕", "intensity": 6},
    ])

    assert mixed is not None
    assert mixed["name"] == "纠结"
    assert mixed["components"][0]["word"] == "想要"
    assert "承认纠结" in mixed["response_principle"]
    assert emotion_engine.analyze_mixed_emotion([{"word": "焦虑"}]) is None
    assert emotion_engine.analyze_mixed_emotion([
        {"spectrum": "喜", "word": "满足", "intensity": 5},
        {"spectrum": "怒", "word": "愤怒", "intensity": 5},
    ]) is None


def test_comparison_engine_scores_problems_bonuses_and_report():
    weak = comparison_engine.compare("嗯", "听起来你今天很累，要不要说说？")

    assert weak.score < 100
    assert any(diff["name"] == "封闭式回应" for diff in weak.differences)
    assert any("开放式问题" in suggestion for suggestion in weak.suggestions)

    strong = comparison_engine.compare(
        "听起来你有点失落，我注意到你刚才停了一下。要是你愿意，能说说发生了什么吗？忙的话也没关系。",
        "听起来你有点失落，想说我就在。",
    )
    report = comparison_engine.generate_diff_report(strong)

    assert strong.score == 100
    assert {diff["type"] for diff in strong.differences} == {"bonus"}
    assert "好回应：情绪反射" in report
    assert "改进建议" not in report


def test_comparison_engine_problem_specific_suggestions():
    short_emotion = comparison_engine.compare("情绪", "先别急，我们慢慢说。")
    long_analysis = comparison_engine.compare(
        "你这个情绪。所以你应该马上改变，因为这说明你长期以来都没有真正面对自己的需求，而且你的表达模式、关系期待、过去经验和当下压力都在互相缠绕。"
        "如果继续这样，你以后所有亲密关系都会重复同样的问题，所以现在必须立刻调整。",
        "先别急，我们慢慢说。",
    )
    report = comparison_engine.generate_diff_report(long_analysis)

    assert any(diff["name"] == "忽视情绪信号" for diff in short_emotion.differences)
    assert any(diff["name"] == "急于解决问题" for diff in long_analysis.differences)
    assert any(diff["name"] == "过度分析" for diff in long_analysis.differences)
    assert any("先承认情绪" in suggestion for suggestion in short_emotion.suggestions)
    assert any("少分析多感受" in suggestion for suggestion in long_analysis.suggestions)
    assert "❌" in report


def test_mastery_model_and_error_attribution_are_stage_aware():
    sample = InteractionSample(
        sample_uuid="core-mastery-sample",
        scenario_category="冲突",
        difficulty_level=2,
        context="对方表达委屈并开始退缩。",
        their_words="随便你。",
        emotion_tags_json='[{"spectrum":"哀","word":"委屈","intensity":7}]',
        hidden_need="被理解",
        boundary_test_level=8,
        bad_response="嗯。",
        good_response_soft="我听起来你有点委屈，我不想逼你，我们可以慢慢说。",
    )
    scores = {
        "emotion_score": 42,
        "need_score": 67,
        "safety_score": 81,
        "connection_score": 55,
        "boundary_score": 92,
        "style_score": 74,
        "repair_score": 20,
    }
    mastery = _build_mastery_model(scores)
    attributions = _attribute_errors(
        [{"type": "problem", "name": "忽视情绪信号", "desc": "没有接情绪"}],
        sample,
        scores,
    )

    assert mastery["weakest"]["dimension"] == "repair_score"
    assert mastery["stage"]["label"] in {"知道", "辨认", "操作", "迁移", "自然"}
    assert any(item["dimension"] == "emotion_score" for item in attributions)
    assert any(item["dimension"] == "boundary_score" for item in attributions)
