package com.example

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Adjust
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.CardMembership
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Email
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.OpenInNew
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.room.Room
import com.example.data.AppDatabase
import com.example.data.Journal
import com.example.data.JournalRepository
import com.example.utils.AppLanguage
import com.example.viewmodel.AiSortOption
import com.example.viewmodel.JournalSortOption
import com.example.viewmodel.MainViewModel
import kotlinx.coroutines.launch
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

val DarkBg = Color(0xFF040A18)
val DarkCard = Color(0xFF0B132B)
val DarkInputBg = Color(0xFF131D30)
val CoralRed = Color(0xFFDC2626)
val EmeraldGreen = Color(0xFF059669)
val RoyalBlue = Color(0xFF2563EB)
val GoldYellow = Color(0xFFFFCC00)
val TextMuted = Color(0xFF94A3B8)
val LogoDarkBlue = Color(0xFF0F1E3D)
val SidebarBgColor = Color(0xFF04081C)
val SidebarButtonColor = Color(0xFFF2F0EF)

val broadAreasPT = listOf("Todas", "Ciências Exatas e da Terra", "Ciências Biológicas", "Engenharias", "Ciências da Saúde", "Ciências Agrárias", "Ciências Sociais Aplicadas", "Ciências Humanas", "Linguística, Letras e Artes")
val broadAreasEN = listOf("All", "Exact and Earth Sciences", "Biological Sciences", "Engineering", "Health Sciences", "Agricultural Sciences", "Applied Social Sciences", "Human Sciences", "Linguistics, Letters and Arts")
val broadAreasES = listOf("Todas", "Ciencias Exactas y de la Tierra", "Ciencias Biológicas", "Ingenierías", "Ciencias de la Salud", "Ciencias Agrarias", "Ciencias Sociales Aplicadas", "Ciencias Humanas", "Lingüística, Letras y Artes")

// 🟢 GERENCIADOR DE INSCRITOS VIP (COLETA E ARMAZENAMENTO NO PROJETO)
object SubscriberManager {
    fun saveSubscriber(context: Context, name: String, email: String) {
        try {
            val file = File(context.filesDir, "subscribers.csv")
            val dateStr = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date())
            val line = "\"$dateStr\",\"$name\",\"$email\"\n"
            file.appendText(line)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}

// 🟢 GERENCIADOR DO CONTADOR DE VISITAS PERSISTENTE (NUNCA VOLTA AO ZERO, INVISÍVEL AO USUÁRIO COMUM)
object VisitCounterManager {
    private const val PREFS_NAME = "scipubs_visit_prefs"
    private const val KEY_VISIT_COUNT = "total_visit_count"
    private const val INITIAL_BASE_COUNT = 14820L

    fun incrementAndGet(context: Context): Long {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        var count = prefs.getLong(KEY_VISIT_COUNT, INITIAL_BASE_COUNT)
        count++
        prefs.edit().putLong(KEY_VISIT_COUNT, count).apply()
        return count
    }

