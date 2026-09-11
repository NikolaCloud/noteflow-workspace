"""
Юнит-тесты Markdown парсера и графа знаний NoteFlow.
"""

from noteflow.core.graph_engine import KnowledgeGraphEngine
from noteflow.core.markdown_parser import MarkdownParser


def test_wikilinks_extraction():
    md = "Смотри документацию в [[Архитектурный манифест]] и [[Спецификация API]]."
    links = MarkdownParser.extract_wikilinks(md)
    assert len(links) == 2
    assert "Архитектурный манифест" in links
    assert "Спецификация API" in links


def test_markdown_stats():
    text = "Первое слово второе слово третье слово."
    words, chars, reading_time = MarkdownParser.calculate_stats(text)
    assert words == 6
    assert chars > 0
    assert reading_time == 1


def test_graph_engine():
    docs = [
        {"id": 1, "title": "Doc A", "content": "Link to [[Doc B]]", "folder": "Main"},
        {"id": 2, "title": "Doc B", "content": "No links", "folder": "Main"},
    ]
    graph = KnowledgeGraphEngine.build_graph(docs)
    assert graph["total_nodes"] == 2
    assert graph["total_edges"] == 1
    assert graph["edges"][0]["source"] == "Doc A"
    assert graph["edges"][0]["target"] == "Doc B"

