"""
搜索引擎模块 / Search Engine Module

纯Python实现的TF-IDF + BM25混合搜索引擎，支持中英文分词。
Pure Python implementation of TF-IDF + BM25 hybrid search engine
with Chinese and English tokenization support.
"""

from __future__ import annotations

import math
import re
import string
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

from .models import KnowledgeSnippet, SearchResult


class Tokenizer:
    """
    分词器 / Tokenizer

    支持中文（基于字符的n-gram）和英文（基于空格和标点）分词。
    Supports Chinese (character-based n-gram) and English
    (space and punctuation-based) tokenization.
    """

    # 英文停用词 / English stop words
    ENGLISH_STOP_WORDS: Set[str] = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above", "below",
        "between", "out", "off", "over", "under", "again", "further", "then",
        "once", "here", "there", "when", "where", "why", "how", "all", "both",
        "each", "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very", "just",
        "because", "but", "and", "or", "if", "while", "about", "up", "it",
        "its", "this", "that", "these", "those", "i", "me", "my", "we",
        "our", "you", "your", "he", "him", "his", "she", "her", "they",
        "them", "their", "what", "which", "who", "whom",
    }

    # 中文停用词 / Chinese stop words
    CHINESE_STOP_WORDS: Set[str] = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
        "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会",
        "着", "没有", "看", "好", "自己", "这", "他", "她", "它", "们",
        "那", "些", "么", "什么", "吗", "吧", "呢", "啊", "哦", "嗯",
        "把", "被", "让", "给", "从", "对", "与", "而", "但", "却", "又",
        "还", "已", "已经", "过", "来", "得", "地", "能", "可以", "这个",
        "那个", "之", "以", "及", "等", "等等", "或", "或者", "如果",
        "因为", "所以", "虽然", "但是", "不过", "然后", "于是", "因此",
    }

    def __init__(self, chinese_ngram_size: int = 2) -> None:
        """
        初始化分词器 / Initialize tokenizer

        参数 / Args:
            chinese_ngram_size: 中文n-gram大小 / Chinese n-gram size
        """
        self.chinese_ngram_size = chinese_ngram_size
        self._chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        self._english_pattern = re.compile(r'[a-zA-Z]+')
        self._punctuation = set(string.punctuation) | set("，。！？、；：""''（）【】《》…—·")

    def tokenize(self, text: str) -> List[str]:
        """
        分词 / Tokenize text

        参数 / Args:
            text: 输入文本 / Input text

        返回 / Returns:
            分词结果列表 / List of tokens
        """
        if not text:
            return []

        tokens: List[str] = []

        # 提取中文文本段 / Extract Chinese text segments
        chinese_segments = self._chinese_pattern.findall(text)
        for segment in chinese_segments:
            tokens.extend(self._tokenize_chinese(segment))

        # 提取英文文本段 / Extract English text segments
        english_segments = self._english_pattern.findall(text.lower())
        for segment in english_segments:
            tokens.extend(self._tokenize_english(segment))

        # 过滤停用词和短词 / Filter stop words and short tokens
        all_stop_words = self.ENGLISH_STOP_WORDS | self.CHINESE_STOP_WORDS
        filtered = [
            t for t in tokens
            if t not in all_stop_words and len(t) > 0
        ]

        return filtered

    def _tokenize_chinese(self, text: str) -> List[str]:
        """
        中文分词（基于字符n-gram） / Chinese tokenization (character-based n-gram)

        参数 / Args:
            text: 中文文本 / Chinese text

        返回 / Returns:
            分词结果 / Tokenization result
        """
        tokens: List[str] = []

        # 单字 / Single characters
        for char in text:
            if char not in self.CHINESE_STOP_WORDS:
                tokens.append(char)

        # n-gram / n-grams
        n = self.chinese_ngram_size
        for i in range(len(text) - n + 1):
            gram = text[i:i + n]
            # 检查n-gram中是否包含停用词 / Check if n-gram contains stop words
            has_stop = any(c in self.CHINESE_STOP_WORDS for c in gram)
            if not has_stop:
                tokens.append(gram)

        return tokens

    def _tokenize_english(self, text: str) -> List[str]:
        """
        英文分词 / English tokenization

        参数 / Args:
            text: 英文文本 / English text

        返回 / Returns:
            分词结果 / Tokenization result
        """
        # 简单的词干提取（后缀去除） / Simple stemming (suffix removal)
        word = text.lower()
        if len(word) > 5:
            for suffix in ("ing", "tion", "ment", "ness", "able", "ible"):
                if word.endswith(suffix) and len(word) - len(suffix) > 2:
                    word = word[:-len(suffix)]
                    break
            for suffix in ("ed", "er", "ly", "es", "s"):
                if word.endswith(suffix) and len(word) - len(suffix) > 2:
                    word = word[:-len(suffix)]
                    break

        return [word] if word and word not in self.ENGLISH_STOP_WORDS else []


