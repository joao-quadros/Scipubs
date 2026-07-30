package com.example.viewmodel

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.api.RecommendationEngine
import com.example.data.Journal
import com.example.data.JournalRepository
import com.example.utils.AppLanguage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.FileOutputStream
import java.text.Normalizer

data class ProcessedJournal(
    val journal: Journal,
    val normTitle: String,
    val normIssn: String,
    val titleWords: List<String>
)

object InternalSearchUtils {
    // Normaliza o texto removendo acentos, cedilhas e convertendo para minúsculas
    fun normalize(text: String): String {
        if (text.isBlank()) return ""
        val normalized = Normalizer.normalize(text, Normalizer.Form.NFD)
        return normalized.replace(Regex("\\p{M}+"), "")
            .lowercase()
            .trim()
    }

    // Tabela de radicais acadêmicos equivalentes entre idiomas (PT, EN, ES)
    private val stemTranslations = mapOf(
        "music" to listOf("music", "musica"),
        "musica" to listOf("music", "musica"),
        "educac" to listOf("educac", "educat"),
        "educat" to listOf("educac", "educat"),
        "cienc" to listOf("cienc", "scien"),
        "scien" to listOf("cienc", "scien"),
        "tecnol" to listOf("tecnol", "technol"),
        "technol" to listOf("tecnol", "technol"),
        "medic" to listOf("medic"),
        "biol" to listOf("biol"),
        "histor" to listOf("histor"),
        "lingui" to listOf("lingui", "linguist"),
        "linguist" to listOf("lingui", "linguist"),
        "engenh" to listOf("engenh", "engin"),
        "engin" to listOf("engenh", "engin"),
        "fisic" to listOf("fisic", "physic"),
        "physic" to listOf("fisic", "physic"),
        "quimic" to listOf("quimic", "chemist"),
        "chemist" to listOf("quimic", "chemist"),
        "geograf" to listOf("geograf", "geograph"),
        "geograph" to listOf("geograf", "geograph"),
        "matemat" to listOf("matemat", "mathemat"),
        "mathemat" to listOf("matemat", "mathemat"),
        "socio" to listOf("socio", "sociol"),
        "sociol" to listOf("socio", "sociol"),
        "filosof" to listOf("filosof", "philosoph"),
        "philosoph" to listOf("filosof", "philosoph"),
        "psicol" to listOf("psicol", "psychol"),
        "psychol" to listOf("psicol", "psychol"),
        "direito" to listOf("direito", "law", "juridic"),
        "law" to listOf("direito", "law", "juridic"),
        "art" to listOf("art", "arte"),
        "arte" to listOf("art", "arte")
    )

    private fun getEquivalentStems(queryWord: String): List<String> {
        val list = mutableListOf(queryWord)
        stemTranslations.forEach { (key, equivalents) ->
            if (queryWord.startsWith(key) || key.startsWith(queryWord)) {
                equivalents.forEach { eq ->
                    if (!list.contains(eq)) list.add(eq)
                }
            }
        }
        return list
    }

    // Busca instantânea usando pré-normalização
    fun matchesFast(pj: ProcessedJournal, normQuery: String, queryWords: List<String>): Boolean {
        if (normQuery.isBlank()) return true
        if (pj.normTitle.contains(normQuery) || pj.normIssn.contains(normQuery)) return true
        if (queryWords.isEmpty()) return true

        return queryWords.all { qWord ->
            val equivalentRadicals = getEquivalentStems(qWord)
            pj.titleWords.any { tWord ->
                equivalentRadicals.any { radical ->
                    tWord.startsWith(radical)
                }
            }
        }
    }
}

