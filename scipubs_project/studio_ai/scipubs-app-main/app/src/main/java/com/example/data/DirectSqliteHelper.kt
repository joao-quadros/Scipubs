package com.example.data

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import java.io.File
import java.io.FileOutputStream

object DirectSqliteHelper {
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