class TFIDFCalculator:
    """
    TF-IDF计算器 / TF-IDF Calculator

    计算词频-逆文档频率，用于评估词语在文档中的重要性。
    Calculates Term Frequency-Inverse Document Frequency for evaluating
    the importance of terms in documents.
    """

    def __init__(self) -> None:
        """初始化TF-IDF计算器 / Initialize TF-IDF calculator"""
        self._doc_count: int = 0
        self._doc_freq: Dict[str, int] = defaultdict(int)
        self._doc_vectors: Dict[str, Dict[str, float]] = {}

    def add_document(self, doc_id: str, terms: List[str]) -> None:
        """
        添加文档到索引 / Add document to index

        参数 / Args:
            doc_id: 文档ID / Document ID
            terms: 术语列表 / List of terms
        """
        self._doc_count += 1
        term_freq = Counter(terms)
        unique_terms = set(terms)

        # 更新文档频率 / Update document frequency
        for term in unique_terms:
            self._doc_freq[term] += 1

        # 计算TF / Calculate TF
        total_terms = len(terms) if terms else 1
        doc_vector: Dict[str, float] = {}
        for term, count in term_freq.items():
            # 使用对数TF以减少高频词的影响 / Use log TF to reduce high-frequency impact
            doc_vector[term] = 1 + math.log(count) if count > 0 else 0

        self._doc_vectors[doc_id] = doc_vector

    def get_idf(self, term: str) -> float:
        """
        计算逆文档频率 / Calculate Inverse Document Frequency

        参数 / Args:
            term: 术语 / Term

        返回 / Returns:
            IDF值 / IDF value
        """
        df = self._doc_freq.get(term, 0)
        if df == 0:
            return 0.0
        return math.log((self._doc_count + 1) / (df + 1)) + 1

    def get_tfidf(self, doc_id: str, term: str) -> float:
        """
        计算TF-IDF值 / Calculate TF-IDF value

        参数 / Args:
            doc_id: 文档ID / Document ID
            term: 术语 / Term

        返回 / Returns:
            TF-IDF值 / TF-IDF value
        """
        tf = self._doc_vectors.get(doc_id, {}).get(term, 0.0)
        idf = self.get_idf(term)
        return tf * idf

    def get_document_vector(self, doc_id: str) -> Dict[str, float]:
        """
        获取文档的TF-IDF向量 / Get document's TF-IDF vector

        参数 / Args:
            doc_id: 文档ID / Document ID

        返回 / Returns:
            TF-IDF向量 / TF-IDF vector
        """
        doc_tf = self._doc_vectors.get(doc_id, {})
        return {term: tf * self.get_idf(term) for term, tf in doc_tf.items()}

    def similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """
        计算余弦相似度 / Calculate cosine similarity

        参数 / Args:
            vec1: 向量1 / Vector 1
            vec2: 向量2 / Vector 2

        返回 / Returns:
            余弦相似度 / Cosine similarity
        """
        # 获取公共键 / Get common keys
        common_keys = set(vec1.keys()) & set(vec2.keys())
        if not common_keys:
            return 0.0

        # 点积 / Dot product
        dot_product = sum(vec1[k] * vec2[k] for k in common_keys)

        # 向量长度 / Vector magnitudes
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    @property
    def doc_count(self) -> int:
        """文档总数 / Total document count"""
        return self._doc_count


