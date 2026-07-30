package com.example.data

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "journals")
data class Journal(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val title: String = "",
    val issn: String = "",
    @ColumnInfo(name = "cnpq_area") val cnpqArea: String = "",
    val subarea: String = "",
    val jcr: String = "",
    val quartile: String = "",
    val sjr: String = "",
    @ColumnInfo(name = "sjr_quartile") val sjrQuartile: String = "",
    @ColumnInfo(name = "h_index") val hIndex: String = "",
    @ColumnInfo(name = "h5_index_url") val h5IndexUrl: String = "",
    val indexers: String = ""
) {
    @Ignore var score: Double = 0.0
}

@Dao
interface JournalDao {
    @Query("SELECT * FROM journals ORDER BY title ASC")
    fun getAllJournals(): Flow<List<Journal>>

    @Query("SELECT COUNT(*) FROM journals")
    suspend fun getJournalCount(): Int

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(journals: List<Journal>)
}

@Database(entities = [Journal::class], version = 2, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun journalDao(): JournalDao
}

class JournalRepository(private val journalDao: JournalDao) {
    val allJournals: Flow<List<Journal>> = journalDao.getAllJournals()

    suspend fun getJournalCount(): Int {
        return journalDao.getJournalCount()
    }

    suspend fun insertInBatches(journals: List<Journal>) {
        journalDao.insertAll(journals)
    }
}