    fun getCount(context: Context): Long {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getLong(KEY_VISIT_COUNT, INITIAL_BASE_COUNT)
    }
}

data class AppStrings(
    val tabTraditional: String,
    val tabAi: String,
    val searchPlaceholder: String,
    val filtersTitle: String,
    val broadAreaLabel: String,
    val databaseLabel: String,
    val jcrQuartileLabel: String,
    val sjrQuartileLabel: String,
    val sortLabel: String,
    val allLabel: String,
    val loadingLabel: String,
    val noResultsLabel: String,
    val showingCountLabel: String,
    val aiTitle: String,
    val aiDescription: String,
    val manuscriptTitleLabel: String,
    val abstractLabel: String,
    val analyzeBtn: String,
    val analyzingBtn: String,
    val aiOpinionHeader: String,
    val aiRecommendedHeader: String,
    val secIndexers: String,
    val secRepositories: String,
    val secAi: String,
    val secGov: String,
    val secInst: String,
    val metadataTitle: String,
    val systemStatus: String,
    val baseVersion: String,
    val cnpqStandard: String,
    val copyrightOwner: String,
    val universityName: String,
    val visitJournalWebsite: String,
    val accessH5Index: String,
    val contactUs: String,
    val donation: String,
    val subscribe: String,
    val broadAreas: List<String>
)

val stringsEN = AppStrings(
    tabTraditional = "Search Journal",
    tabAi = "AI Recommender",
    searchPlaceholder = "Search by Journal Title or ISSN...",
    filtersTitle = "🎛️ Filters & Sorting",
    broadAreaLabel = "Broad Area:",
    databaseLabel = "Database:",
    jcrQuartileLabel = "JCR Quartile:",
    sjrQuartileLabel = "SJR Quartile:",
    sortLabel = "Sort Results by:",
    allLabel = "All",
    loadingLabel = "Loading database...",
    noResultsLabel = "No journals found with applied filters.",
    showingCountLabel = "Displaying journals:",
    aiTitle = "🤖 Smart AI Journal Recommender",
    aiDescription = "Paste your paper title and abstract to discover recommended target journals ranked by scientific adherence.",
    manuscriptTitleLabel = "Manuscript Title",
    abstractLabel = "Abstract",
    analyzeBtn = "Analyze Paper with AI",
    analyzingBtn = "Analyzing Paper...",
    aiOpinionHeader = "🏆 AI Recommender Opinion:",
    aiRecommendedHeader = "🏆 Recommended Journals:",
    secIndexers = "DATABASES",
    secRepositories = "REPOSITORIES",
    secAi = "ACADEMIC AI",
    secGov = "GOVERNMENT PORTALS",
    secInst = "INSTITUTIONAL INFO",
    metadataTitle = "METADATA",
    systemStatus = "● System: Operational",
    baseVersion = "Base Version: 2026.1",
    cnpqStandard = "CNPq Standard: Active",
    copyrightOwner = "© 2026 João F. Soares-Quadros Jr.",
    universityName = "Federal University of Ouro Preto\nMinas Gerais, Brazil. All rights reserved.",
    visitJournalWebsite = "🌐 Official Journal Website",
    accessH5Index = "Access H5-Index",
    contactUs = "Contact Us",
    donation = "Donate",
    subscribe = "Subscribe",
    broadAreas = broadAreasEN
)

val stringsES = AppStrings(
    tabTraditional = "Buscar Revista",
    tabAi = "Recomendador IA",
    searchPlaceholder = "Buscar por Título de Revista o ISSN...",
    filtersTitle = "🎛️ Filtros y Ordenación",
    broadAreaLabel = "Gran Área:",
    databaseLabel = "Base de Datos:",
    jcrQuartileLabel = "Cuartil JCR:",
    sjrQuartileLabel = "Cuartil SJR:",
    sortLabel = "Ordenar Resultados por:",
    allLabel = "Todas",
    loadingLabel = "Cargando base de datos...",
    noResultsLabel = "No se encontraron revistas con los filtros aplicados.",
    showingCountLabel = "Mostrando revistas:",
    aiTitle = "🤖 Recomendador Inteligente de Revistas IA",
    aiDescription = "Pegue el título y resumen de su artículo para recibir recomendaciones de revistas ordenadas por adherencia científica.",
    manuscriptTitleLabel = "Título del Manuscrito",
    abstractLabel = "Resumen / Abstract",
    analyzeBtn = "Analizar Artículo con IA",
    analyzingBtn = "Analizando Artículo...",
    aiOpinionHeader = "🏆 Dictamen del Recomendador IA:",
    aiRecommendedHeader = "🏆 Revistas Recomendadas:",
    secIndexers = "BASES DE DATOS",
    secRepositories = "REPOSITORIOS",
    secAi = "IA ACADÉMICA",
    secGov = "SITIOS GUBERNAMENTALES",
    secInst = "INFORMACIÓN INSTITUCIONAL",
    metadataTitle = "METADATOS",
    systemStatus = "● Sistema: Operativo",
    baseVersion = "Versión Base: 2026.1",
    cnpqStandard = "Estándar CNPq: Activo",
    copyrightOwner = "© 2026 João F. Soares-Quadros Jr.",
    universityName = "Universidad Federal de Ouro Preto\nMinas Gerais, Brasil. Todos los derechos reservados.",
    visitJournalWebsite = "🌐 Sitio Oficial de la Revista",
    accessH5Index = "Acceda al Índice H5",
    contactUs = "Contáctenos",
    donation = "Donación",
    subscribe = "Suscribirse",
    broadAreas = broadAreasES
)

val stringsPT = AppStrings(
    tabTraditional = "Pesquisar Periódico",
    tabAi = "Recomendador IA",
    searchPlaceholder = "Buscar por Título da Revista ou ISSN...",
    filtersTitle = "🎛️ Filtros & Ordenação",
    broadAreaLabel = "Grande Área:",
    databaseLabel = "Base de Dados:",
    jcrQuartileLabel = "Quartil JCR:",
    sjrQuartileLabel = "SJR Quartile:",
    sortLabel = "Ordenar Resultados por:",
    allLabel = "Todas",
    loadingLabel = "Carregando base de dados...",
    noResultsLabel = "Nenhum periódico encontrado com os filtros aplicados.",
    showingCountLabel = "Exibindo periódicos:",
    aiTitle = "🤖 Recomendador de Periódicos por IA",
    aiDescription = "Cole o título e resumo do seu artigo para receber recomendações ranqueadas por aderência científica.",
    manuscriptTitleLabel = "Título do Manuscrito",
    abstractLabel = "Resumo / Abstract",
    analyzeBtn = "Analisar Artigo com IA",
    analyzingBtn = "Analisando Artigo...",
    aiOpinionHeader = "🏆 Parecer do Recomendador IA:",
    aiRecommendedHeader = "🏆 Periódicos Recomendados:",
    secIndexers = "BASES DADOS",
    secRepositories = "REPOSITÓRIOS",
    secAi = "IA ACADÊMICA",
    secGov = "SITES GOVERNAMENTAIS",
    secInst = "INFORMAÇÕES INSTITUCIONAIS",
    metadataTitle = "METADADOS",
    systemStatus = "● Sistema: Operacional",
    baseVersion = "Versão Base: 2026.1",
    cnpqStandard = "Padrão CNPq: Ativo",
    copyrightOwner = "© 2026 João F. Soares-Quadros Jr.",
    universityName = "Universidade Federal de Ouro Preto\nMinas Gerais, Brasil. Todos os direitos reservados.",
    visitJournalWebsite = "🌐 Site Oficial do Periódico",
    accessH5Index = "Acesse o Índice H5",
    contactUs = "Fale Conosco",
    donation = "Doação",
    subscribe = "Inscrever-se",
    broadAreas = broadAreasPT
)

fun getAppStrings(lang: AppLanguage): AppStrings {
    return when (lang) {
        AppLanguage.EN -> stringsEN
        AppLanguage.ES -> stringsES
        AppLanguage.PT -> stringsPT
    }
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val database = Room.databaseBuilder(
            applicationContext,
            AppDatabase::class.java,
            "scipubs-main-db"
        ).fallbackToDestructiveMigration().build()
        
        val repository = JournalRepository(database.journalDao())
        
        enableEdgeToEdge()
        setContent {
            val viewModel: MainViewModel = viewModel(factory = object : ViewModelProvider.Factory {
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return MainViewModel(repository) as T
                }
            })
            
            SciPubsApp(viewModel)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SciPubsApp(viewModel: MainViewModel) {
    val context = LocalContext.current

    // Incrementar contador de visitas contínuo na memória persistente
    val currentVisitCount = remember { mutableLongStateOf(0L) }

    LaunchedEffect(Unit) {
        viewModel.initializeMockData(context.applicationContext)
        currentVisitCount.longValue = VisitCounterManager.incrementAndGet(context.applicationContext)
    }

    val journals by viewModel.filteredJournals.collectAsState(initial = emptyList())
    val isLoadingDb by viewModel.isLoading.collectAsState(initial = true)
    val searchQuery by viewModel.searchQuery.collectAsState()

    val selectedCnpqFilter by viewModel.selectedCnpqFilter.collectAsState()
    val selectedIndexerFilter by viewModel.selectedIndexerFilter.collectAsState()
    val selectedJcrFilter by viewModel.selectedJcrFilter.collectAsState()
    val selectedSjrFilter by viewModel.selectedSjrFilter.collectAsState()
    val selectedSortOption by viewModel.selectedSortOption.collectAsState()

    val aiTitle by viewModel.aiTitle.collectAsState()
    val aiAbstract by viewModel.aiAbstract.collectAsState()
    val aiDatabaseFilter by viewModel.aiDatabaseFilter.collectAsState()
    val aiSortOption by viewModel.aiSortOption.collectAsState()
    val aiResult by viewModel.aiResult.collectAsState()
    val aiRecommendedJournals by viewModel.aiRecommendedJournals.collectAsState()
    val aiLoading by viewModel.aiLoading.collectAsState()

    var currentLanguage by remember { mutableStateOf(AppLanguage.EN) }
    val strings = getAppStrings(currentLanguage)

    var activeTab by remember { mutableIntStateOf(0) }
    var showSubscribeDialog by remember { mutableStateOf(false) }

    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    val scope = rememberCoroutineScope()

    // 🟢 MODAL POP-UP "INSCREVER-SE" NA COMUNIDADE VIP
    if (showSubscribeDialog) {
        var fullName by remember { mutableStateOf("") }
        var email by remember { mutableStateOf("") }
        var isSubmitted by remember { mutableStateOf(false) }
        var errorMessage by remember { mutableStateOf("") }

        AlertDialog(
            onDismissRequest = { showSubscribeDialog = false },
            containerColor = Color(0xFF0F1E3D),
            titleContentColor = GoldYellow,
            textContentColor = Color.White,
            title = {
                Text(
                    text = "Junte-se à nossa Comunidade VIP! 🚀",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(
                        text = "Deixe seu e-mail para receber dicas de publicação e atualizações da plataforma. Sem spam, prometemos.",
                        fontSize = 12.sp,
                        color = TextMuted
                    )

                    if (isSubmitted) {
                        Surface(
                            color = EmeraldGreen,
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.fillMaxWidth().padding(top = 8.dp)
                        ) {
                            Text(
                                text = "✅ Inscrição realizada com sucesso! Bem-vindo(a) à Comunidade VIP.",
                                color = Color.White,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(12.dp)
                            )
                        }
                    } else {
                        OutlinedTextField(
                            value = fullName,
                            onValueChange = { fullName = it },
                            label = { Text("Nome completo", color = TextMuted) },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                            colors = OutlinedTextFieldDefaults.colors(
                                unfocusedContainerColor = DarkInputBg,
                                focusedContainerColor = DarkInputBg,
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White
                            ),
                            shape = RoundedCornerShape(8.dp)
                        )

                        OutlinedTextField(
                            value = email,
                            onValueChange = { email = it },
                            label = { Text("E-mail", color = TextMuted) },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true,
                            colors = OutlinedTextFieldDefaults.colors(
                                unfocusedContainerColor = DarkInputBg,
                                focusedContainerColor = DarkInputBg,
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White
                            ),
                            shape = RoundedCornerShape(8.dp)
                        )

                        if (errorMessage.isNotEmpty()) {
                            Text(errorMessage, color = CoralRed, fontSize = 11.sp)
                        }
                    }
                }
            },
            confirmButton = {
                if (!isSubmitted) {
                    Button(
                        onClick = {
                            if (fullName.isBlank() || email.isBlank() || !email.contains("@")) {
                                errorMessage = "Por favor, preencha o nome completo e um e-mail válido."
                            } else {
                                SubscriberManager.saveSubscriber(context, fullName.trim(), email.trim())
                                isSubmitted = true
                                errorMessage = ""
                            }
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = RoyalBlue)
                    ) {
                        Text("Confirmar Inscrição", fontWeight = FontWeight.Bold)
                    }
                } else {
                    Button(
                        onClick = { showSubscribeDialog = false },
                        colors = ButtonDefaults.buttonColors(containerColor = CoralRed)
                    ) {
                        Text("Fechar", fontWeight = FontWeight.Bold)
                    }
                }
            },
            dismissButton = {
                if (!isSubmitted) {
                    TextButton(onClick = { showSubscribeDialog = false }) {
                        Text("Cancelar", color = TextMuted)
                    }
                }
            }
        )
    }

    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {
            ModalDrawerSheet(
                drawerContainerColor = SidebarBgColor,
                drawerContentColor = Color.White,
                modifier = Modifier.width(300.dp)
            ) {
                SidebarContent(
                    strings = strings,
                    onClose = { scope.launch { drawerState.close() } },
                    context = context,
                    onOpenSubscribeDialog = { showSubscribeDialog = true },
                    visitCount = currentVisitCount.longValue
                )
            }
        }
    ) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = DarkBg
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .statusBarsPadding()
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(3.dp)
                        .background(CoralRed)
                )