class BM25Calculator:
    """
    BM25排序算法计算器 / BM25 Ranking Algorithm Calculator

    实现Okapi BM25算法，用于文档相关性排序。
    Implements the Okapi BM25 algorithm for document relevance ranking.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """
        初始化BM25计算器 / Initialize BM25 calculator

        参数 / Args:
            k1: 词频饱和参数 / Term frequency saturation parameter
            b: 文档长度归一化参数 / Document length normalization parameter
        """
        self.k1 = k1
        self.b = b
        self._doc_count: int = 0
        self._avg_doc_length: float = 0.0
        self._doc_freq: Dict[str, int] = defaultdict(int)
        self._doc_lengths: Dict[str, int] = {}
        self._doc_term_freqs: Dict[str, Dict[str, int]] = {}

    def add_document(self, doc_id: str, terms: List[str]) -> None:
        """
        添加文档到索引 / Add document to index

        参数 / Args:
            doc_id: 文档ID / Document ID
            terms: 术语列表 / List of terms
        """
        self._doc_count += 1
        term_freq = Counter(terms)
        unique_terms = set(terms)

        self._doc_lengths[doc_id] = len(terms)
        self._doc_term_freqs[doc_id] = dict(term_freq)

        for term in unique_terms:
            self._doc_freq[term] += 1

        # 更新平均文档长度 / Update average document length
        total_length = sum(self._doc_lengths.values())
        self._avg_doc_length = total_length / self._doc_count

    def score(self, doc_id: str, query_terms: List[str]) -> float:
        """
        计算文档与查询的BM25分数 / Calculate BM25 score for document and query

        参数 / Args:
            doc_id: 文档ID / Document ID
            query_terms: 查询术语列表 / List of query terms

        返回 / Returns:
            BM25分数 / BM25 score
        """
        doc_length = self._doc_lengths.get(doc_id, 0)
        doc_term_freqs = self._doc_term_freqs.get(doc_id, {})

        if self._avg_doc_length == 0:
            return 0.0

        score = 0.0
        query_term_freq = Counter(query_terms)

        for term, qtf in query_term_freq.items():
            if term not in doc_term_freqs:
                continue

            # 逆文档频率 / Inverse document frequency
            df = self._doc_freq.get(term, 0)
            idf = math.log(
                (self._doc_count - df + 0.5) / (df + 0.5) + 1
            )

            # 词频 / Term frequency
            tf = doc_term_freqs[term]

            # BM25公式 / BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * doc_length / self._avg_doc_length
            )

            score += idf * (numerator / denominator) * qtf

        return score

    @property
    def doc_count(self) -> int:
        """文档总数 / Total document count"""
        return self._doc_count


class SearchEngine:
    """
    搜索引擎 / Search Engine

    结合TF-IDF和BM25算法的混合搜索引擎，支持中英文全文搜索。
    Hybrid search engine combining TF-IDF and BM25 algorithms,
    supporting full-text search in Chinese and English.

    用法 / Usage:
        engine = SearchEngine()
        engine.add_snippet(snippet1)
        engine.add_snippet(snippet2)
        results = engine.search("关键词")
    """

    def __init__(
        self,
        algorithm: str = "bm25",
        chinese_ngram_size: int = 2,
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
        tfidf_weight: float = 0.3,
        bm25_weight: float = 0.7,
    ) -> None:
        """
        初始化搜索引擎 / Initialize search engine

        参数 / Args:
            algorithm: 搜索算法 ("tfidf", "bm25", "hybrid") / Search algorithm
            chinese_ngram_size: 中文n-gram大小 / Chinese n-gram size
            bm25_k1: BM25 k1参数 / BM25 k1 parameter
            bm25_b: BM25 b参数 / BM25 b parameter
            tfidf_weight: TF-IDF权重（混合模式） / TF-IDF weight (hybrid mode)
            bm25_weight: BM25权重（混合模式） / BM25 weight (hybrid mode)
        """
        self.algorithm = algorithm
        self.tokenizer = Tokenizer(chinese_ngram_size=chinese_ngram_size)
        self.tfidf = TFIDFCalculator()
        self.bm25 = BM25Calculator(k1=bm25_k1, b=bm25_b)
        self.tfidf_weight = tfidf_weight
        self.bm25_weight = bm25_weight
        self._snippets: Dict[str, KnowledgeSnippet] = {}
        self._doc_terms: Dict[str, List[str]] = {}

    def add_snippet(self, snippet: KnowledgeSnippet) -> None:
        """
        添加知识片段到搜索索引 / Add knowledge snippet to search index

        参数 / Args:
            snippet: 知识片段 / Knowledge snippet
        """
        self._snippets[snippet.id] = snippet
        text = f"{snippet.title} {snippet.content}"
        terms = self.tokenizer.tokenize(text)
        self._doc_terms[snippet.id] = terms

        self.tfidf.add_document(snippet.id, terms)
        self.bm25.add_document(snippet.id, terms)

    def add_snippets(self, snippets: List[KnowledgeSnippet]) -> None:
        """
        批量添加知识片段 / Batch add knowledge snippets

        参数 / Args:
            snippets: 知识片段列表 / List of knowledge snippets
        """
        for snippet in snippets:
            self.add_snippet(snippet)

    def remove_snippet(self, snippet_id: str) -> None:
        """
        从搜索索引中移除知识片段 / Remove knowledge snippet from search index

        注意：这是一个简化实现，完整实现需要重建索引。
        Note: This is a simplified implementation; full implementation
        requires index rebuild.

        参数 / Args:
            snippet_id: 知识片段ID / Snippet ID
        """
        self._snippets.pop(snippet_id, None)
        self._doc_terms.pop(snippet_id, None)

    def rebuild_index(self, snippets: List[KnowledgeSnippet]) -> None:
        """
        重建搜索索引 / Rebuild search index

        参数 / Args:
            snippets: 知识片段列表 / List of knowledge snippets
        """
        self._snippets.clear()
        self._doc_terms.clear()
        self.tfidf = TFIDFCalculator()
        self.bm25 = BM25Calculator()
        self.add_snippets(snippets)

    def search(
        self,
        query: str,
        max_results: int = 20,
        min_score: float = 0.0,
    ) -> List[SearchResult]:
        """
        搜索知识片段 / Search knowledge snippets

        参数 / Args:
            query: 搜索查询 / Search query
            max_results: 最大结果数 / Maximum number of results
            min_score: 最低分数阈值 / Minimum score threshold

        返回 / Returns:
            搜索结果列表 / List of search results
        """
        if not query or not self._snippets:
            return []

        query_terms = self.tokenizer.tokenize(query)
        if not query_terms:
            return []

        # 计算每个文档的分数 / Calculate scores for each document
        scored_results: List[Tuple[str, float]] = []

        for doc_id in self._snippets:
            score = self._calculate_score(doc_id, query_terms)
            if score >= min_score:
                scored_results.append((doc_id, score))

        # 按分数排序 / Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # 构建搜索结果 / Build search results
        results: List[SearchResult] = []
        for doc_id, score in scored_results[:max_results]:
            snippet = self._snippets[doc_id]
            highlighted_title = self._highlight(snippet.title, query_terms)
            highlighted_content = self._highlight(
                snippet.summary(200), query_terms
            )
            matched = self._get_matched_terms(query_terms, doc_id)

            results.append(SearchResult(
                snippet=snippet,
                score=round(score, 4),
                highlighted_title=highlighted_title,
                highlighted_content=highlighted_content,
                matched_terms=matched,
            ))

        return results

    def _calculate_score(self, doc_id: str, query_terms: List[str]) -> float:
        """
        计算文档分数 / Calculate document score

        参数 / Args:
            doc_id: 文档ID / Document ID
            query_terms: 查询术语 / Query terms

        返回 / Returns:
            综合分数 / Combined score
        """
        if self.algorithm == "bm25":
            return self.bm25.score(doc_id, query_terms)
        elif self.algorithm == "tfidf":
            # 使用TF-IDF向量相似度 / Use TF-IDF vector similarity
            doc_vector = self.tfidf.get_document_vector(doc_id)
            query_vector: Dict[str, float] = {}
            for term in query_terms:
                query_vector[term] = self.tfidf.get_idf(term)
            return self.tfidf.similarity(doc_vector, query_vector)
        else:
            # 混合模式 / Hybrid mode
            bm25_score = self.bm25.score(doc_id, query_terms)

            doc_vector = self.tfidf.get_document_vector(doc_id)
            query_vector: Dict[str, float] = {}
            for term in query_terms:
                query_vector[term] = self.tfidf.get_idf(term)
            tfidf_score = self.tfidf.similarity(doc_vector, query_vector)

            # 归一化BM25分数 / Normalize BM25 score
            max_bm25 = max(
                (self.bm25.score(did, query_terms) for did in self._snippets),
                default=1.0,
            )
            if max_bm25 > 0:
                bm25_score = bm25_score / max_bm25

            return (
                self.tfidf_weight * tfidf_score
                + self.bm25_weight * bm25_score
            )

    def _highlight(self, text: str, query_terms: List[str]) -> str:
        """
        高亮匹配的关键词 / Highlight matched keywords

        参数 / Args:
            text: 原始文本 / Original text
            query_terms: 查询术语 / Query terms

        返回 / Returns:
            高亮后的文本 / Highlighted text
        """
        if not query_terms or not text:
            return text

        # 过滤短词 / Filter short terms
        significant_terms = [t for t in query_terms if len(t) >= 2]
        if not significant_terms:
            return text

        result = text
        for term in significant_terms:
            # 使用标记代替ANSI颜色（便于多格式输出）
            # Use markers instead of ANSI colors (for multi-format output)
            result = re.sub(
                re.escape(term),
                f"[[{term}]]",
                result,
                flags=re.IGNORECASE,
            )

        return result

    def _get_matched_terms(
        self, query_terms: List[str], doc_id: str
    ) -> List[str]:
        """
        获取匹配的术语 / Get matched terms

        参数 / Args:
            query_terms: 查询术语 / Query terms
            doc_id: 文档ID / Document ID

        返回 / Returns:
            匹配的术语列表 / List of matched terms
        """
        doc_terms_set = set(self._doc_terms.get(doc_id, []))
        return [t for t in query_terms if t in doc_terms_set]

    def tokenize_and_count(self, text: str) -> Dict[str, int]:
        """
        分词并统计词频 / Tokenize and count term frequencies

        用于构建搜索索引。

        参数 / Args:
            text: 输入文本 / Input text

        返回 / Returns:
            术语-频率字典 / Term-frequency dictionary
        """
        terms = self.tokenizer.tokenize(text)
        return dict(Counter(terms))

    def suggest(self, prefix: str, max_suggestions: int = 5) -> List[str]:
        """
        搜索建议 / Search suggestions

        根据前缀提供搜索建议。

        参数 / Args:
            prefix: 搜索前缀 / Search prefix
            max_suggestions: 最大建议数 / Maximum number of suggestions

        返回 / Returns:
            建议列表 / List of suggestions
        """
        if not prefix or len(prefix) < 1:
            return []

        prefix_lower = prefix.lower()
        suggestions: Set[str] = set()

        for doc_id, terms in self._doc_terms.items():
            for term in terms:
                if term.startswith(prefix_lower) or prefix_lower in term:
                    suggestions.add(term)
                    if len(suggestions) >= max_suggestions * 2:
                        break
            if len(suggestions) >= max_suggestions * 2:
                break

        # 按长度排序，优先短词 / Sort by length, prefer shorter terms
        sorted_suggestions = sorted(suggestions, key=len)
        return sorted_suggestions[:max_suggestions]

    @property
    def doc_count(self) -> int:
        """索引文档数 / Number of indexed documents"""
        return len(self._snippets)
