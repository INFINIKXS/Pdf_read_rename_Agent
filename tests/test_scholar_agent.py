import pytest
from src.agent_core.scholar_agent import ScholarAgent

def test_read_search_terms_filters_only_queries(tmp_path):
    # Create a temporary Search_terms.md with mixed content
    content = '''
# Heading
("foo" OR "bar") AND (baz)
Example: (not a query)
AND: Narrows your search (all terms must be present).
("alpha" OR "beta") AND (gamma)
'''
    file_path = tmp_path / "Search_terms.md"
    file_path.write_text(content, encoding="utf-8")
    agent = ScholarAgent(search_terms_file=str(file_path))
    terms = agent.read_search_terms()
    assert terms == ['("foo" OR "bar") AND (baz)', '("alpha" OR "beta") AND (gamma)']


