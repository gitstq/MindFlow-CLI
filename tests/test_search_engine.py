# -*- coding: utf-8 -*-
"""Tests for search engine: Tokenizer, TF-IDF, BM25, Chinese/English tokenization."""

import math
import unittest

from mindflow_cli.models import KnowledgeSnippet, SearchResult
from mindflow_cli.search_engine import (
    BM25Calculator,
    SearchEngine,
    TFIDFCalculator,
    Tokenizer,
)


class TestTokenizer(unittest.TestCase):
    """Tests for the Tokenizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tokenizer = Tokenizer()

    def test_english_tokenization(self):
        """Test tokenizing English text."""
        text = "Hello world, this is a test."
        tokens = self.tokenizer.tokenize(text)
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)
        self.assertIn("test", tokens)

    def test_lowercasing(self):
        """Test that tokens are lowercased."""
        text = "UPPERCASE Mixed Case"
        tokens = self.tokenizer.tokenize(text)
        for token in tokens:
            self.assertEqual(token, token.lower())

    def test_punctuation_removal(self):
        """Test that punctuation is removed."""
        text = "hello, world! how are you?"
        tokens = self.tokenizer.tokenize(text)
        self.assertNotIn("hello,", tokens)
        self.assertNotIn("world!", tokens)
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)

    def test_empty_string(self):
        """Test tokenizing an empty string."""
        tokens = self.tokenizer.tokenize("")
        self.assertEqual(tokens, [])

    def test_stopwords_filtered(self):
        """Test that English stopwords are filtered."""
        text = "the quick brown fox jumps over the lazy dog"
        tokens = self.tokenizer.tokenize(text)
        self.assertNotIn("the", tokens)
        self.assertNotIn("over", tokens)
        self.assertIn("quick", tokens)
        self.assertIn("brown", tokens)
        self.assertIn("fox", tokens)

    def test_chinese_tokenization(self):
        """Test tokenizing Chinese text."""
        text = "这是一个测试"
        tokens = self.tokenizer.tokenize(text)
        self.assertTrue(len(tokens) > 0)
        self.assertIsInstance(tokens, list)
        for token in tokens:
            self.assertIsInstance(token, str)

    def test_chinese_english_mixed(self):
        """Test tokenizing mixed Chinese-English text."""
        text = "Python编程语言非常强大"
        tokens = self.tokenizer.tokenize(text)
        self.assertTrue(len(tokens) > 0)

    def test_chinese_punctuation_removal(self):
        """Test that Chinese punctuation is removed."""
        text = "你好，世界！这是一个测试。"
        tokens = self.tokenizer.tokenize(text)
        for token in tokens:
            self.assertNotIn("，", token)
            self.assertNotIn("！", token)
            self.assertNotIn("。", token)

    def test_custom_ngram_size(self):
        """Test tokenizer with custom Chinese n-gram size."""
        tokenizer = Tokenizer(chinese_ngram_size=3)
        text = "人工智能技术"
        tokens = tokenizer.tokenize(text)
        self.assertTrue(len(tokens) > 0)


class TestTFIDFCalculator(unittest.TestCase):
    """Tests for TF-IDF Calculator."""

    def setUp(self):
        """Set up test fixtures."""
        self.calc = TFIDFCalculator()
        self.calc.add_document("doc1", ["python", "programming", "language"])
        self.calc.add_document("doc2", ["java", "programming", "language"])
        self.calc.add_document("doc3", ["machine", "learning", "python"])

    def test_idf_calculation(self):
        """Test IDF calculation."""
        # "python" appears in doc1 and doc3 (2 out of 3)
        idf = self.calc.get_idf("python")
        self.assertGreater(idf, 0)

    def test_idf_rare_term(self):
        """Test that rare terms have higher IDF."""
        # "machine" appears only in doc3
        idf_rare = self.calc.get_idf("machine")
        # "programming" appears in doc1 and doc2
        idf_common = self.calc.get_idf("programming")
        self.assertGreater(idf_rare, idf_common)

    def test_idf_nonexistent_term(self):
        """Test IDF for a term not in the index."""
        idf = self.calc.get_idf("nonexistent")
        self.assertEqual(idf, 0.0)

    def test_document_vector(self):
        """Test getting document vector."""
        vector = self.calc.get_document_vector("doc1")
        self.assertIn("python", vector)
        self.assertIn("programming", vector)
        self.assertIn("language", vector)

    def test_similarity(self):
        """Test document similarity calculation."""
        doc_vector = self.calc.get_document_vector("doc1")
        query_vector = {"python": 1.0, "programming": 1.0}
        sim = self.calc.similarity(doc_vector, query_vector)
        self.assertGreater(sim, 0)


class TestBM25Calculator(unittest.TestCase):
    """Tests for BM25 Calculator."""

    def setUp(self):
        """Set up test fixtures."""
        self.calc = BM25Calculator()
        self.calc.add_document("doc1", ["python", "popular", "programming", "language"])
        self.calc.add_document("doc2", ["javascript", "web", "development"])
        self.calc.add_document("doc3", ["python", "web", "frameworks", "django", "flask"])
        self.calc.add_document("doc4", ["machine", "learning", "python"])
        self.calc.add_document("doc5", ["data", "analysis", "python", "pandas"])

    def test_bm25_score(self):
        """Test BM25 score calculation."""
        query_terms = ["python", "programming"]
        score = self.calc.score("doc1", query_terms)
        self.assertGreater(score, 0)

    def test_bm25_relevance(self):
        """Test that more relevant documents score higher."""
        # doc1 contains both "python" and "programming"
        score_doc1 = self.calc.score("doc1", ["python", "programming"])
        # doc2 contains neither
        score_doc2 = self.calc.score("doc2", ["python", "programming"])
        self.assertGreater(score_doc1, score_doc2)

    def test_bm25_empty_query(self):
        """Test BM25 with empty query terms."""
        score = self.calc.score("doc1", [])
        self.assertEqual(score, 0.0)

    def test_bm25_nonexistent_doc(self):
        """Test BM25 for a nonexistent document."""
        score = self.calc.score("nonexistent", ["python"])
        self.assertEqual(score, 0.0)


class TestSearchEngine(unittest.TestCase):
    """Tests for the SearchEngine class."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = SearchEngine()
        self.snippets = [
            KnowledgeSnippet(
                title="Python Basics",
                content="Python is a popular programming language",
                source="test",
                tags=["python", "programming"],
            ),
            KnowledgeSnippet(
                title="JavaScript Web Dev",
                content="JavaScript is used for web development",
                source="test",
                tags=["javascript", "web"],
            ),
            KnowledgeSnippet(
                title="Python Web Frameworks",
                content="Python web frameworks include Django and Flask",
                source="test",
                tags=["python", "web"],
            ),
            KnowledgeSnippet(
                title="Machine Learning",
                content="Machine learning algorithms in Python",
                source="test",
                tags=["ai", "ml"],
            ),
            KnowledgeSnippet(
                title="Data Analysis",
                content="Data analysis with Python pandas",
                source="test",
                tags=["data", "python"],
            ),
        ]
        self.engine.add_snippets(self.snippets)

    def test_search_basic(self):
        """Test basic search functionality."""
        results = self.engine.search("Python")
        self.assertTrue(len(results) > 0)
        # All results should be SearchResult instances
        for r in results:
            self.assertIsInstance(r, SearchResult)
            self.assertGreaterEqual(r.score, 0)

    def test_search_returns_sorted(self):
        """Test that results are sorted by score descending."""
        results = self.engine.search("Python")
        if len(results) > 1:
            scores = [r.score for r in results]
            self.assertEqual(scores, sorted(scores, reverse=True))

    def test_search_max_results(self):
        """Test that max_results is respected."""
        results = self.engine.search("Python", max_results=2)
        self.assertLessEqual(len(results), 2)

    def test_search_no_results(self):
        """Test search with a term that matches nothing."""
        results = self.engine.search("xyznonexistent123")
        # May return results with zero score
        if results:
            for r in results:
                self.assertEqual(r.score, 0.0)

    def test_search_empty_query(self):
        """Test search with empty query."""
        results = self.engine.search("")
        self.assertEqual(len(results), 0)

    def test_search_relevance(self):
        """Test that more relevant documents rank higher."""
        results = self.engine.search("web development")
        doc_ids = [r.snippet.id for r in results]
        # JavaScript Web Dev should rank high for "web development"
        js_snippet = self.snippets[1]
        self.assertIn(js_snippet.id, doc_ids)

    def test_search_matched_terms(self):
        """Test that matched terms are populated."""
        results = self.engine.search("Python programming")
        if results:
            self.assertTrue(len(results[0].matched_terms) > 0)

    def test_search_min_score(self):
        """Test that min_score threshold works."""
        all_results = self.engine.search("Python")
        results = self.engine.search("Python", min_score=100.0)
        # With very high min_score, should return fewer or no results
        self.assertTrue(len(results) <= len(all_results))

    def test_add_snippet(self):
        """Test adding a single snippet."""
        engine = SearchEngine()
        snippet = KnowledgeSnippet(title="Test", content="Test content")
        engine.add_snippet(snippet)
        results = engine.search("Test")
        self.assertEqual(len(results), 1)

    def test_remove_snippet(self):
        """Test removing a snippet from index."""
        snippet = self.snippets[0]
        self.engine.remove_snippet(snippet.id)
        results = self.engine.search("Python Basics")
        # Should not find the removed snippet
        for r in results:
            self.assertNotEqual(r.snippet.id, snippet.id)

    def test_tfidf_algorithm(self):
        """Test search with TF-IDF algorithm."""
        engine = SearchEngine(algorithm="tfidf")
        engine.add_snippets(self.snippets)
        results = engine.search("Python")
        self.assertTrue(len(results) > 0)

    def test_hybrid_algorithm(self):
        """Test search with hybrid algorithm."""
        engine = SearchEngine(algorithm="hybrid")
        engine.add_snippets(self.snippets)
        results = engine.search("Python")
        self.assertTrue(len(results) > 0)

    def test_tokenize_and_count(self):
        """Test tokenize_and_count method."""
        counts = self.engine.tokenize_and_count("python programming python")
        self.assertIn("python", counts)
        self.assertGreater(counts["python"], 1)


if __name__ == "__main__":
    unittest.main()
