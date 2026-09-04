"""
Движок графа знаний (Knowledge Graph & Backlinks).
"""

from collections import defaultdict
from typing import Any, Dict, List, Set


class KnowledgeGraphEngine:
    @staticmethod
    def build_graph(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Строит граф связей между документами по двунаправленным wiki-ссылкам [[doc]].
        """
        doc_titles = {d["title"] for d in documents}
        nodes = []
        edges = []
        in_degree = defaultdict(int)

        for d in documents:
            title = d["title"]
            from noteflow.core.markdown_parser import MarkdownParser
            links = MarkdownParser.extract_wikilinks(d["content"])
            valid_targets = [l for l in links if l in doc_titles and l != title]

            for target in valid_targets:
                edges.append({"source": title, "target": target})
                in_degree[target] += 1

        for d in documents:
            title = d["title"]
            nodes.append({
                "id": d["id"],
                "title": title,
                "folder": d["folder"],
                "connections": in_degree[title]
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

