package com.example.api

import com.example.data.Journal
import com.example.viewmodel.AiSortOption
import kotlin.math.sqrt

object RecommendationEngine {

    data class ScoredJournal(
        val journal: Journal,
        val similarityScore: Double,
        val proxyScore: Double
    )

    fun recommend(
        journals: List<Journal>,
        title: String,
        abstractText: String,
        filterDatabase: String,
        aiSortOption: AiSortOption
    ): Pair<String, List<Journal>> {
        val query = "$title $abstractText".lowercase().trim()
        if (query.isBlank()) {
            return Pair("Por favor, insira o título e o resumo do seu manuscrito para obter recomendações científicas personalizadas.", emptyList())
        }

        val queryTokens = tokenize(query)
        if (queryTokens.isEmpty()) {
            return Pair("Texto muito curto para análise vetorial semântica.", emptyList())
        }

        var candidateList = journals
        if (filterDatabase.isNotBlank() && filterDatabase != "All" && filterDatabase != "Todas") {
            candidateList = candidateList.filter { it.indexers.contains(filterDatabase, ignoreCase = true) }
        }

        val scoredJournals = candidateList.map { journal ->
            val journalText = "${journal.title} ${journal.cnpqArea} ${journal.subarea} ${journal.indexers}".lowercase()
            val journalTokens = tokenize(journalText)

            val simScore = calculateCosineSimilarity(queryTokens, journalTokens)
            
            val jcrVal = journal.jcr.toDoubleOrNull() ?: 0.0
            val sjrVal = journal.sjr.toDoubleOrNull() ?: 0.0

            val proxyScore = (simScore * 0.60) + ((jcrVal / 50.0).coerceAtMost(0.20)) + ((sjrVal / 20.0).coerceAtMost(0.20))

            ScoredJournal(journal, simScore, proxyScore)
        }

        val sortedList = when (aiSortOption) {
            AiSortOption.SEMANTIC_SIMILARITY -> scoredJournals.sortedByDescending { it.similarityScore }
            AiSortOption.PROXY_PROBABILITY -> scoredJournals.sortedByDescending { it.proxyScore }
        }.map { it.journal }

        val topRecommendations = sortedList.take(20)

        val analysisOpinion = buildString {
            append("Análise semântica concluída com sucesso para ")
            append(topRecommendations.size)
            append(" periódicos. ")
            if (aiSortOption == AiSortOption.SEMANTIC_SIMILARITY) {
                append("Resultados ordenados por Score de Similaridade Semântica vetorial.")
            } else {
                append("Resultados ordenados por Probabilidade Proxy de Publicação (Aderência Semântica + Fator de Impacto JCR/SJR).")
            }
        }

        return Pair(analysisOpinion, topRecommendations)
    }

    private fun tokenize(text: String): Map<String, Int> {
        val stopWords = setOf(
            "a", "an", "the", "and", "or", "but", "about", "above", "across", "after", "against", "along",
            "among", "around", "at", "before", "behind", "below", "beneath", "beside", "between", "beyond",
            "by", "down", "during", "except", "for", "from", "in", "inside", "into", "near", "of", "off",
            "on", "onto", "out", "outside", "over", "past", "through", "throughout", "to", "toward", "under",
            "underneath", "until", "up", "upon", "with", "within", "without", "o", "a", "os", "as", "um",
            "uma", "uns", "umas", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "por",
            "pelo", "pela", "pelos", "pelas", "com", "para", "que", "se", "ou", "e"
        )
        return text.split(Regex("\\W+"))
            .map { it.lowercase() }
            .filter { it.length > 2 && !stopWords.contains(it) }
            .groupingBy { it }
            .eachCount()
    }

    private fun calculateCosineSimilarity(vec1: Map<String, Int>, vec2: Map<String, Int>): Double {
        val intersection = vec1.keys.intersect(vec2.keys)
        if (intersection.isEmpty()) return 0.0

        var dotProduct = 0.0
        for (key in intersection) {
            dotProduct += vec1.getValue(key) * vec2.getValue(key)
        }

        val norm1 = sqrt(vec1.values.sumOf { (it * it).toDouble() })
        val norm2 = sqrt(vec2.values.sumOf { (it * it).toDouble() })

        return if (norm1 > 0.0 && norm2 > 0.0) dotProduct / (norm1 * norm2) else 0.0
    }
}