object InternalSqliteLoader {
    fun loadJournalsFromAssets(context: Context): List<Journal> {
        val dbFile = context.getDatabasePath("scipubs_imported.db")
        if (dbFile.exists()) {
            dbFile.delete()
        }
        
        dbFile.parentFile?.mkdirs()
        
        try {
            context.assets.open("databases/scipubs.db").use { input ->
                FileOutputStream(dbFile).use { output ->
                    input.copyTo(output)
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
            return emptyList()
        }

        val list = mutableListOf<Journal>()
        try {
            val db = SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY)
            val cursor = db.rawQuery("SELECT * FROM journals", null)
            
            val idIdx = cursor.getColumnIndex("id")
            val titleIdx = cursor.getColumnIndex("title")
            val issnIdx = cursor.getColumnIndex("issn")
            val cnpqIdx = cursor.getColumnIndex("cnpq_area")
            val subareaIdx = cursor.getColumnIndex("subarea")
            val jcrIdx = cursor.getColumnIndex("jcr")
            val quartileIdx = cursor.getColumnIndex("quartile")
            val sjrIdx = cursor.getColumnIndex("sjr")
            val sjrQuartileIdx = cursor.getColumnIndex("sjr_quartile")
            val hIndexIdx = cursor.getColumnIndex("h_index")
            val h5UrlIdx = cursor.getColumnIndex("h5_index_url")
            val indexersIdx = cursor.getColumnIndex("indexers")

            while (cursor.moveToNext()) {
                val journal = Journal(
                    id = if (idIdx >= 0) cursor.getInt(idIdx) else 0,
                    title = if (titleIdx >= 0) cursor.getString(titleIdx) ?: "" else "",
                    issn = if (issnIdx >= 0) cursor.getString(issnIdx) ?: "" else "",
                    cnpqArea = if (cnpqIdx >= 0) cursor.getString(cnpqIdx) ?: "" else "",
                    subarea = if (subareaIdx >= 0) cursor.getString(subareaIdx) ?: "" else "",
                    jcr = if (jcrIdx >= 0) cursor.getString(jcrIdx) ?: "" else "",
                    quartile = if (quartileIdx >= 0) cursor.getString(quartileIdx) ?: "" else "",
                    sjr = if (sjrIdx >= 0) cursor.getString(sjrIdx) ?: "" else "",
                    sjrQuartile = if (sjrQuartileIdx >= 0) cursor.getString(sjrQuartileIdx) ?: "" else "",
                    hIndex = if (hIndexIdx >= 0) cursor.getString(hIndexIdx) ?: "" else "",
                    h5IndexUrl = if (h5UrlIdx >= 0) cursor.getString(h5UrlIdx) ?: "" else "",
                    indexers = if (indexersIdx >= 0) cursor.getString(indexersIdx) ?: "" else ""
                )
                list.add(journal)
            }
            cursor.close()
            db.close()
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return list
    }
}

enum class JournalSortOption(val labelEn: String, val labelEs: String, val labelPt: String) {
    TITLE_ASC("Title (A-Z)", "Título (A-Z)", "Título (A-Z)"),
    TITLE_DESC("Title (Z-A)", "Título (Z-A)", "Título (Z-A)"),
    DATABASE_ASC("Database", "Base de Datos", "Base de Dados"),
    JCR_QUARTILE_ASC("JCR Quartile", "Cuartil JCR", "Quartil JCR"),
    SJR_QUARTILE_ASC("SJR Quartile", "Cuartil SJR", "Quartil SJR");

    fun getLocalizedLabel(lang: AppLanguage): String {
        return when (lang) {
            AppLanguage.EN -> labelEn
            AppLanguage.ES -> labelEs
            AppLanguage.PT -> labelPt
        }
    }
}

enum class AiSortOption(val labelEn: String, val labelEs: String, val labelPt: String) {
    SEMANTIC_SIMILARITY(
        "Semantic Similarity Score",
        "Puntuación de Similitud Semántica",
        "Score de Similaridade Semântica"
    ),
    PROXY_PROBABILITY(
        "Proxy Publication Probability",
        "Probabilidad Proxy de Publicación",
        "Probabilidade Proxy de Publicação"
    );

    fun getLocalizedLabel(lang: AppLanguage): String {
        return when (lang) {
            AppLanguage.EN -> labelEn
            AppLanguage.ES -> labelEs
            AppLanguage.PT -> labelPt
        }
    }
}

data class SearchFilters(
    val query: String = "",
    val cnpq: String = "",
    val indexer: String = "",
    val jcr: String = "",
    val sjr: String = "",
    val sortOption: JournalSortOption = JournalSortOption.TITLE_ASC
)

class MainViewModel(private val repository: JournalRepository) : ViewModel() {

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    private val _selectedCnpqFilter = MutableStateFlow("")
    val selectedCnpqFilter: StateFlow<String> = _selectedCnpqFilter.asStateFlow()

    private val _selectedIndexerFilter = MutableStateFlow("")
    val selectedIndexerFilter: StateFlow<String> = _selectedIndexerFilter.asStateFlow()

    private val _selectedJcrFilter = MutableStateFlow("")
    val selectedJcrFilter: StateFlow<String> = _selectedJcrFilter.asStateFlow()

    private val _selectedSjrFilter = MutableStateFlow("")
    val selectedSjrFilter: StateFlow<String> = _selectedSjrFilter.asStateFlow()

    private val _selectedSortOption = MutableStateFlow(JournalSortOption.TITLE_ASC)
    val selectedSortOption: StateFlow<JournalSortOption> = _selectedSortOption.asStateFlow()

    private val _isLoading = MutableStateFlow(true)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _aiTitle = MutableStateFlow("")
    val aiTitle: StateFlow<String> = _aiTitle.asStateFlow()

    private val _aiAbstract = MutableStateFlow("")
    val aiAbstract: StateFlow<String> = _aiAbstract.asStateFlow()

    private val _aiDatabaseFilter = MutableStateFlow("")
    val aiDatabaseFilter: StateFlow<String> = _aiDatabaseFilter.asStateFlow()

    private val _aiSortOption = MutableStateFlow(AiSortOption.SEMANTIC_SIMILARITY)
    val aiSortOption: StateFlow<AiSortOption> = _aiSortOption.asStateFlow()

    private val _aiResult = MutableStateFlow("")
    val aiResult: StateFlow<String> = _aiResult.asStateFlow()

    private val _aiRecommendedJournals = MutableStateFlow<List<Journal>>(emptyList())
    val aiRecommendedJournals: StateFlow<List<Journal>> = _aiRecommendedJournals.asStateFlow()

    private val _aiLoading = MutableStateFlow(false)
    val aiLoading: StateFlow<Boolean> = _aiLoading.asStateFlow()

    val allJournals: StateFlow<List<Journal>> = repository.allJournals
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.Eagerly,
            initialValue = emptyList()
        )

    // Índice pré-normalizado na memória para busca instantânea em < 3ms
    private val processedJournals: StateFlow<List<ProcessedJournal>> = allJournals
        .map { list ->
            list.map { journal ->
                val normTitle = InternalSearchUtils.normalize(journal.title)
                val normIssn = InternalSearchUtils.normalize(journal.issn)
                val words = normTitle.split(Regex("[^a-z0-9]+")).filter { it.isNotBlank() }
                ProcessedJournal(journal, normTitle, normIssn, words)
            }
        }
        .flowOn(Dispatchers.Default)
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.Eagerly,
            initialValue = emptyList()
        )

