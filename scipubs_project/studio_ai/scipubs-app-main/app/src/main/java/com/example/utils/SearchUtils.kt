package com.example.utils

import com.example.data.Journal
import java.text.Normalizer
import java.util.regex.Pattern

enum class AppLanguage {
    EN, ES, PT
}

enum class CnpqMajorArea(
    val code: String,
    val namePt: String,
    val nameEn: String,
    val nameEs: String
) {
    EXATAS("1000000X", "Ciências Exatas e da Terra", "Exact and Earth Sciences", "Ciencias Exactas y de la Tierra"),
    BIOLOGICAS("2000000X", "Ciências Biológicas", "Biological Sciences", "Ciencias Biológicas"),
    ENGENHARIAS("3000000X", "Engenharias", "Engineering", "Ingenierías"),
    SAUDE("4000000X", "Ciências da Saúde", "Health Sciences", "Ciencias de la Salud"),
    AGRARIAS("5000000X", "Ciências Agrárias", "Agricultural Sciences", "Ciencias Agrarias"),
    SOCIAIS_APLICADAS("6000000X", "Ciências Sociais Aplicadas", "Applied Social Sciences", "Ciencias Sociales Aplicadas"),
    HUMANAS("7000000X", "Ciências Humanas", "Human Sciences", "Ciencias Humanas"),
    ARTES("8000000X", "Linguística, Letras e Artes", "Linguistics, Letters and Arts", "Lingüística, Letras y Artes"),
    OUTRAS("9000000X", "Outras / Não Classificado", "Others / Unclassified", "Otras / No Clasificado");

    fun localizedName(lang: AppLanguage): String {
        return when (lang) {
            AppLanguage.PT -> namePt
            AppLanguage.EN -> nameEn
            AppLanguage.ES -> nameEs
        }
    }

    companion object {
        fun fromText(text: String): CnpqMajorArea {
            val norm = stripAccents(text).lowercase()
            return when {
                norm.contains("musica") || norm.contains("music") || norm.contains("artes") || norm.contains("letras") || norm.contains("linguist") || norm.contains("literature") -> ARTES
                norm.contains("exatas") || norm.contains("exact") || norm.contains("comput") || norm.contains("math") || norm.contains("fisica") || norm.contains("quimica") -> EXATAS
                norm.contains("saude") || norm.contains("health") || norm.contains("medicin") || norm.contains("salud") || norm.contains("pharm") -> SAUDE
                norm.contains("biolog") || norm.contains("cell") || norm.contains("biomed") -> BIOLOGICAS
                norm.contains("engenh") || norm.contains("engineer") -> ENGENHARIAS
                norm.contains("agrar") || norm.contains("agronom") -> AGRARIAS
                norm.contains("sociais aplic") || norm.contains("applied social") || norm.contains("direito") || norm.contains("law") || norm.contains("economy") || norm.contains("administra") -> SOCIAIS_APLICADAS
                norm.contains("human") || norm.contains("educa") || norm.contains("psicolog") || norm.contains("psychology") -> HUMANAS
                else -> OUTRAS
            }
        }
    }
}

fun stripAccents(input: String): String {
    if (input.isBlank()) return ""
    val normalized = Normalizer.normalize(input, Normalizer.Form.NFD)
    return Pattern.compile("\\p{InCombiningDiacriticalMarks}+").matcher(normalized).replaceAll("").lowercase().trim()
}

// Expansão Multilíngue de Termos Acadêmicos
fun expandToken(token: String): List<String> {
    val norm = stripAccents(token).lowercase()
    return when {
        norm.startsWith("psicolog") || norm.startsWith("psycholog") -> listOf("psicolog", "psycholog", "psicologia", "psychology", "psychological")
        norm.startsWith("music") -> listOf("music", "musica", "musical")
        norm.startsWith("educa") || norm.startsWith("educat") -> listOf("educa", "education", "educational", "educacion")
        norm.startsWith("literat") -> listOf("literat", "literatura", "literature")
        norm.startsWith("arte") || norm.startsWith("art") -> listOf("art", "arte", "arts")
        norm.startsWith("saude") || norm.startsWith("health") -> listOf("saude", "health")
        norm.startsWith("medicin") || norm.startsWith("medic") -> listOf("medicin", "medical", "medicine")
        norm.startsWith("fisic") || norm.startsWith("physic") -> listOf("fisic", "physic", "physics")
        norm.startsWith("quimic") || norm.startsWith("chemic") -> listOf("quimic", "chem", "chemistry")
        norm.startsWith("biolog") -> listOf("biolog", "biology", "biological")
        else -> listOf(norm)
    }
}

fun matchesTraditionalSearch(
    journal: Journal,
    query: String,
    cnpqFilter: String = "",
    indexerFilter: String = "",
    jcrFilter: String = "",
    sjrFilter: String = ""
): Boolean {
    // 1. Filtro por Quartil JCR
    if (jcrFilter.isNotBlank() && jcrFilter != "Todos" && jcrFilter != "All") {
        if (!journal.quartile.equals(jcrFilter, ignoreCase = true)) return false
    }

    // 2. Filtro por Quartil SJR
    if (sjrFilter.isNotBlank() && sjrFilter != "Todos" && sjrFilter != "All") {
        if (!journal.sjrQuartile.equals(sjrFilter, ignoreCase = true)) return false
    }

    // 3. Filtro por Indexadores
    if (indexerFilter.isNotBlank() && indexerFilter != "Todas" && indexerFilter != "All") {
        if (!journal.indexers.contains(indexerFilter, ignoreCase = true)) return false
    }

    // 4. Filtro por Grande Área CNPq
    val normCnpqFilter = stripAccents(cnpqFilter).lowercase()
    if (normCnpqFilter.isNotBlank() && normCnpqFilter != "todas" && normCnpqFilter != "all" && !normCnpqFilter.startsWith("todas as areas")) {
        val filterNorm = normCnpqFilter.substringBefore(" (")
        val journalArea = stripAccents("${journal.cnpqArea} ${journal.subarea}").lowercase()
        if (!journalArea.contains(filterNorm)) return false
    }

    if (query.isBlank()) return true

    // 🟢 RESTRITO EXCLUSIVAMENTE AO TÍTULO DA REVISTA E AO ISSN
    val targetNormalized = stripAccents("${journal.title} ${journal.issn}").lowercase()

    val qNormalized = stripAccents(query).trim().lowercase()

    val queryTokens = qNormalized.split("\\s+".toRegex()).filter { it.isNotBlank() }
    
    return queryTokens.all { token ->
        val variants = expandToken(token)
        variants.any { variant -> targetNormalized.contains(variant) }
    }
}