                // BARRA SUPERIOR
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Surface(
                        shape = RoundedCornerShape(8.dp),
                        color = Color.White,
                        modifier = Modifier
                            .size(38.dp)
                            .clickable { scope.launch { drawerState.open() } }
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(Icons.Default.Menu, contentDescription = "Menu", tint = Color.Black, modifier = Modifier.size(20.dp))
                        }
                    }

                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        listOf(AppLanguage.EN to "EN", AppLanguage.ES to "ES", AppLanguage.PT to "PT").forEach { (lang, code) ->
                            val isSelected = currentLanguage == lang
                            Surface(
                                shape = RoundedCornerShape(6.dp),
                                color = if (isSelected) CoralRed else DarkInputBg,
                                modifier = Modifier.clickable { currentLanguage = lang }
                            ) {
                                Text(
                                    text = code,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                )
                            }
                        }
                    }
                }

                // BANNER SUPERIOR 16:9
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .aspectRatio(16f / 9f)
                        .padding(horizontal = 16.dp, vertical = 4.dp)
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color(0xFF081228))
                ) {
                    Image(
                        painter = painterResource(id = R.drawable.logo_capa),
                        contentDescription = "SciPubs Banner",
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Fit
                    )
                }

                // LINHA DE BOTÕES DESTACADOS NA TELA PRINCIPAL (DOAÇÃO E INSCREVER-SE)
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 6.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    // 1. Doação -> Abre Buy Me A Coffee (https://buymeacoffee.com/scipubs)
                    Surface(
                        color = EmeraldGreen,
                        shape = RoundedCornerShape(10.dp),
                        modifier = Modifier
                            .weight(1f)
                            .clickable {
                                try {
                                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://buymeacoffee.com/scipubs"))
                                    context.startActivity(intent)
                                } catch (e: Exception) {
                                    e.printStackTrace()
                                }
                            }
                    ) {
                        Row(
                            modifier = Modifier.padding(vertical = 10.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.Center
                        ) {
                            Icon(Icons.Default.Favorite, contentDescription = null, tint = Color.White, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(strings.donation, color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        }
                    }

                    // 2. Inscrever-se -> Abre Pop-up Modal VIP
                    Surface(
                        color = RoyalBlue,
                        shape = RoundedCornerShape(10.dp),
                        modifier = Modifier
                            .weight(1f)
                            .clickable { showSubscribeDialog = true }
                    ) {
                        Row(
                            modifier = Modifier.padding(vertical = 10.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.Center
                        ) {
                            Icon(Icons.Default.CardMembership, contentDescription = null, tint = Color.White, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(strings.subscribe, color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                // ABAS PRINCIPAIS MULTILÍNGUES
                Row(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .clickable { activeTab = 0 }
                            .padding(vertical = 10.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Search, contentDescription = null, tint = CoralRed, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(strings.tabTraditional, fontSize = 13.sp, fontWeight = FontWeight.Bold, color = if (activeTab == 0) CoralRed else TextMuted)
                        }
                        Spacer(modifier = Modifier.height(6.dp))
                        Box(modifier = Modifier.fillMaxWidth(0.8f).height(2.dp).background(if (activeTab == 0) CoralRed else Color.Transparent))
                    }

                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .clickable { activeTab = 1 }
                            .padding(vertical = 10.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.AutoAwesome, contentDescription = null, tint = CoralRed, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(strings.tabAi, fontSize = 13.sp, fontWeight = FontWeight.Bold, color = if (activeTab == 1) CoralRed else TextMuted)
                        }
                        Spacer(modifier = Modifier.height(6.dp))
                        Box(modifier = Modifier.fillMaxWidth(0.8f).height(2.dp).background(if (activeTab == 1) CoralRed else Color.Transparent))
                    }
                }

                HorizontalDivider(color = Color(0xFF1E2A42), thickness = 1.dp)

                if (activeTab == 0) {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(16.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        item {
                            OutlinedTextField(
                                value = searchQuery,
                                onValueChange = viewModel::onSearchQueryChange,
                                modifier = Modifier.fillMaxWidth(),
                                placeholder = { Text(strings.searchPlaceholder, color = TextMuted, fontSize = 12.sp) },
                                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null, tint = TextMuted) },
                                shape = RoundedCornerShape(10.dp),
                                colors = OutlinedTextFieldDefaults.colors(
                                    unfocusedContainerColor = DarkInputBg,
                                    focusedContainerColor = DarkInputBg,
                                    focusedTextColor = Color.White,
                                    unfocusedTextColor = Color.White
                                ),
                                singleLine = true
                            )
                        }

                        item {
                            Surface(
                                shape = RoundedCornerShape(12.dp),
                                color = DarkCard,
                                border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF1E2A42)),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(
                                    modifier = Modifier.padding(14.dp),
                                    verticalArrangement = Arrangement.spacedBy(10.dp)
                                ) {
                                    Text(strings.filtersTitle, fontSize = 13.sp, fontWeight = FontWeight.Bold, color = GoldYellow)

                                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                        Column(modifier = Modifier.weight(1f)) {
                                            Text(strings.broadAreaLabel, fontSize = 10.sp, color = TextMuted)
                                            val currentBroadSelected = when {
                                                selectedCnpqFilter.isBlank() || selectedCnpqFilter == "All" || selectedCnpqFilter == "Todas" -> strings.allLabel
                                                else -> {
                                                    val idx = broadAreasPT.indexOf(selectedCnpqFilter)
                                                    if (idx >= 0 && idx < strings.broadAreas.size) strings.broadAreas[idx] else selectedCnpqFilter
                                                }
                                            }
                                            FilterDropdown(
                                                selected = currentBroadSelected,
                                                options = strings.broadAreas,
                                                onSelect = { chosen ->
                                                    val idx = strings.broadAreas.indexOf(chosen)
                                                    val ptValue = if (idx >= 0 && idx < broadAreasPT.size) broadAreasPT[idx] else chosen
                                                    viewModel.onCnpqFilterChange(ptValue)
                                                }
                                            )
                                        }

                                        Column(modifier = Modifier.weight(1f)) {
                                            Text(strings.databaseLabel, fontSize = 10.sp, color = TextMuted)
                                            FilterDropdown(
                                                selected = selectedIndexerFilter.ifBlank { strings.allLabel },
                                                options = listOf(strings.allLabel, "Web of Science - SCIE", "Web of Science - SSCI", "Web of Science - AHCI", "Web of Science - ESCI", "Scopus", "SciELO", "Educ@"),
                                                onSelect = viewModel::onIndexerFilterChange
                                            )
                                        }
                                    }

                                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                        Column(modifier = Modifier.weight(1f)) {
                                            Text(strings.jcrQuartileLabel, fontSize = 10.sp, color = TextMuted)
                                            FilterDropdown(
                                                selected = selectedJcrFilter.ifBlank { strings.allLabel },
                                                options = listOf(strings.allLabel, "Q1", "Q2", "Q3", "Q4"),
                                                onSelect = viewModel::onJcrFilterChange
                                            )
                                        }

                                        Column(modifier = Modifier.weight(1f)) {
                                            Text(strings.sjrQuartileLabel, fontSize = 10.sp, color = TextMuted)
                                            FilterDropdown(
                                                selected = selectedSjrFilter.ifBlank { strings.allLabel },
                                                options = listOf(strings.allLabel, "Q1", "Q2", "Q3", "Q4"),
                                                onSelect = viewModel::onSjrFilterChange
                                            )
                                        }
                                    }

                                    Column(modifier = Modifier.fillMaxWidth()) {
                                        Text(strings.sortLabel, fontSize = 10.sp, color = TextMuted)
                                        FilterDropdown(
                                            selected = selectedSortOption.getLocalizedLabel(currentLanguage),
                                            options = JournalSortOption.values().map { it.getLocalizedLabel(currentLanguage) },
                                            onSelect = { selectedLabel ->
                                                val found = JournalSortOption.values().firstOrNull { it.getLocalizedLabel(currentLanguage) == selectedLabel }
                                                if (found != null) viewModel.onSortOptionChange(found)
                                            }
                                        )
                                    }
                                }
                            }
                        }

                        if (isLoadingDb) {
                            item {
                                Row(
                                    modifier = Modifier.fillMaxWidth().padding(vertical = 32.dp),
                                    horizontalArrangement = Arrangement.Center,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    CircularProgressIndicator(modifier = Modifier.size(24.dp), color = CoralRed, strokeWidth = 3.dp)
                                    Spacer(modifier = Modifier.width(12.dp))
                                    Text(strings.loadingLabel, fontSize = 13.sp, color = TextMuted)
                                }
                            }
                        } else if (journals.isEmpty()) {
                            item {
                                Box(modifier = Modifier.fillMaxWidth().padding(vertical = 32.dp), contentAlignment = Alignment.Center) {
                                    Text(strings.noResultsLabel, fontSize = 13.sp, color = TextMuted)
                                }
                            }
                        } else {
                            item {
                                Text("${strings.showingCountLabel} ${journals.size}", fontSize = 12.sp, color = TextMuted, modifier = Modifier.padding(vertical = 4.dp))
                            }

                            items(journals, key = { it.id }) { journal ->
                                JournalRowItem(journal, strings)
                            }
                        }
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        item {
                            Surface(
                                shape = RoundedCornerShape(12.dp),
                                color = DarkCard,
                                border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF1E2A42)),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(16.dp)) {
                                    Text(strings.aiTitle, fontSize = 15.sp, fontWeight = FontWeight.Bold, color = GoldYellow)
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(strings.aiDescription, fontSize = 12.sp, color = TextMuted)

                                    Spacer(modifier = Modifier.height(12.dp))

                                    OutlinedTextField(
                                        value = aiTitle,
                                        onValueChange = viewModel::onAiTitleChange,
                                        label = { Text(strings.manuscriptTitleLabel, color = TextMuted) },
                                        modifier = Modifier.fillMaxWidth(),
                                        colors = OutlinedTextFieldDefaults.colors(
                                            unfocusedContainerColor = DarkInputBg,
                                            focusedContainerColor = DarkInputBg,
                                            focusedTextColor = Color.White,
                                            unfocusedTextColor = Color.White
                                        ),
                                        shape = RoundedCornerShape(8.dp)
                                    )

                                    Spacer(modifier = Modifier.height(10.dp))

                                    OutlinedTextField(
                                        value = aiAbstract,
                                        onValueChange = viewModel::onAiAbstractChange,
                                        label = { Text(strings.abstractLabel, color = TextMuted) },
                                        modifier = Modifier.fillMaxWidth(),
                                        minLines = 4,
                                        maxLines = 6,
                                        colors = OutlinedTextFieldDefaults.colors(
                                            unfocusedContainerColor = DarkInputBg,
                                            focusedContainerColor = DarkInputBg,
                                            focusedTextColor = Color.White,
                                            unfocusedTextColor = Color.White
                                        ),
                                        shape = RoundedCornerShape(8.dp)
                                    )

                                    Spacer(modifier = Modifier.height(12.dp))

                                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                        Column(modifier = Modifier.weight(1f)) {
                                            Text(strings.databaseLabel, fontSize = 10.sp, color = TextMuted)
                                            FilterDropdown(
                                                selected = aiDatabaseFilter.ifBlank { strings.allLabel },
                                                options = listOf(strings.allLabel, "Web of Science - SCIE", "Web of Science - SSCI", "Web of Science - AHCI", "Web of Science - ESCI", "Scopus", "SciELO", "Educ@"),
                                                onSelect = viewModel::onAiDatabaseFilterChange
                                            )
                                        }

                                        Column(modifier = Modifier.weight(1f)) {
                                            Text(strings.sortLabel, fontSize = 10.sp, color = TextMuted)
                                            FilterDropdown(
                                                selected = aiSortOption.getLocalizedLabel(currentLanguage),
                                                options = AiSortOption.values().map { it.getLocalizedLabel(currentLanguage) },
                                                onSelect = { selectedLabel ->
                                                    val found = AiSortOption.values().firstOrNull { it.getLocalizedLabel(currentLanguage) == selectedLabel }
                                                    if (found != null) viewModel.onAiSortOptionChange(found)
                                                }
                                            )
                                        }
                                    }

                                    Spacer(modifier = Modifier.height(14.dp))

                                    Button(
                                        onClick = { viewModel.getRecommendations() },
                                        modifier = Modifier.fillMaxWidth().height(46.dp),
                                        enabled = !aiLoading,
                                        colors = ButtonDefaults.buttonColors(containerColor = CoralRed, contentColor = Color.White),
                                        shape = RoundedCornerShape(8.dp)
                                    ) {
                                        if (aiLoading) {
                                            CircularProgressIndicator(modifier = Modifier.size(20.dp), color = Color.White, strokeWidth = 2.dp)
                                            Spacer(modifier = Modifier.width(8.dp))
                                            Text(strings.analyzingBtn, fontWeight = FontWeight.Bold)
                                        } else {
                                            Icon(Icons.Default.AutoAwesome, contentDescription = null, modifier = Modifier.size(18.dp))
                                            Spacer(modifier = Modifier.width(8.dp))
                                            Text(strings.analyzeBtn, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                                        }
                                    }
                                }
                            }
                        }

                        if (aiResult.isNotEmpty()) {
                            item {
                                Surface(
                                    color = DarkInputBg,
                                    shape = RoundedCornerShape(10.dp),
                                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF1E2A42)),
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Column(modifier = Modifier.padding(14.dp)) {
                                        Text(strings.aiOpinionHeader, fontWeight = FontWeight.Bold, color = GoldYellow, fontSize = 13.sp)
                                        Spacer(modifier = Modifier.height(6.dp))
                                        Text(text = aiResult, color = Color.White, fontSize = 12.sp, lineHeight = 16.sp)
                                    }
                                }
                            }
                        }

                        if (aiRecommendedJournals.isNotEmpty()) {
                            item {
                                Text("${strings.aiRecommendedHeader} (${aiRecommendedJournals.size})", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = GoldYellow)
                            }

                            items(aiRecommendedJournals, key = { "rec_${it.id}" }) { journal ->
                                JournalRowItem(journal, strings)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun FilterDropdown(selected: String, options: List<String>, onSelect: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }

    Box {
        Surface(
            color = DarkInputBg,
            shape = RoundedCornerShape(6.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF1E2A42)),
            modifier = Modifier.fillMaxWidth().clickable { expanded = !expanded }
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 7.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(selected, fontSize = 11.sp, color = Color.White, maxLines = 1)
                Text("▼", fontSize = 9.sp, color = TextMuted)
            }
        }
        DropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
            modifier = Modifier.background(Color(0xFF0F172A))
        ) {
            options.forEach { option ->
                DropdownMenuItem(
                    text = { Text(option, fontSize = 11.sp, color = if (option == selected) CoralRed else Color.White) },
                    onClick = {
                        onSelect(option)
                        expanded = false
                    }
                )
            }
        }
    }
}