    private val searchFilters: Flow<SearchFilters> = combine(
        _searchQuery,
        _selectedCnpqFilter,
        _selectedIndexerFilter,
        _selectedJcrFilter,
        _selectedSjrFilter,
        _selectedSortOption
    ) { args: Array<Any?> ->
        SearchFilters(
            query = args[0] as String,
            cnpq = args[1] as String,
            indexer = args[2] as String,
            jcr = args[3] as String,
            sjr = args[4] as String,
            sortOption = args[5] as JournalSortOption
        )
    }

    @OptIn(FlowPreview::class)
    val filteredJournals: StateFlow<List<Journal>> = combine(
        processedJournals,
        searchFilters.debounce(150L) // Aguarda 150ms após digitar para evitar churn de CPU
    ) { pJournals, filters ->
        if (pJournals.isEmpty()) return@combine emptyList()

        if (filters.query.isBlank() && filters.cnpq.isBlank() && filters.indexer.isBlank() && filters.jcr.isBlank() && filters.sjr.isBlank() && filters.sortOption == JournalSortOption.TITLE_ASC) {
            return@combine pJournals.map { it.journal }
        }

        val normQuery = InternalSearchUtils.normalize(filters.query)
        val queryWords = normQuery.split(Regex("[^a-z0-9]+")).filter { it.isNotBlank() }

        var list = pJournals.filter { pj ->
            val j = pj.journal
            InternalSearchUtils.matchesFast(pj, normQuery, queryWords) &&
            (filters.cnpq.isBlank() || filters.cnpq == "All" || filters.cnpq == "Todas" || j.cnpqArea.equals(filters.cnpq, ignoreCase = true)) &&
            (filters.indexer.isBlank() || filters.indexer == "All" || filters.indexer == "Todas" || j.indexers.contains(filters.indexer, ignoreCase = true)) &&
            (filters.jcr.isBlank() || filters.jcr == "All" || filters.jcr == "Todas" || j.quartile.equals(filters.jcr, ignoreCase = true)) &&
            (filters.sjr.isBlank() || filters.sjr == "All" || filters.sjr == "Todas" || j.sjrQuartile.equals(filters.sjr, ignoreCase = true))
        }.map { it.journal }

        when (filters.sortOption) {
            JournalSortOption.TITLE_ASC -> list = list.sortedBy { it.title }
            JournalSortOption.TITLE_DESC -> list = list.sortedByDescending { it.title }
            JournalSortOption.DATABASE_ASC -> list = list.sortedBy { it.indexers }
            JournalSortOption.JCR_QUARTILE_ASC -> list = list.sortedBy { it.quartile }
            JournalSortOption.SJR_QUARTILE_ASC -> list = list.sortedBy { it.sjrQuartile }
        }

        list
    }
    .flowOn(Dispatchers.Default)
    .stateIn(
        scope = viewModelScope,
        started = SharingStarted.Eagerly,
        initialValue = emptyList()
    )

    fun initializeMockData(context: Context) {
        viewModelScope.launch(Dispatchers.IO) {
            try {
                if (allJournals.value.isEmpty()) {
                    _isLoading.value = true
                    val journalsFromSqlite = InternalSqliteLoader.loadJournalsFromAssets(context)
                    if (journalsFromSqlite.isNotEmpty()) {
                        repository.insertInBatches(journalsFromSqlite)
                    }
                    _isLoading.value = false
                } else {
                    _isLoading.value = false
                }
            } catch (e: Exception) {
                _isLoading.value = true
                val journalsFromSqlite = InternalSqliteLoader.loadJournalsFromAssets(context)
                if (journalsFromSqlite.isNotEmpty()) {
                    repository.insertInBatches(journalsFromSqlite)
                }
                _isLoading.value = false
            }
        }
    }

    fun onSearchQueryChange(newQuery: String) { _searchQuery.value = newQuery }
    fun onCnpqFilterChange(filter: String) { _selectedCnpqFilter.value = filter }
    fun onIndexerFilterChange(filter: String) { _selectedIndexerFilter.value = filter }
    fun onJcrFilterChange(filter: String) { _selectedJcrFilter.value = filter }
    fun onSjrFilterChange(filter: String) { _selectedSjrFilter.value = filter }
    fun onSortOptionChange(option: JournalSortOption) { _selectedSortOption.value = option }

    fun onAiTitleChange(title: String) { _aiTitle.value = title }
    fun onAiAbstractChange(abstractText: String) { _aiAbstract.value = abstractText }
    fun onAiDatabaseFilterChange(filter: String) { _aiDatabaseFilter.value = filter }
    fun onAiSortOptionChange(option: AiSortOption) { _aiSortOption.value = option }

    fun getRecommendations() {
        viewModelScope.launch {
            _aiLoading.value = true
            val (opinion, recommendations) = withContext(Dispatchers.Default) {
                RecommendationEngine.recommend(
                    journals = allJournals.value,
                    title = _aiTitle.value,
                    abstractText = _aiAbstract.value,
                    filterDatabase = _aiDatabaseFilter.value,
                    aiSortOption = _aiSortOption.value
                )
            }
            _aiResult.value = opinion
            _aiRecommendedJournals.value = recommendations
            _aiLoading.value = false
        }
    }
}