@Composable
fun JournalRowItem(journal: Journal, strings: AppStrings) {
    val context = LocalContext.current
    val rawUrl = journal.h5IndexUrl.trim()
    val targetUrl = if (rawUrl.startsWith("http", ignoreCase = true)) {
        rawUrl
    } else if (rawUrl.isNotEmpty()) {
        "https://$rawUrl"
    } else {
        "https://www.google.com/search?q=${Uri.encode(journal.title + " journal official website")}"
    }

    val scholarUrl = if (rawUrl.startsWith("http", ignoreCase = true)) {
        rawUrl
    } else {
        "https://scholar.google.com/citations?view_op=search_venues&hl=en&vq=${Uri.encode(journal.title)}"
    }

    Surface(
        shape = RoundedCornerShape(10.dp),
        color = Color(0xFF01031E),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF1E2A42)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Surface(
                shape = RoundedCornerShape(8.dp),
                color = Color(0xFF031226),
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable {
                        try {
                            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(targetUrl))
                            context.startActivity(intent)
                        } catch (e: Exception) {
                            e.printStackTrace()
                        }
                    }
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = journal.title,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = strings.visitJournalWebsite,
                            fontSize = 11.sp,
                            color = TextMuted,
                            fontWeight = FontWeight.Normal
                        )
                    }

                    Icon(
                        Icons.Default.OpenInNew,
                        contentDescription = "Link Oficial",
                        tint = Color.White,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = journal.subarea.ifBlank { journal.cnpqArea.ifBlank { "Multidisciplinar" } },
                fontSize = 11.sp,
                color = TextMuted
            )

            if (journal.indexers.isNotBlank()) {
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Indexadores: ${journal.indexers}",
                    fontSize = 10.sp,
                    color = Color(0xFF94A3B8)
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                val jcrText = journal.jcr.ifBlank { "N/A" }
                val jcrQText = if (journal.quartile.isNotBlank()) " (${journal.quartile})" else ""
                val sjrText = journal.sjr.ifBlank { "N/A" }
                val sjrQText = if (journal.sjrQuartile.isNotBlank()) " (${journal.sjrQuartile})" else ""
                val hIndexVal = journal.hIndex.ifBlank { "N/A" }

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = "JCR: $jcrText$jcrQText | SJR: $sjrText$sjrQText | H: $hIndexVal",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = GoldYellow
                    )
                }

                Spacer(modifier = Modifier.width(6.dp))

                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = Color(0xFF1E2A42),
                    border = androidx.compose.foundation.BorderStroke(1.dp, GoldYellow),
                    modifier = Modifier.clickable {
                        try {
                            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(scholarUrl))
                            context.startActivity(intent)
                        } catch (e: Exception) {
                            e.printStackTrace()
                        }
                    }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Default.Adjust,
                            contentDescription = "Target",
                            tint = GoldYellow,
                            modifier = Modifier.size(13.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = strings.accessH5Index,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = GoldYellow
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun SidebarContent(
    strings: AppStrings,
    onClose: () -> Unit,
    context: android.content.Context,
    onOpenSubscribeDialog: () -> Unit,
    visitCount: Long
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SidebarBgColor)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 14.dp),
            horizontalArrangement = Arrangement.End,
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onClose, modifier = Modifier.size(28.dp)) {
                Icon(Icons.Default.Close, contentDescription = "Close", tint = Color.White)
            }
        }

        HorizontalDivider(color = Color(0xFF1E2A42))

        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(scrollState)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // BOTÕES DE AÇÃO DESTACADOS: FALE CONOSCO, DOAÇÃO E INSCREVER-SE
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                // 1. Fale Conosco
                Surface(
                    color = CoralRed,
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable {
                            try {
                                val intent = Intent(Intent.ACTION_SENDTO).apply {
                                    data = Uri.parse("mailto:support@scipubs.com")
                                    putExtra(Intent.EXTRA_SUBJECT, "SciPubs Journal Finder Support")
                                }
                                context.startActivity(intent)
                            } catch (e: Exception) {
                                e.printStackTrace()
                            }
                            onClose()
                        }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            Icons.Default.Email,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = strings.contactUs,
                            color = Color.White,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                // 2. Doação -> Direciona para Buy Me A Coffee (https://buymeacoffee.com/scipubs)
                Surface(
                    color = EmeraldGreen,
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable {
                            try {
                                val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://buymeacoffee.com/scipubs"))
                                context.startActivity(intent)
                            } catch (e: Exception) {
                                e.printStackTrace()
                            }
                            onClose()
                        }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            Icons.Default.Favorite,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = strings.donation,
                            color = Color.White,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                // 3. Inscrever-se -> Abre Pop-up VIP
                Surface(
                    color = RoyalBlue,
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable {
                            onClose()
                            onOpenSubscribeDialog()
                        }
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            Icons.Default.CardMembership,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = strings.subscribe,
                            color = Color.White,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            SidebarSection(strings.secIndexers, listOf(
                "Web of Science" to "https://www.webofknowledge.com",
                "Scopus" to "https://www.scopus.com",
                "PubMed" to "https://pubmed.ncbi.nlm.nih.gov/",
                "SciELO" to "https://www.scielo.org/pt-br/",
                "Educ@" to "http://educa.fcc.org.br/",
                "JSTOR" to "https://www.jstor.org/",
                "Latindex" to "https://www.latindex.org/"
            ), context, onClose)

            SidebarSection(strings.secRepositories, listOf(
                "ERIC" to "https://eric.ed.gov/",
                "BASE" to "https://www.base-search.net/",
                "DOAJ" to "https://doaj.org/",
                "Catálogo de Teses CAPES" to "https://catalogodeteses.capes.gov.br/"
            ), context, onClose)

            SidebarSection(strings.secAi, listOf(
                "ScopusAI" to "https://www.scopus.com/pages/home#scopus-ai",
                "ResearchRabbit" to "https://www.researchrabbit.ai/",
                "Perplexity" to "https://www.perplexity.ai/",
                "ConnectedPapers" to "https://www.connectedpapers.com/",
                "Consensus" to "https://consensus.app/",
                "SciSpace" to "https://scispace.com/",
                "Elicit" to "https://elicit.com/"
            ), context, onClose)

            SidebarSection(strings.secGov, listOf(
                "CNPq" to "https://cnpq.br/",
                "CAPES" to "https://www.gov.br/capes/pt-br",
                "Currículo Lattes" to "https://lattes.cnpq.br/",
                "Portal Periódicos CAPES" to "https://www.periodicos.capes.gov.br/"
            ), context, onClose)

            SidebarSection(strings.secInst, listOf(
                "UFOP" to "https://www.ufop.br",
                "PPGE-UFOP" to "https://www.posedu.ufop.br",
                "Música-UFOP" to "https://www.musica.ufop.br",
                "👤 Site Pessoal Prof. João Quadros" to "https://professor.ufop.br/joaoquadros"
            ), context, onClose)

            HorizontalDivider(color = Color(0xFF1E2A42))

            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(strings.metadataTitle, fontSize = 10.sp, fontWeight = FontWeight.Bold, color = GoldYellow)
                Text(strings.systemStatus, fontSize = 10.sp, color = TextMuted)
                Text(strings.baseVersion, fontSize = 10.sp, color = TextMuted)
                Text(strings.cnpqStandard, fontSize = 10.sp, color = TextMuted)
                Spacer(modifier = Modifier.height(6.dp))
                // 🔒 SEÇÃO DE COPYRIGHT COM CLIQUE LONGO SECRETO PARA ADMINISTRADOR EXIBIR VISITAS ACUMULADAS
                Text(
                    text = strings.copyrightOwner,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                    modifier = Modifier.combinedClickable(
                        onClick = {},
                        onLongClick = {
                            Toast.makeText(
                                context,
                                "🔐 [ADMINISTRADOR]\nVisitas ao Portal: %,d acessos contínuos".format(visitCount),
                                Toast.LENGTH_LONG
                            ).show()
                        }
                    )
                )
                Text(strings.universityName, fontSize = 10.sp, color = TextMuted)
            }
        }
    }
}

@Composable
fun SidebarSection(
    title: String,
    items: List<Pair<String, String>>,
    context: android.content.Context,
    onClose: () -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(
            text = title,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            color = GoldYellow,
            letterSpacing = 1.sp
        )
        items.forEach { (label, url) ->
            var active by remember { mutableStateOf(false) }

            Surface(
                color = if (active) CoralRed else SidebarButtonColor,
                shape = RoundedCornerShape(8.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF1E2A42)),
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable {
                        active = true
                        try {
                            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                            context.startActivity(intent)
                        } catch (e: Exception) {
                            e.printStackTrace()
                        }
                        onClose()
                    }
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 9.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = label,
                        color = if (active) Color.White else LogoDarkBlue,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Normal
                    )
                    Icon(
                        Icons.Default.OpenInNew,
                        contentDescription = null,
                        tint = if (active) Color.White else LogoDarkBlue,
                        modifier = Modifier.size(14.dp)
                    )
                }
            }
        }
    }
}